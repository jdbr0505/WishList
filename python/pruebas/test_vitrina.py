"""Pruebas de la logica de la vitrina (sin Streamlit): contrasena, datos codificados y limite de intentos."""
import pandas as pd
import pytest

from logica.datos_excel import COLUMNAS_PERFIL, guardar_excel, normalizar_wishlist
from logica.vitrina import (
  LIMITADOR, LimitadorIntentos, codificar_excel, faltantes_config, generar_clave_hash,
  hojas_desde_b64, verificar_clave,
)

CLAVE = "una-clave-larga-123"


# ---------- contrasena ----------
def test_la_clave_correcta_se_acepta_y_las_demas_no():
  sal, huella = generar_clave_hash(CLAVE)

  assert verificar_clave(CLAVE, sal, huella) is True
  assert verificar_clave("otra-clave-larga-1", sal, huella) is False
  assert verificar_clave(CLAVE + " ", sal, huella) is False
  assert verificar_clave("", sal, huella) is False


def test_la_huella_no_contiene_la_contrasena_y_cambia_en_cada_generacion():
  sal1, huella1 = generar_clave_hash(CLAVE)
  sal2, huella2 = generar_clave_hash(CLAVE)

  assert CLAVE not in huella1 and CLAVE not in sal1
  assert (sal1, huella1) != (sal2, huella2)          # sal aleatoria: dos huellas distintas para la misma clave
  assert verificar_clave(CLAVE, sal2, huella2)


def test_una_clave_con_caracteres_invisibles_se_rechaza():
  # un Ctrl+V en una terminal de Windows puede colar un caracter de control sin que se vea
  with pytest.raises(ValueError, match="invisibles"):
    generar_clave_hash("una-clave\x16-larga-123")


def test_los_acentos_valen_igual_escritos_de_cualquier_forma():
  compuesta = "contraseña-fácil-123"                        # é como un solo caracter
  descompuesta = "contraseña-fácil-123"         # n + tilde y a + tilde por separado
  sal, huella = generar_clave_hash(compuesta)

  assert compuesta != descompuesta
  assert verificar_clave(descompuesta, sal, huella) is True


def test_una_clave_corta_se_rechaza():
  with pytest.raises(ValueError, match="al menos"):
    generar_clave_hash("corta")


@pytest.mark.parametrize("sal, huella", [("", ""), ("zz", "zz"), (None, None), ("abcd", ""), ("00" * 16, "")])
def test_si_faltan_o_estan_rotos_los_secretos_nadie_entra(sal, huella):
  assert verificar_clave(CLAVE, sal, huella) is False


# ---------- datos ----------
def _excel_de_prueba(tmp_path):
  lista = normalizar_wishlist(pd.DataFrame({"Articulo": ["Mouse", "Teclado"], "Costo Estimado": [20.0, None]}))
  perfil = pd.DataFrame([[190.0, 20.0, 15.0, 10.0, 3.0]], columns=COLUMNAS_PERFIL)
  ruta = tmp_path / "datos.xlsx"
  guardar_excel({"WishList": lista, "Perfil": perfil}, ruta)
  return ruta.read_bytes()


def test_el_excel_codificado_vuelve_igual_como_hojas_de_la_app(tmp_path):
  texto = codificar_excel(_excel_de_prueba(tmp_path))

  hojas = hojas_desde_b64(texto)

  assert hojas["WishList"]["Articulo"].tolist() == ["Mouse", "Teclado"]
  assert pd.isna(hojas["WishList"]["Costo Estimado"].iloc[1])
  assert hojas["Perfil"]["Ingreso Neto Mensual"].iloc[0] == 190.0


def test_un_texto_de_datos_roto_da_error_en_vez_de_datos_a_medias():
  with pytest.raises(Exception):
    hojas_desde_b64("esto no es base64 !!!")


def test_faltantes_lista_nombres_sin_valores():
  assert faltantes_config({}) == ["VITRINA_SAL", "VITRINA_HASH", "VITRINA_EXCEL_B64"]
  assert faltantes_config({"VITRINA_SAL": "a", "VITRINA_HASH": "b", "VITRINA_EXCEL_B64": " "}) == ["VITRINA_EXCEL_B64"]
  assert faltantes_config({"VITRINA_SAL": "a", "VITRINA_HASH": "b", "VITRINA_EXCEL_B64": "c"}) == []


# ---------- texto de secretos ----------
def test_texto_secretos_es_toml_valido_sin_la_contrasena_y_con_los_datos(tmp_path):
  import tomllib
  from logica.vitrina import texto_secretos

  texto = texto_secretos(_excel_de_prueba(tmp_path), CLAVE)
  secretos = tomllib.loads(texto)

  assert CLAVE not in texto
  assert secretos["WISHLIST_MODO"] == "vitrina"
  assert faltantes_config(secretos) == []
  assert verificar_clave(CLAVE, secretos["VITRINA_SAL"], secretos["VITRINA_HASH"])
  assert hojas_desde_b64(secretos["VITRINA_EXCEL_B64"])["WishList"]["Articulo"].tolist() == ["Mouse", "Teclado"]


def test_texto_secretos_rechaza_una_clave_corta(tmp_path):
  from logica.vitrina import texto_secretos

  with pytest.raises(ValueError):
    texto_secretos(_excel_de_prueba(tmp_path), "corta")


# ---------- limite de intentos ----------
def test_el_limitador_bloquea_tras_demasiados_fallos_y_se_libera_con_el_tiempo():
  limitador = LimitadorIntentos(max_fallos=3, ventana_segundos=60)
  for segundo in (0, 1, 2):
    assert limitador.bloqueado(segundo) is False
    limitador.registrar_fallo(segundo)

  assert limitador.bloqueado(3) is True
  assert limitador.bloqueado(59) is True        # los 3 fallos siguen dentro de la ventana de 60 s
  assert limitador.bloqueado(61) is False       # el primero (t=0) venció: quedan 2, menos que el maximo
  assert limitador.bloqueado(63) is False


def test_el_limitador_global_se_puede_reiniciar():
  LIMITADOR.reiniciar()
  for _ in range(LIMITADOR.max_fallos):
    LIMITADOR.registrar_fallo()
  assert LIMITADOR.bloqueado() is True

  LIMITADOR.reiniciar()

  assert LIMITADOR.bloqueado() is False
