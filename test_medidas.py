"""Las medidas del reporte de Power BI (powerbi/medidas.dax) calculadas en pandas: mismos numeros que en la guia."""
import math

import pandas as pd

from datos_demo import hojas_demo
from finanzas import analizar_wishlist, perfil_desde_hoja
from medidas import calcular_medidas

HOY = pd.Timestamp("2026-10-01")


def _demo():
  hojas = hojas_demo()
  perfil = perfil_desde_hoja(hojas["Perfil"])
  return analizar_wishlist(hojas["WishList"], perfil, HOY), perfil


def test_con_los_datos_de_ejemplo_dan_los_mismos_numeros_que_la_guia_de_power_bi():
  analisis, perfil = _demo()

  medidas = calcular_medidas(analisis, perfil.ingreso)

  # tabla "Resultado esperado (demo)" de powerbi/GUIA_POWER_BI.md
  assert medidas["Articulos Pendientes"] == 12
  assert medidas["Total Pendiente"] == 3847
  assert medidas["Por Cotizar"] == 2
  assert round(medidas["% de un Mes de Ingreso"] * 100) == 256
  assert (medidas["Comprar Ya"], medidas["Esperar"], medidas["No Conviene"]) == (3, 6, 1)
  assert medidas["Plazo Maximo (meses)"] == 10


def test_costo_total_incluye_los_comprados_y_total_pendiente_no():
  analisis, perfil = _demo()

  medidas = calcular_medidas(analisis, perfil.ingreso)

  assert medidas["Costo Total"] == 3847 + 8 + 15           # los dos comprados suman 23
  assert medidas["Total Pendiente"] == 3847


def test_los_filtros_cambian_las_medidas_como_un_segmentador_de_power_bi():
  analisis, perfil = _demo()

  solo_necesidades = analisis[analisis["Tipo"] == "Necesidad"]
  medidas = calcular_medidas(solo_necesidades, perfil.ingreso)

  assert medidas["Total Pendiente"] == 30 + 60 + 180        # Power bank no tiene precio
  assert medidas["Articulos Pendientes"] == 4
  assert medidas["Por Cotizar"] == 1
  assert round(medidas["% de un Mes de Ingreso"], 3) == 0.18


def test_sin_ingreso_el_porcentaje_queda_vacio_en_vez_de_fallar():
  analisis, _ = _demo()

  assert math.isnan(calcular_medidas(analisis, 0)["% de un Mes de Ingreso"])


def test_con_una_lista_vacia_todo_es_cero_y_el_plazo_queda_vacio():
  analisis, perfil = _demo()

  medidas = calcular_medidas(analisis.iloc[0:0], perfil.ingreso)

  assert medidas["Articulos Pendientes"] == 0 and medidas["Total Pendiente"] == 0 and medidas["Por Cotizar"] == 0
  assert math.isnan(medidas["Plazo Maximo (meses)"])
  assert medidas["% de un Mes de Ingreso"] == 0


def test_un_plazo_infinito_no_cuenta_como_plazo():
  analisis, perfil = _demo()
  analisis = analisis.assign(**{"Meses de Espera": analisis["Meses de Espera"].where(analisis["Articulo"] != "Guitarra nueva", float("inf"))})

  assert calcular_medidas(analisis, perfil.ingreso)["Plazo Maximo (meses)"] == 3
