import pandas as pd

from datos_demo import hojas_demo
from finanzas import Perfil, analizar_wishlist, perfil_desde_hoja
from graficos import (
  COLORES_SEMAFORO, grafico_503020, grafico_costo_por_decision, grafico_costo_por_mes, grafico_meses_por_articulo,
  grafico_pendiente_por_tipo, grafico_plan_de_compras, grafico_ranking,
)

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


def test_costo_por_decision_suma_el_costo_de_cada_semaforo_de_mayor_a_menor():
  analisis, _ = _demo()

  figura = grafico_costo_por_decision(analisis)

  # "Por cotizar" no tiene costos: no dibuja una barra vacia
  assert list(figura.data[0].y) == ["No conviene", "Esperar", "Comprar ya", "Comprado"]
  assert list(figura.data[0].x) == [3000, 507, 340, 23]
  assert figura.data[0].marker.color[0] == COLORES_SEMAFORO["No conviene"]


def test_pendiente_por_tipo_es_una_dona_con_el_total_pendiente_de_cada_tipo():
  analisis, _ = _demo()

  figura = grafico_pendiente_por_tipo(analisis)

  assert figura.data[0].type == "pie" and figura.data[0].hole > 0
  assert dict(zip(figura.data[0].labels, figura.data[0].values)) == {"Deseo": 3577, "Necesidad": 270}


def test_meses_por_articulo_solo_muestra_los_que_tienen_plazo_y_el_mas_cercano_arriba():
  analisis, _ = _demo()

  figura = grafico_meses_por_articulo(analisis)

  assert len(figura.data[0].y) == 10                        # sin precio y comprados no tienen plazo
  assert list(figura.data[0].x) == sorted(figura.data[0].x)
  assert figura.data[0].y[-1] == "Guitarra nueva"           # el de 10 meses queda al final
  assert figura.layout.yaxis.autorange == "reversed"


def test_costo_por_mes_agrupa_el_total_pendiente_por_mes_de_compra():
  analisis, _ = _demo()

  figura = grafico_costo_por_mes(analisis)

  assert [str(x) for x in figura.data[0].x] == ["1", "2", "3", "10"]
  assert list(figura.data[0].y) == [340, 327, 180, 3000]
  assert sum(figura.data[0].y) == 3847


def test_los_graficos_nuevos_aceptan_lista_vacia():
  vacio, _ = _demo()
  vacio = vacio.iloc[0:0]

  for crear in (grafico_costo_por_decision, grafico_pendiente_por_tipo, grafico_meses_por_articulo, grafico_costo_por_mes):
    assert crear(vacio) is not None


def test_graficos_aceptan_lista_vacia():
  vacio, _ = _demo()
  vacio = vacio.iloc[0:0]

  assert grafico_ranking(vacio) is not None
  assert grafico_plan_de_compras(vacio, Perfil(ingreso=1000)) is not None
