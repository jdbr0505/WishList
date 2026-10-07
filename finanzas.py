"""Logica financiera de la WishList: regla 50/30/20, prioridad y semaforo de compra.

Son funciones puras: reciben datos (DataFrame, Perfil) y devuelven numeros o tablas nuevas.
No usan Streamlit ni leen archivos, asi que se prueban con pytest (ver test_finanzas.py).
Las reglas y los pesos estan documentados en la seccion "Reglas de decision" del ROADMAP.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
import pandas as pd

from datos_excel import COLUMNAS_PERFIL

# Regla 50/30/20 sobre el ingreso neto mensual
PORC_NECESIDADES = 0.50
PORC_DESEOS = 0.30
PORC_AHORRO = 0.20

MESES_FONDO_POR_DEFECTO = 3  # se usa si el perfil no define meses de fondo objetivo
MESES_MAXIMO_ESPERA = 6      # mas de esto = "No conviene"

# Pesos del puntaje de prioridad (suman 1). Se pueden ajustar a gusto.
PESO_URGENCIA = 0.45
PESO_VALOR = 0.30
PESO_NECESIDAD = 0.25


@dataclass(frozen=True)
class Perfil:
  """Datos financieros del mes. frozen=True: no se puede modificar despues de crearlo."""
  ingreso: float = 0.0
  gastos_fijos: float = 0.0
  deseos_gastados: float = 0.0
  ahorro_actual: float = 0.0
  meses_fondo_objetivo: float = 0.0

  @property
  def completo(self) -> bool:
    return self.ingreso > 0


class Decision(NamedTuple):
  semaforo: str
  motivo: str


def _numero(valor) -> float:
  convertido = pd.to_numeric(valor, errors="coerce")
  return 0.0 if pd.isna(convertido) else float(convertido)


def perfil_desde_hoja(hoja: pd.DataFrame) -> Perfil:
  """Convierte la primera fila de la hoja Perfil en un Perfil (vacio si no hay filas)."""
  if hoja.empty:
    return Perfil()
  fila = hoja.iloc[0]
  ingreso, fijos, deseos, ahorro, meses = (_numero(fila[c]) for c in COLUMNAS_PERFIL)
  return Perfil(ingreso, fijos, deseos, ahorro, meses)


def presupuesto_503020(ingreso: float) -> dict[str, float]:
  return {
    "Necesidades": ingreso * PORC_NECESIDADES,
    "Deseos": ingreso * PORC_DESEOS,
    "Ahorro": ingreso * PORC_AHORRO,
  }


def deseos_disponibles(perfil: Perfil) -> float:
  """Lo que queda del 30% de deseos este mes (nunca negativo)."""
  return max(perfil.ingreso * PORC_DESEOS - perfil.deseos_gastados, 0.0)


def margen_necesidades(perfil: Perfil) -> float:
  """Lo que queda del 50% de necesidades despues de los gastos fijos (nunca negativo)."""
  return max(perfil.ingreso * PORC_NECESIDADES - perfil.gastos_fijos, 0.0)


def meses_fondo_cubiertos(perfil: Perfil) -> float:
  """Cuantos meses de gastos fijos cubre el ahorro actual (NaN si no hay gastos fijos)."""
  if perfil.gastos_fijos <= 0:
    return math.nan
  return perfil.ahorro_actual / perfil.gastos_fijos


def fondo_completo(perfil: Perfil) -> bool:
  objetivo = perfil.meses_fondo_objetivo or MESES_FONDO_POR_DEFECTO
  cubiertos = meses_fondo_cubiertos(perfil)
  return not math.isnan(cubiertos) and cubiertos >= objetivo


def _es(serie: pd.Series, valor: str) -> pd.Series:
  """Mascara booleana 'serie == valor' donde los vacios cuentan como False."""
  return (serie == valor).fillna(False).astype(bool)


def puntaje_prioridad(wishlist: pd.DataFrame) -> pd.Series:
  """Puntaje 0-100: urgencia (45%), valor percibido (30%) y si es una necesidad (25%)."""
  urgencia = (wishlist["Urgencia"] - 1) / 4
  valor = (wishlist["Valor"] - 1) / 4
  necesidad = _es(wishlist["Tipo"], "Necesidad").astype(float)
  puntaje = 100 * (urgencia * PESO_URGENCIA + valor * PESO_VALOR + necesidad * PESO_NECESIDAD)
  return puntaje.round(1)


def porcentaje_del_ingreso(costos: pd.Series, ingreso: float) -> pd.Series:
  """Que parte de un mes de ingreso representa cada costo, en % (NaN si no hay ingreso)."""
  if ingreso <= 0:
    return pd.Series(np.nan, index=costos.index)
  return (costos / ingreso * 100).round(1)


def impacto_en_fondo(costos: pd.Series, ahorro_actual: float) -> pd.Series:
  """Que parte del ahorro actual consumiria cada costo, en % (NaN si no hay ahorro)."""
  if ahorro_actual <= 0:
    return pd.Series(np.nan, index=costos.index)
  return (costos / ahorro_actual * 100).round(1)


def compromiso_mensual(wishlist: pd.DataFrame) -> pd.Series:
  """Gasto que se repite cada mes: Mensual = costo, Anual = costo / 12, Unico = 0."""
  factor = wishlist["Frecuencia"].map({"Mensual": 1.0, "Anual": 1 / 12}).astype(float).fillna(0.0)
  return (wishlist["Costo Estimado"] * factor).round(2)


def _tiene_precio(wishlist: pd.DataFrame) -> pd.Series:
  costo = wishlist["Costo Estimado"]
  return costo.notna() & (costo > 0)


def fuera_de_alcance(costos: pd.Series, aporte: float) -> pd.Series:
  """True para los costos que, solos, tardarian mas de MESES_MAXIMO_ESPERA meses en pagarse."""
  if aporte <= 0:
    return pd.Series(True, index=costos.index)
  return np.ceil(costos / aporte) > MESES_MAXIMO_ESPERA


def meses_de_espera(wishlist: pd.DataFrame, puntaje: pd.Series, perfil: Perfil) -> pd.Series:
  """Meses hasta poder comprar cada articulo pendiente con precio (1 = este mes).

  Los articulos compiten por el mismo presupuesto: dentro de cada tipo se ordenan por
  puntaje y se acumula el costo. Deseos usan lo que queda del 30%; necesidades, el margen del 50%.
  Un articulo fuera de alcance (solo, tardaria mas de MESES_MAXIMO_ESPERA meses) no entra en la fila,
  para que un gasto enorme no bloquee a los pequenos que si se pueden comprar.
  """
  meses = pd.Series(np.nan, index=wishlist.index)
  pendientes = _es(wishlist["Estado"], "Pendiente") & _tiene_precio(wishlist)

  for tipo, aporte in (("Deseo", deseos_disponibles(perfil)), ("Necesidad", margen_necesidades(perfil))):
    grupo = wishlist[pendientes & _es(wishlist["Tipo"], tipo)]
    if aporte <= 0:
      meses.loc[grupo.index] = math.inf
      continue

    fuera = fuera_de_alcance(grupo["Costo Estimado"], aporte)
    meses.loc[fuera[fuera].index] = np.ceil(grupo.loc[fuera, "Costo Estimado"] / aporte)

    fila = grupo[~fuera]
    orden = puntaje.loc[fila.index].sort_values(ascending=False, kind="stable").index
    acumulado = fila.loc[orden, "Costo Estimado"].cumsum()
    meses.loc[orden] = np.ceil(acumulado / aporte)
  return meses


def fecha_estimada(meses: float, hoy: pd.Timestamp) -> pd.Timestamp:
  """Fecha aproximada de compra (NaT si no hay plazo finito). Mes 1 = hoy."""
  if not math.isfinite(meses):
    return pd.NaT
  return hoy + pd.DateOffset(months=int(meses) - 1)


def decidir(tipo, estado, costo, meses: float, perfil: Perfil, fondo_ok: bool) -> Decision:
  """Semaforo de compra de un articulo. Las reglas se evaluan en este orden."""
  tipo = None if pd.isna(tipo) else tipo
  estado = None if pd.isna(estado) else estado

  if estado == "Comprado":
    return Decision("Comprado", "Ya lo compraste.")
  if pd.isna(costo) or costo <= 0:
    return Decision("Por cotizar", "Falta el precio para evaluarlo.")
  if tipo not in ("Deseo", "Necesidad"):
    return Decision("Clasificar", "Define si es un deseo o una necesidad.")
  if not perfil.completo:
    return Decision("Falta perfil", "Completa tu perfil financiero (ingreso mensual).")
  if math.isinf(meses):
    return Decision("No conviene", "No tienes presupuesto mensual disponible para este tipo de gasto.")
  if tipo == "Deseo" and not fondo_ok:
    return Decision("Esperar", "Primero completa tu fondo de emergencia.")
  if meses <= 1:
    return Decision("Comprar ya", "Cabe en el presupuesto de este mes.")
  if meses <= MESES_MAXIMO_ESPERA:
    return Decision("Esperar", f"Alcanza en {int(meses)} meses con tu presupuesto.")
  return Decision("No conviene", f"Tardaria {int(meses)} meses (mas de {MESES_MAXIMO_ESPERA}).")


def analizar_wishlist(wishlist: pd.DataFrame, perfil: Perfil, hoy: pd.Timestamp | None = None) -> pd.DataFrame:
  """Devuelve una copia de la WishList con las columnas calculadas (no modifica la original)."""
  hoy = hoy if hoy is not None else pd.Timestamp.today().normalize()
  puntaje = puntaje_prioridad(wishlist)
  meses = meses_de_espera(wishlist, puntaje, perfil)
  fondo_ok = fondo_completo(perfil)

  decisiones = [
    decidir(tipo, estado, costo, mes, perfil, fondo_ok)
    for tipo, estado, costo, mes in zip(
      wishlist["Tipo"], wishlist["Estado"], wishlist["Costo Estimado"], meses
    )
  ]

  return wishlist.assign(**{
    "Puntaje": puntaje,
    "% del Ingreso": porcentaje_del_ingreso(wishlist["Costo Estimado"], perfil.ingreso),
    "Impacto en Fondo %": impacto_en_fondo(wishlist["Costo Estimado"], perfil.ahorro_actual),
    "Compromiso Mensual": compromiso_mensual(wishlist),
    "Meses de Espera": meses,
    "Fecha Estimada": [fecha_estimada(m, hoy) for m in meses],
    "Semaforo": [d.semaforo for d in decisiones],
    "Motivo": [d.motivo for d in decisiones],
  })
