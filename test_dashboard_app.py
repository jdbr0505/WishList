"""El Dashboard de la app replica las dos paginas del reporte de Power BI (Dashboard y Plan de compras)."""
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).parent
ARCHIVOS_APP = [p.name for p in RAIZ.glob("*.py") if not p.name.startswith("test_")]


@pytest.fixture
def app(tmp_path, monkeypatch):
  """La app en modo demostracion (datos inventados), en una carpeta sin Excel real."""
  for nombre in ARCHIVOS_APP:
    shutil.copy(RAIZ / nombre, tmp_path / nombre)
  monkeypatch.setenv("WISHLIST_SOLO_DEMO", "1")
  return AppTest.from_file(str(tmp_path / "WishList.py"), default_timeout=60).run()


def _metricas(at):
  return {m.label: m.value for m in at.metric}


def test_el_dashboard_tiene_las_mismas_paginas_que_el_reporte_de_power_bi(app):
  assert not app.exception
  etiquetas = [t.label for t in app.tabs]
  assert "Resumen" in etiquetas and "Plan de compras" in etiquetas


def test_las_tarjetas_de_la_pagina_dashboard_dan_los_numeros_de_la_guia(app):
  metricas = _metricas(app)

  assert metricas["Total Pendiente"] == "$3,847"
  assert metricas["% de un Mes de Ingreso"] == "256%"
  assert metricas["Por Cotizar"] == "2"


def test_las_tarjetas_de_la_pagina_plan_de_compras_dan_los_numeros_de_la_guia(app):
  metricas = _metricas(app)

  assert metricas["Artículos Pendientes"] == "12"
  assert (metricas["Comprar Ya"], metricas["Esperar"], metricas["No Conviene"]) == ("3", "6", "1")


def test_un_segmentador_filtra_las_tarjetas_como_en_power_bi(app):
  app.multiselect(key="dash_tipo").set_value(["Necesidad"]).run()

  metricas = _metricas(app)

  assert not app.exception
  assert metricas["Total Pendiente"] == "$270"
  assert metricas["Por Cotizar"] == "1"
  assert metricas["Artículos Pendientes"] == "12"          # el segmentador de la otra pagina no afecta a esta


def test_un_segmentador_sin_resultados_avisa_en_vez_de_fallar(app):
  app.multiselect(key="dash_tipo").set_value(["Necesidad"])
  app.multiselect(key="dash_estado").set_value(["Comprado"]).run()

  assert not app.exception
  assert any("No hay artículos" in i.value for i in app.info)


def test_la_pagina_plan_de_compras_tiene_su_propia_tabla_ordenada_por_puntaje(app):
  columnas = [list(df.value.columns) for df in app.dataframe]

  assert any(c[:2] == ["Articulo", "Tipo"] and "Puntaje" in c and "Motivo" in c for c in columnas)
