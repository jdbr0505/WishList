"""Pruebas de la version privada (Google Sheets + login). No usan internet ni cuentas reales:
Google se simula con objetos falsos y el login se simula reemplazando st.user."""
import shutil
from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import almacenamiento
from almacenamiento import AlmacenGoogleSheets
from finanzas import agregar_analisis
from test_almacenamiento import HojaCalculoFalsa, _error_api, _hojas

RAIZ = Path(__file__).parent
ARCHIVOS_APP = [
  "WishList.py", "datos_excel.py", "finanzas.py", "graficos.py", "datos_demo.py", "almacenamiento.py", "acceso.py",
]
MI_CORREO = "yo@gmail.com"
USUARIO_AUTORIZADO = {"is_logged_in": True, "email": MI_CORREO, "email_verified": True}
USUARIO_AJENO = {"is_logged_in": True, "email": "intruso@gmail.com", "email_verified": True}

# valores obviamente falsos: nada real
SECRETOS_COMPLETOS = {
  "WISHLIST_MODO": "nube",
  "auth": {
    "client_id": "falso", "client_secret": "falso", "cookie_secret": "falso",
    "redirect_uri": "https://ejemplo.streamlit.app/oauth2callback",
    "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
  },
  "gcp_service_account": {"client_email": "cuenta@proyecto.iam.gserviceaccount.com", "private_key": "falsa"},
  "gsheets": {"spreadsheet_id": "hoja-falsa"},
  "correos_permitidos": [MI_CORREO],
}


@pytest.fixture
def entorno(tmp_path, monkeypatch):
  """Copia de la app + una hoja de Google falsa ya cargada con datos + un registro de si alguien la abrio."""
  for nombre in ARCHIVOS_APP:
    shutil.copy(RAIZ / nombre, tmp_path / nombre)

  hoja_calculo = HojaCalculoFalsa()
  AlmacenGoogleSheets(hoja_calculo).guardar(agregar_analisis(_hojas(articulos=3)))
  aperturas = []

  def abrir_falsa(cuenta, spreadsheet_id):
    aperturas.append(spreadsheet_id)
    return hoja_calculo

  monkeypatch.setattr(almacenamiento, "abrir_hoja_calculo", abrir_falsa)
  return type("Entorno", (), {"carpeta": tmp_path, "hoja": hoja_calculo, "aperturas": aperturas})


def _iniciar(entorno, monkeypatch, usuario=None, secretos=None):
  if usuario is not None:
    monkeypatch.setattr(st, "user", usuario, raising=False)
  at = AppTest.from_file(str(entorno.carpeta / "WishList.py"), default_timeout=60)
  for clave, valor in (SECRETOS_COMPLETOS if secretos is None else secretos).items():
    at.secrets[clave] = valor
  return at.run()


def _texto_visible(at):
  return " ".join(str(df.value.to_dict()) for df in at.dataframe)


def test_sin_sesion_pide_login_y_no_toca_google(entorno, monkeypatch):
  at = _iniciar(entorno, monkeypatch)

  assert not at.exception
  assert any("versión privada" in i.value for i in at.info)
  assert any(b.label == "Iniciar sesión con Google" for b in at.button)
  assert len(at.dataframe) == 0                       # ningun dato en pantalla
  assert entorno.aperturas == []                      # ni siquiera se abrio la hoja de Google


def test_una_cuenta_no_autorizada_no_ve_nada(entorno, monkeypatch):
  at = _iniciar(entorno, monkeypatch, usuario=USUARIO_AJENO)

  assert not at.exception
  assert any("no tiene acceso" in e.value for e in at.error)
  assert len(at.dataframe) == 0 and "Cosa 0" not in _texto_visible(at)
  assert entorno.aperturas == []


def test_un_correo_sin_verificar_no_entra_aunque_este_en_la_lista(entorno, monkeypatch):
  at = _iniciar(entorno, monkeypatch, usuario={**USUARIO_AUTORIZADO, "email_verified": False})

  assert any("no tiene acceso" in e.value for e in at.error)
  assert entorno.aperturas == []


def test_la_cuenta_autorizada_ve_sus_datos_de_google_sheets(entorno, monkeypatch):
  at = _iniciar(entorno, monkeypatch, usuario=USUARIO_AUTORIZADO)

  assert not at.exception
  assert entorno.aperturas == ["hoja-falsa"]
  assert "Cosa 0" in _texto_visible(at) and "Cosa 2" in _texto_visible(at)
  assert any(MI_CORREO in c.value for c in at.sidebar.caption)         # muestra con que cuenta entro
  assert [t.label for t in at.tabs][0] == "Artículos"


def test_guardar_un_articulo_lo_escribe_en_google_sheets_con_su_analisis(entorno, monkeypatch):
  at = _iniciar(entorno, monkeypatch, usuario=USUARIO_AUTORIZADO)

  at.text_input[0].set_value("Articulo desde el telefono")
  at.number_input[0].set_value(40.0)
  at.button[0].click().run()

  assert not at.exception and any("guardados" in s.value for s in at.success)
  guardados = AlmacenGoogleSheets(entorno.hoja).cargar()["WishList"]
  assert len(guardados) == 4 and "Articulo desde el telefono" in guardados["Articulo"].tolist()
  assert len(entorno.hoja.worksheet("Analisis").get_all_values()) == 5      # cabecera + 4 articulos


def test_configuracion_incompleta_se_detiene_sin_mostrar_datos(entorno, monkeypatch):
  at = _iniciar(entorno, monkeypatch, usuario=USUARIO_AUTORIZADO, secretos={"WISHLIST_MODO": "nube"})

  assert any("Falta" in e.value for e in at.error)
  assert len(at.dataframe) == 0
  assert entorno.aperturas == []


def test_sin_correos_permitidos_nadie_entra(entorno, monkeypatch):
  secretos = {**SECRETOS_COMPLETOS, "correos_permitidos": []}

  at = _iniciar(entorno, monkeypatch, usuario=USUARIO_AUTORIZADO, secretos=secretos)

  assert any("correos_permitidos" in e.value for e in at.error)
  assert len(at.dataframe) == 0 and entorno.aperturas == []


def test_si_google_falla_al_leer_se_muestra_el_error_y_nunca_una_lista_vacia(entorno, monkeypatch):
  entorno.hoja.worksheet = lambda nombre: (_ for _ in ()).throw(_error_api(403))

  at = _iniciar(entorno, monkeypatch, usuario=USUARIO_AUTORIZADO)

  assert any("compártela" in e.value for e in at.error)
  assert len(at.dataframe) == 0                       # no se muestra una lista vacia que luego se pueda guardar


def test_la_nube_ignora_un_excel_local_que_este_al_lado(entorno, monkeypatch):
  from datos_excel import guardar_excel
  guardar_excel({"WishList": _hojas(1)["WishList"].assign(Articulo="SOLO-LOCAL"), "Perfil": _hojas(1)["Perfil"]},
                entorno.carpeta / "TablaWishList.xlsx")

  at = _iniciar(entorno, monkeypatch, usuario=USUARIO_AUTORIZADO)

  assert "SOLO-LOCAL" not in _texto_visible(at) and "Cosa 0" in _texto_visible(at)


def test_sin_wishlist_modo_la_demostracion_no_usa_google(entorno, monkeypatch):
  secretos = {k: v for k, v in SECRETOS_COMPLETOS.items() if k != "WISHLIST_MODO"}

  at = _iniciar(entorno, monkeypatch, usuario=USUARIO_AUTORIZADO, secretos=secretos)

  assert any("Demostración" in i.value for i in at.info)
  assert entorno.aperturas == [] and "Cosa 0" not in _texto_visible(at)
