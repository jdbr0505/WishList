"""Los dos archivos puente de la raiz (Streamlit Cloud los necesita) tienen que seguir funcionando y al dia."""
import pytest
from streamlit.testing.v1 import AppTest

from ayudas import RAIZ_PROYECTO


def _requisitos(ruta):
  return [linea.strip() for linea in ruta.read_text(encoding="utf-8").splitlines() if linea.strip() and not linea.startswith("#")]


def test_el_requirements_de_la_raiz_es_copia_de_requisitos():
  assert _requisitos(RAIZ_PROYECTO / "requirements.txt") == _requisitos(RAIZ_PROYECTO / "requisitos" / "requirements.txt")


def test_el_puente_de_la_raiz_arranca_la_app_como_demostracion(monkeypatch):
  monkeypatch.setenv("WISHLIST_SOLO_DEMO", "1")      # nunca lee tu Excel real, aunque exista en excel/

  at = AppTest.from_file(str(RAIZ_PROYECTO / "WishList.py"), default_timeout=60).run()

  assert not at.exception
  assert any("Demostración" in i.value for i in at.info)
  assert "Total Pendiente" in [m.label for m in at.metric]
