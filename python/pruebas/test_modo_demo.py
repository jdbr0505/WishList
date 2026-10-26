"""Pruebas de la demostracion publica (WISHLIST_SOLO_DEMO): nunca debe leer ni tocar el Excel real."""
import hashlib

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from ayudas import copiar_app, excel_de_la_copia

ARTICULO_SECRETO = "ARTICULO-REAL-PRIVADO"


def _huella(ruta):
  return hashlib.sha256(ruta.read_bytes()).hexdigest()


@pytest.fixture
def app_con_excel_real(tmp_path, monkeypatch):
  """Copia de la app con un Excel 'real' falso al lado, para comprobar que la demostracion no lo toca."""
  copiar_app(tmp_path)
  from logica.datos_excel import guardar_excel
  real = {
    "WishList": pd.DataFrame({"Articulo": [ARTICULO_SECRETO], "Tipo": ["Deseo"], "Costo Estimado": [999.0],
                              "Estado": ["Pendiente"], "Notas": [None], "Frecuencia": ["Único"], "Urgencia": [3],
                              "Valor": [3], "Fecha de alta": [pd.Timestamp("2026-01-01")]}),
    "Perfil": pd.DataFrame([[5000.0, 1000.0, 100.0, 9000.0, 3.0]], columns=[
      "Ingreso Neto Mensual", "Gastos fijos", "Deseos ya gastados", "Ahorro actual", "Meses de Fondo de emergencia objetivo"]),
  }
  guardar_excel(real, excel_de_la_copia(tmp_path))
  monkeypatch.setenv("WISHLIST_SOLO_DEMO", "1")
  return tmp_path


def _textos(at):
  partes = [str(df.value.to_dict()) for df in at.dataframe]
  partes += [m.value for m in at.metric]
  return " ".join(partes)


def test_la_demostracion_muestra_datos_inventados_y_no_el_excel_real(app_con_excel_real):
  at = AppTest.from_file(str(app_con_excel_real / "python" / "interfaz" / "WishList.py"), default_timeout=60).run()

  assert not at.exception
  assert ARTICULO_SECRETO not in _textos(at)
  assert "Mouse" in _textos(at)                       # dato del ejemplo
  assert len(at.sidebar.toggle) == 0                  # no hay interruptor para pedir los datos reales
  assert any("Demostración" in i.value for i in at.info)


def test_la_demostracion_no_guarda_nada_ni_modifica_el_excel_real(app_con_excel_real):
  real = app_con_excel_real / "excel" / "TablaWishList.xlsx"
  antes = _huella(real)
  at = AppTest.from_file(str(app_con_excel_real / "python" / "interfaz" / "WishList.py"), default_timeout=60).run()

  at.text_input[0].set_value("Articulo nuevo")
  at.number_input[0].set_value(10.0)
  at.button[0].click().run()

  assert any("no se guarda nada" in w.value for w in at.warning)
  assert not any("guardad" in s.value.lower() for s in at.success)   # nunca dice "guardado"
  assert _huella(real) == antes                        # el archivo real quedo intacto


def test_seguro_por_defecto_sin_excel_y_sin_variable_es_solo_demostracion(app_con_excel_real, monkeypatch):
  """Lo que pasa en una app publicada si se olvida el secreto: no hay Excel (esta en .gitignore)."""
  monkeypatch.delenv("WISHLIST_SOLO_DEMO")
  (app_con_excel_real / "excel" / "TablaWishList.xlsx").unlink()

  at = AppTest.from_file(str(app_con_excel_real / "python" / "interfaz" / "WishList.py"), default_timeout=60).run()
  at.text_input[0].set_value("Articulo nuevo")
  at.number_input[0].set_value(10.0)
  at.button[0].click().run()

  assert not at.exception
  assert len(at.sidebar.toggle) == 0                       # no hay interruptor
  assert any("Demostración" in i.value for i in at.info)
  assert not (app_con_excel_real / "excel" / "TablaWishList.xlsx").exists()   # no se creo ningun archivo


def test_con_datos_reales_activados_se_puede_empezar_sin_excel(app_con_excel_real, monkeypatch):
  monkeypatch.delenv("WISHLIST_SOLO_DEMO")
  monkeypatch.setenv("WISHLIST_DATOS_REALES", "1")
  (app_con_excel_real / "excel" / "TablaWishList.xlsx").unlink()

  at = AppTest.from_file(str(app_con_excel_real / "python" / "interfaz" / "WishList.py"), default_timeout=60).run()
  at.text_input[0].set_value("Mi primer articulo")
  at.number_input[0].set_value(25.0)
  at.button[0].click().run()

  assert not at.exception
  assert len(at.sidebar.toggle) == 1
  assert (app_con_excel_real / "excel" / "TablaWishList.xlsx").exists()        # modo normal: crea el archivo


def test_sin_la_variable_la_app_funciona_normal_con_el_excel(app_con_excel_real, monkeypatch):
  monkeypatch.delenv("WISHLIST_SOLO_DEMO")

  at = AppTest.from_file(str(app_con_excel_real / "python" / "interfaz" / "WishList.py"), default_timeout=60).run()

  assert not at.exception
  assert len(at.sidebar.toggle) == 1                   # el interruptor de ejemplo existe
  assert ARTICULO_SECRETO in _textos(at)               # en modo normal lee el Excel
