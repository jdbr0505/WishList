import math

import pandas as pd
import pytest

from datos_excel import COLUMNAS_PERFIL, normalizar_wishlist
from finanzas import (
  Perfil, analizar_wishlist, compromiso_mensual, decidir, deseos_disponibles,
  fecha_estimada, fondo_completo, margen_necesidades, perfil_desde_hoja,
  porcentaje_del_ingreso, presupuesto_503020, puntaje_prioridad,
)

HOY = pd.Timestamp("2026-10-01")

# ingreso 1000 -> deseos 300 (quedan 200), necesidades 500 (quedan 100 tras fijos 400)
# ahorro 1200 / fijos 400 = 3 meses de fondo, igual al objetivo
PERFIL = Perfil(ingreso=1000, gastos_fijos=400, deseos_gastados=100, ahorro_actual=1200, meses_fondo_objetivo=3)


def _lista(filas):
  """Arma una WishList normalizada a partir de tuplas (Articulo, Tipo, Costo, Estado, Urgencia, Valor)."""
  datos = pd.DataFrame(
    filas, columns=["Articulo", "Tipo", "Costo Estimado", "Estado", "Urgencia", "Valor"]
  )
  return normalizar_wishlist(datos)


def test_presupuesto_503020_reparte_el_ingreso():
  assert presupuesto_503020(1000) == {"Necesidades": 500, "Deseos": 300, "Ahorro": 200}


def test_deseos_disponibles_resta_lo_ya_gastado_y_no_baja_de_cero():
  assert deseos_disponibles(PERFIL) == 200
  assert deseos_disponibles(Perfil(ingreso=1000, deseos_gastados=999)) == 0


def test_margen_necesidades_resta_gastos_fijos():
  assert margen_necesidades(PERFIL) == 100


def test_fondo_completo_usa_el_objetivo_del_perfil():
  assert fondo_completo(PERFIL) is True
  assert fondo_completo(Perfil(ingreso=1000, gastos_fijos=400, ahorro_actual=800, meses_fondo_objetivo=3)) is False


def test_fondo_completo_sin_gastos_fijos_es_falso():
  assert fondo_completo(Perfil(ingreso=1000, ahorro_actual=5000)) is False


def test_puntaje_maximo_y_minimo():
  lista = _lista([("A", "Necesidad", 10, "Pendiente", 5, 5), ("B", "Deseo", 10, "Pendiente", 1, 1)])

  assert puntaje_prioridad(lista).tolist() == [100.0, 0.0]


def test_porcentaje_del_ingreso_y_sin_ingreso():
  costos = pd.Series([100.0, None])

  assert porcentaje_del_ingreso(costos, 1000).iloc[0] == 10.0
  assert porcentaje_del_ingreso(costos, 0).isna().all()


def test_compromiso_mensual_por_frecuencia():
  lista = _lista([("A", "Deseo", 12, "Pendiente", 3, 3)])
  lista = pd.concat([lista] * 3, ignore_index=True)
  lista["Frecuencia"] = ["Único", "Mensual", "Anual"]

  assert compromiso_mensual(lista).tolist() == [0.0, 12.0, 1.0]


def test_fecha_estimada_mes_uno_es_hoy_y_sin_plazo_es_nat():
  assert fecha_estimada(1, HOY) == HOY
  assert fecha_estimada(3, HOY) == pd.Timestamp("2026-12-01")
  assert pd.isna(fecha_estimada(math.inf, HOY))
  assert pd.isna(fecha_estimada(math.nan, HOY))


def test_los_deseos_compiten_por_el_mismo_presupuesto_segun_prioridad():
  lista = _lista([
    ("Menos importante", "Deseo", 300, "Pendiente", 3, 3),
    ("Mas importante", "Deseo", 150, "Pendiente", 5, 5),
  ])

  resultado = analizar_wishlist(lista, PERFIL, HOY).set_index("Articulo")

  # presupuesto de deseos 200: 150 -> mes 1; 150+300=450 -> mes 3
  assert resultado.loc["Mas importante", "Meses de Espera"] == 1
  assert resultado.loc["Mas importante", "Semaforo"] == "Comprar ya"
  assert resultado.loc["Menos importante", "Meses de Espera"] == 3
  assert resultado.loc["Menos importante", "Semaforo"] == "Esperar"
  assert resultado.loc["Menos importante", "Fecha Estimada"] == pd.Timestamp("2026-12-01")


def test_necesidad_usa_el_margen_de_necesidades():
  lista = _lista([("Mouse", "Necesidad", 250, "Pendiente", 4, 4)])

  resultado = analizar_wishlist(lista, PERFIL, HOY)

  assert resultado["Meses de Espera"].iloc[0] == 3  # ceil(250 / 100)


def test_deseo_con_fondo_incompleto_espera():
  perfil = Perfil(ingreso=1000, gastos_fijos=400, deseos_gastados=0, ahorro_actual=100, meses_fondo_objetivo=3)
  lista = _lista([("Pedalera", "Deseo", 50, "Pendiente", 5, 5)])

  assert analizar_wishlist(lista, perfil, HOY)["Semaforo"].iloc[0] == "Esperar"


def test_necesidad_ignora_el_fondo_incompleto():
  perfil = Perfil(ingreso=1000, gastos_fijos=400, ahorro_actual=100, meses_fondo_objetivo=3)
  lista = _lista([("Medias", "Necesidad", 50, "Pendiente", 5, 5)])

  assert analizar_wishlist(lista, perfil, HOY)["Semaforo"].iloc[0] == "Comprar ya"


def test_mas_de_seis_meses_no_conviene():
  lista = _lista([("Guitarra", "Deseo", 2000, "Pendiente", 5, 5)])

  resultado = analizar_wishlist(lista, PERFIL, HOY)

  assert resultado["Meses de Espera"].iloc[0] == 10
  assert resultado["Semaforo"].iloc[0] == "No conviene"


def test_un_gasto_enorme_no_bloquea_a_los_pequenos():
  lista = _lista([
    ("Guitarra", "Deseo", 3000, "Pendiente", 5, 5),  # fuera de alcance: 15 meses solo
    ("Cuerdas", "Deseo", 150, "Pendiente", 3, 3),
  ])

  resultado = analizar_wishlist(lista, PERFIL, HOY).set_index("Articulo")

  assert resultado.loc["Guitarra", "Meses de Espera"] == 15
  assert resultado.loc["Guitarra", "Semaforo"] == "No conviene"
  assert resultado.loc["Cuerdas", "Meses de Espera"] == 1  # sin el fix serian 17
  assert resultado.loc["Cuerdas", "Semaforo"] == "Comprar ya"


def test_sin_presupuesto_mensual_no_conviene():
  perfil = Perfil(ingreso=1000, gastos_fijos=400, deseos_gastados=300, ahorro_actual=1200, meses_fondo_objetivo=3)
  lista = _lista([("Teclado", "Deseo", 100, "Pendiente", 5, 5)])

  resultado = analizar_wishlist(lista, perfil, HOY)

  assert resultado["Semaforo"].iloc[0] == "No conviene"
  assert pd.isna(resultado["Fecha Estimada"].iloc[0])


def test_costo_vacio_o_cero_es_por_cotizar():
  lista = _lista([("A", "Deseo", None, "Pendiente", 3, 3), ("B", "Deseo", 0, "Pendiente", 3, 3)])

  assert analizar_wishlist(lista, PERFIL, HOY)["Semaforo"].tolist() == ["Por cotizar", "Por cotizar"]


def test_comprado_y_sin_clasificar_y_sin_perfil():
  lista = _lista([
    ("Hecho", "Deseo", 50, "Comprado", 3, 3),
    ("Raro", None, 50, "Pendiente", 3, 3),
  ])

  assert analizar_wishlist(lista, PERFIL, HOY)["Semaforo"].tolist() == ["Comprado", "Clasificar"]
  sin_perfil = _lista([("X", "Deseo", 50, "Pendiente", 3, 3)])
  assert analizar_wishlist(sin_perfil, Perfil(), HOY)["Semaforo"].iloc[0] == "Falta perfil"


def test_analizar_no_modifica_la_wishlist_original():
  lista = _lista([("A", "Deseo", 50, "Pendiente", 3, 3)])
  columnas = list(lista.columns)

  analizar_wishlist(lista, PERFIL, HOY)

  assert list(lista.columns) == columnas


def test_decidir_acepta_valores_vacios_sin_error():
  decision = decidir(pd.NA, pd.NA, pd.NA, math.nan, PERFIL, True)

  assert decision.semaforo == "Por cotizar"


def test_perfil_desde_hoja_lee_la_primera_fila_y_tolera_vacios():
  hoja = pd.DataFrame([[1000, None, 100, 500, 3]], columns=COLUMNAS_PERFIL)

  assert perfil_desde_hoja(hoja) == Perfil(1000, 0, 100, 500, 3)
  assert perfil_desde_hoja(pd.DataFrame(columns=COLUMNAS_PERFIL)) == Perfil()
