import pytest

from acceso import MODO_DEMO, MODO_LOCAL, MODO_VITRINA, diagnosticar_archivo_secretos, elegir_modo


@pytest.mark.parametrize("solo_demo, vitrina, excel, reales, esperado", [
  (True, True, True, True, MODO_DEMO),        # la demostracion siempre gana
  (False, True, False, False, MODO_VITRINA),
  (False, True, True, True, MODO_VITRINA),    # la vitrina gana sobre el Excel local
  (False, False, True, False, MODO_LOCAL),
  (False, False, False, True, MODO_LOCAL),    # sin Excel pero con permiso explicito
  (False, False, False, False, MODO_DEMO),    # seguro por defecto
])
def test_elegir_modo(solo_demo, vitrina, excel, reales, esperado):
  assert elegir_modo(solo_demo, vitrina, excel, reales) == esperado


def test_un_archivo_de_secretos_con_bom_se_detecta_y_se_explica(tmp_path):
  archivo = tmp_path / "secrets.toml"
  archivo.write_bytes(b"\xef\xbb\xbf" + 'WISHLIST_SOLO_DEMO = "1"\n'.encode("utf-8"))

  mensaje = diagnosticar_archivo_secretos(archivo)

  assert mensaje and "BOM" in mensaje


def test_un_archivo_de_secretos_correcto_o_inexistente_no_da_aviso(tmp_path):
  correcto = tmp_path / "secrets.toml"
  correcto.write_text('WISHLIST_SOLO_DEMO = "1"\n', encoding="utf-8")

  assert diagnosticar_archivo_secretos(correcto) is None
  assert diagnosticar_archivo_secretos(tmp_path / "no_existe.toml") is None


def test_un_error_de_formato_se_avisa_sin_mostrar_el_contenido(tmp_path):
  roto = tmp_path / "secrets.toml"
  roto.write_text('clave_privada = "SECRETO-123\n[[[roto', encoding="utf-8")

  mensaje = diagnosticar_archivo_secretos(roto)

  assert mensaje and "error de formato" in mensaje and "SECRETO-123" not in mensaje
