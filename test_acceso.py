import pytest

from acceso import (
  DENEGADO, MODO_DEMO, MODO_LOCAL, MODO_NUBE, PERMITIDO, SIN_SESION,
  correos_permitidos, diagnosticar_archivo_secretos, elegir_modo, evaluar_acceso, faltantes_config_nube,
)

YO = "yo@gmail.com"
SESION_OK = {"is_logged_in": True, "email": YO, "email_verified": True}


# ---------- elegir_modo ----------
@pytest.mark.parametrize("solo_demo, nube, excel, reales, esperado", [
  (True, True, True, True, MODO_DEMO),        # la demostracion siempre gana
  (False, True, False, False, MODO_NUBE),
  (False, True, True, False, MODO_NUBE),      # la nube gana sobre el Excel local
  (False, False, True, False, MODO_LOCAL),
  (False, False, False, True, MODO_LOCAL),    # sin Excel pero con permiso explicito
  (False, False, False, False, MODO_DEMO),    # seguro por defecto
])
def test_elegir_modo(solo_demo, nube, excel, reales, esperado):
  assert elegir_modo(solo_demo, nube, excel, reales) == esperado


# ---------- evaluar_acceso ----------
def test_sin_sesion_no_entra():
  assert evaluar_acceso(None, [YO]) == SIN_SESION
  assert evaluar_acceso({}, [YO]) == SIN_SESION
  assert evaluar_acceso({"is_logged_in": False, "email": YO}, [YO]) == SIN_SESION


def test_entra_quien_esta_en_la_lista_sin_importar_mayusculas_ni_espacios():
  usuario = {**SESION_OK, "email": "  YO@Gmail.COM "}

  assert evaluar_acceso(usuario, [YO]) == PERMITIDO


def test_un_correo_ajeno_es_denegado():
  usuario = {**SESION_OK, "email": "otra.persona@gmail.com"}

  assert evaluar_acceso(usuario, [YO]) == DENEGADO


def test_la_lista_vacia_no_deja_entrar_a_nadie():
  assert evaluar_acceso(SESION_OK, []) == DENEGADO
  assert evaluar_acceso(SESION_OK, None) == DENEGADO
  assert evaluar_acceso(SESION_OK, "") == DENEGADO
  assert evaluar_acceso(SESION_OK, [" ", ""]) == DENEGADO


def test_correo_sin_verificar_o_sin_dato_es_denegado():
  assert evaluar_acceso({**SESION_OK, "email_verified": False}, [YO]) == DENEGADO
  assert evaluar_acceso({"is_logged_in": True, "email": YO}, [YO]) == DENEGADO     # falta el dato: falla cerrada
  assert evaluar_acceso({**SESION_OK, "email": ""}, [YO]) == DENEGADO
  assert evaluar_acceso({**SESION_OK, "email": None}, [YO]) == DENEGADO


def test_un_correo_parecido_no_cuenta():
  assert evaluar_acceso({**SESION_OK, "email": "yo@gmail.com.evil.com"}, [YO]) == DENEGADO
  assert evaluar_acceso({**SESION_OK, "email": "xyo@gmail.com"}, [YO]) == DENEGADO


def test_correos_permitidos_acepta_lista_o_texto_con_comas():
  assert correos_permitidos("A@x.com, b@x.com ,,") == {"a@x.com", "b@x.com"}
  assert correos_permitidos(["A@x.com", " b@x.com "]) == {"a@x.com", "b@x.com"}
  assert correos_permitidos(None) == set()


# ---------- diagnosticar_archivo_secretos ----------
def test_un_archivo_de_secretos_con_bom_se_detecta_y_se_explica(tmp_path):
  archivo = tmp_path / "secrets.toml"
  archivo.write_bytes(b"\xef\xbb\xbf" + 'WISHLIST_MODO = "nube"\n'.encode("utf-8"))

  mensaje = diagnosticar_archivo_secretos(archivo)

  assert mensaje and "BOM" in mensaje


def test_un_archivo_de_secretos_correcto_o_inexistente_no_da_aviso(tmp_path):
  correcto = tmp_path / "secrets.toml"
  correcto.write_text('WISHLIST_MODO = "nube"\ncorreos_permitidos = ["a@b.com"]\n', encoding="utf-8")

  assert diagnosticar_archivo_secretos(correcto) is None
  assert diagnosticar_archivo_secretos(tmp_path / "no_existe.toml") is None


def test_un_error_de_formato_se_avisa_sin_mostrar_el_contenido(tmp_path):
  roto = tmp_path / "secrets.toml"
  roto.write_text('clave_privada = "SECRETO-123\n[[[roto', encoding="utf-8")

  mensaje = diagnosticar_archivo_secretos(roto)

  assert mensaje and "error de formato" in mensaje and "SECRETO-123" not in mensaje


# ---------- faltantes_config_nube ----------
def _config_completa():
  return {
    "auth": {"client_id": "i", "client_secret": "s", "cookie_secret": "c",
             "redirect_uri": "https://x/oauth2callback", "server_metadata_url": "https://m"},
    "gcp_service_account": {"client_email": "cuenta@proyecto.iam.gserviceaccount.com", "private_key": "k"},
    "gsheets": {"spreadsheet_id": "abc"},
    "correos_permitidos": [YO],
  }


def test_config_completa_no_tiene_faltantes():
  assert faltantes_config_nube(_config_completa()) == []


def test_config_vacia_lista_todo_lo_que_falta_sin_mostrar_valores():
  faltan = faltantes_config_nube({})

  assert "[auth] client_secret" in faltan
  assert "[gcp_service_account] private_key" in faltan
  assert "[gsheets] spreadsheet_id" in faltan
  assert "correos_permitidos" in faltan
  assert len(faltan) == 5 + 2 + 1 + 1


def test_config_con_una_sola_pieza_faltante():
  config = _config_completa()
  config["auth"]["cookie_secret"] = ""

  assert faltantes_config_nube(config) == ["[auth] cookie_secret"]
