import pandas as pd

from datos_demo import hojas_demo
from finanzas import Perfil, analizar_wishlist, perfil_desde_hoja
from graficos import COLORES_SEMAFORO, grafico_503020, grafico_plan_de_compras, grafico_ranking

HOY = pd.Timestamp("2026-10-01")


def _demo():
  hojas = hojas_demo()
  perfil = perfil_desde_hoja(hojas["Perfil"])
  return analizar_wishlist(hojas["WishList"], perfil, HOY), perfil


def test_hojas_demo_tiene_las_dos_hojas_y_un_perfil_completo():
  hojas = hojas_demo()

  assert set(hojas) == {"WishList", "Perfil"}
  assert perfil_desde_hoja(hojas["Perfil"]).completo


def test_demo_cubre_todos_los_colores_principales_del_semaforo():
  analisis, _ = _demo()

  assert {"Comprar ya", "Esperar", "No conviene", "Por cotizar", "Comprado"} <= set(analisis["Semaforo"])


def test_grafico_503020_compara_meta_y_real():
  _, perfil = _demo()

  figura = grafico_503020(perfil)

  assert [t.name for t in figura.data] == ["Meta", "Real"]
  assert list(figura.data[0].y) == [50.0, 30.0, 20.0]
  # ingreso 1500: fijos 650 = 43.3%, deseos 120 = 8%, ahorro 730 = 48.7%
  assert [round(v, 1) for v in figura.data[1].y] == [43.3, 8.0, 48.7]


def test_grafico_ranking_excluye_comprados_y_usa_colores_del_semaforo():
  analisis, _ = _demo()

  figura = grafico_ranking(analisis)

  assert "Cuerda E de guitarra" not in list(figura.data[0].y)
  assert all(c in COLORES_SEMAFORO.values() for c in figura.data[0].marker.color)


def test_grafico_plan_de_compras_solo_pinta_compras_con_plazo():
  analisis, perfil = _demo()

  figura = grafico_plan_de_compras(analisis, perfil)

  puntos = {t.name: t for t in figura.data if t.mode == "markers"}
  articulos_pintados = set(puntos["Compras: deseos"].hovertext) | set(puntos["Compras: necesidades"].hovertext)
  assert "Reloj digital" not in articulos_pintados  # sin precio
  assert "Pedalera" in articulos_pintados


def test_graficos_aceptan_lista_vacia():
  vacio, _ = _demo()
  vacio = vacio.iloc[0:0]

  assert grafico_ranking(vacio) is not None
  assert grafico_plan_de_compras(vacio, Perfil(ingreso=1000)) is not None
