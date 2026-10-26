"""El script que prepara los secretos de la vitrina: escribe un archivo valido, sin BOM y sin la contrasena."""
import tomllib

import pandas as pd
import pytest

import preparar_vitrina
from datos_excel import COLUMNAS_PERFIL, guardar_excel, normalizar_wishlist
from vitrina import hojas_desde_b64, verificar_clave

CLAVE = "una-clave-larga-123"


@pytest.fixture
def excel(tmp_path):
  lista = normalizar_wishlist(pd.DataFrame({"Articulo": ["Mouse", "Teclado"], "Costo Estimado": [20.0, 40.0]}))
  perfil = pd.DataFrame([[190.0, 20.0, 15.0, 10.0, 3.0]], columns=COLUMNAS_PERFIL)
  ruta = tmp_path / "TablaWishList.xlsx"
  guardar_excel({"WishList": lista, "Perfil": perfil}, ruta)
  return ruta


def test_crea_un_archivo_toml_valido_sin_bom_ni_contrasena(excel, tmp_path):
  salida = tmp_path / "vitrina_secretos.toml"

  resumen = preparar_vitrina.crear_archivo_secretos(excel, salida, CLAVE)

  crudo = salida.read_bytes()
  assert not crudo.startswith(b"\xef\xbb\xbf")                     # un BOM haria que Streamlit ignore los secretos
  assert CLAVE.encode() not in crudo
  secretos = tomllib.loads(crudo.decode("utf-8"))
  assert secretos["WISHLIST_MODO"] == "vitrina"
  assert verificar_clave(CLAVE, secretos["VITRINA_SAL"], secretos["VITRINA_HASH"])
  assert hojas_desde_b64(secretos["VITRINA_EXCEL_B64"])["WishList"]["Articulo"].tolist() == ["Mouse", "Teclado"]
  assert resumen["articulos"] == 2 and resumen["filas_perfil"] == 1


def test_no_modifica_el_excel_original(excel, tmp_path):
  antes = excel.read_bytes()

  preparar_vitrina.crear_archivo_secretos(excel, tmp_path / "salida.toml", CLAVE)

  assert excel.read_bytes() == antes


def test_con_clave_corta_no_crea_nada(excel, tmp_path):
  salida = tmp_path / "salida.toml"

  with pytest.raises(ValueError):
    preparar_vitrina.crear_archivo_secretos(excel, salida, "corta")

  assert not salida.exists()


def test_probar_clave_dice_si_coincide_con_el_archivo_generado(excel, tmp_path):
  salida = tmp_path / "salida.toml"
  preparar_vitrina.crear_archivo_secretos(excel, salida, CLAVE)

  assert preparar_vitrina.probar_clave(salida, CLAVE) is True
  assert preparar_vitrina.probar_clave(salida, "otra-clave-larga-99") is False
  assert preparar_vitrina.probar_clave(salida, CLAVE + "\x16") is False


def test_describir_clave_avisa_de_caracteres_invisibles_sin_mostrar_la_clave():
  limpia = preparar_vitrina.describir_clave(CLAVE)
  sucia = preparar_vitrina.describir_clave("abc\x16def-ghi-jkl")

  assert str(len(CLAVE)) in limpia and "invisible" not in limpia
  assert "invisible" in sucia
  assert CLAVE not in limpia and "abc" not in sucia


def test_con_la_opcion_visible_la_clave_se_pide_con_input(monkeypatch):
  respuestas = iter([CLAVE, CLAVE])
  monkeypatch.setattr("builtins.input", lambda _mensaje: next(respuestas))

  assert preparar_vitrina.pedir_clave(visible=True) == CLAVE


def test_una_clave_con_caracteres_invisibles_no_se_acepta_al_pedirla(monkeypatch):
  respuestas = iter(["una-clave\x16-larga-123"] * 2)
  monkeypatch.setattr(preparar_vitrina.getpass, "getpass", lambda _mensaje: next(respuestas))

  with pytest.raises(SystemExit):
    preparar_vitrina.pedir_clave()


def test_la_clave_se_pide_dos_veces_y_debe_coincidir(monkeypatch):
  respuestas = iter([CLAVE, CLAVE])
  monkeypatch.setattr(preparar_vitrina.getpass, "getpass", lambda _mensaje: next(respuestas))
  assert preparar_vitrina.pedir_clave() == CLAVE

  respuestas = iter([CLAVE, "otra-distinta-123"])
  with pytest.raises(SystemExit):
    preparar_vitrina.pedir_clave()


def test_main_sin_excel_avisa_y_no_crea_nada(tmp_path, monkeypatch):
  monkeypatch.setattr(preparar_vitrina, "EXCEL", tmp_path / "no_existe.xlsx")
  monkeypatch.setattr(preparar_vitrina, "SALIDA", tmp_path / "salida.toml")

  with pytest.raises(SystemExit):
    preparar_vitrina.main()

  assert not (tmp_path / "salida.toml").exists()
