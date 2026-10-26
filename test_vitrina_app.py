"""La vitrina dentro de la app: solo lectura, protegida con contrasena. Se simula con AppTest (sin internet)."""
import shutil
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import vitrina
from datos_excel import COLUMNAS_PERFIL, guardar_excel, normalizar_wishlist
from vitrina import codificar_excel, generar_clave_hash

RAIZ = Path(__file__).parent
ARCHIVOS_APP = ["WishList.py", "datos_excel.py", "finanzas.py", "graficos.py", "datos_demo.py", "acceso.py", "vitrina.py"]
CLAVE = "clave-de-prueba-123"
ARTICULO_REAL = "ARTICULO-DE-LA-VITRINA"


def _excel_de_la_vitrina(carpeta):
  lista = normalizar_wishlist(pd.DataFrame({
    "Articulo": [ARTICULO_REAL, "Otro articulo"],
    "Tipo": ["Deseo", "Necesidad"],
    "Costo Estimado": [50.0, 20.0],
    "Estado": ["Pendiente", "Pendiente"],
  }))
  perfil = pd.DataFrame([[190.0, 20.0, 15.0, 10.0, 3.0]], columns=COLUMNAS_PERFIL)
  ruta = carpeta / "para_codificar.xlsx"
  guardar_excel({"WishList": lista, "Perfil": perfil}, ruta)
  return ruta.read_bytes()


@pytest.fixture
def secretos(tmp_path):
  sal, huella = generar_clave_hash(CLAVE)
  return {
    "WISHLIST_MODO": "vitrina",
    "VITRINA_SAL": sal,
    "VITRINA_HASH": huella,
    "VITRINA_EXCEL_B64": codificar_excel(_excel_de_la_vitrina(tmp_path)),
  }


@pytest.fixture(autouse=True)
def entorno(tmp_path, monkeypatch):
  for nombre in ARCHIVOS_APP:
    shutil.copy(RAIZ / nombre, tmp_path / nombre)
  monkeypatch.setattr(vitrina, "PAUSA_TRAS_FALLO", 0)      # las pruebas no necesitan esperar
  vitrina.LIMITADOR.reiniciar()
  yield tmp_path
  vitrina.LIMITADOR.reiniciar()


def _abrir(carpeta, secretos):
  at = AppTest.from_file(str(carpeta / "WishList.py"), default_timeout=60)
  for clave, valor in secretos.items():
    at.secrets[clave] = valor
  return at.run()


def _intentar(at, clave):
  at.text_input[0].set_value(clave)
  [b for b in at.button if b.label == "Entrar"][0].click()
  return at.run()


def _texto_visible(at):
  return " ".join(str(df.value.to_dict()) for df in at.dataframe) + " ".join(m.value for m in at.metric)


def test_sin_contrasena_no_se_ve_ningun_dato(entorno, secretos):
  at = _abrir(entorno, secretos)

  assert not at.exception
  assert any("solo lectura" in i.value for i in at.info)
  assert at.text_input[0].label == "Contraseña"
  assert len(at.dataframe) == 0 and len(at.metric) == 0 and ARTICULO_REAL not in _texto_visible(at)


def test_una_contrasena_incorrecta_no_deja_pasar(entorno, secretos):
  at = _intentar(_abrir(entorno, secretos), "contrasena-equivocada")

  assert any("incorrecta" in e.value for e in at.error)
  assert len(at.dataframe) == 0 and ARTICULO_REAL not in _texto_visible(at)


def test_la_contrasena_correcta_muestra_los_datos_en_solo_lectura(entorno, secretos):
  at = _intentar(_abrir(entorno, secretos), CLAVE)

  assert not at.exception
  assert ARTICULO_REAL in _texto_visible(at)
  assert [t.label for t in at.tabs] == ["Artículos", "Perfil financiero", "Análisis", "Dashboard"]   # sin "Editar lista"
  assert not [b for b in at.button if "Guardar" in b.label]          # ni formularios ni botones para guardar
  assert len(at.text_input) == 2                                     # solo los buscadores, ningun campo para escribir datos
  assert not at.get("download_button")                               # tampoco se puede bajar el Excel
  assert any("Vitrina de solo lectura" in i.value for i in at.sidebar.info)


def test_la_vitrina_muestra_todo_incluido_el_perfil_porque_asi_se_eligio(entorno, secretos):
  at = _intentar(_abrir(entorno, secretos), CLAVE)

  etiquetas = [m.label for m in at.metric]
  assert "Necesidades (50%)" in etiquetas and "Ahorro (20%)" in etiquetas
  assert "$95" in [m.value for m in at.metric]                       # 50% de un ingreso de 190


def test_con_demasiados_fallos_se_bloquea_aunque_despues_se_ponga_la_clave_correcta(entorno, secretos):
  at = _abrir(entorno, secretos)
  for _ in range(vitrina.LIMITADOR.max_fallos):
    at = _intentar(at, "mala-clave-numero-x")

  at = _intentar(at, CLAVE)

  assert any("Demasiados intentos" in e.value for e in at.error)
  assert len(at.dataframe) == 0


def test_el_bloqueo_vale_para_todas_las_sesiones(entorno, secretos):
  at1 = _abrir(entorno, secretos)
  for _ in range(vitrina.LIMITADOR.max_fallos):
    at1 = _intentar(at1, "mala-clave-numero-x")

  at2 = _intentar(_abrir(entorno, secretos), CLAVE)       # otra sesion distinta, clave correcta

  assert any("Demasiados intentos" in e.value for e in at2.error)


def test_configuracion_incompleta_se_detiene_sin_pedir_nada_ni_mostrar_datos(entorno, secretos):
  incompletos = {k: v for k, v in secretos.items() if k != "VITRINA_HASH"}

  at = _abrir(entorno, incompletos)

  assert any("VITRINA_HASH" in e.value for e in at.error)
  assert len(at.text_input) == 0 and len(at.dataframe) == 0


def test_la_vitrina_ignora_un_excel_local_que_este_al_lado(entorno, secretos):
  guardar_excel(
    {"WishList": normalizar_wishlist(pd.DataFrame({"Articulo": ["SOLO-LOCAL"], "Costo Estimado": [1.0]})),
     "Perfil": pd.DataFrame([[1.0, 1.0, 1.0, 1.0, 1.0]], columns=COLUMNAS_PERFIL)},
    entorno / "TablaWishList.xlsx",
  )

  at = _intentar(_abrir(entorno, secretos), CLAVE)

  assert "SOLO-LOCAL" not in _texto_visible(at) and ARTICULO_REAL in _texto_visible(at)


def test_salir_vuelve_a_pedir_la_contrasena(entorno, secretos):
  at = _intentar(_abrir(entorno, secretos), CLAVE)
  assert len(at.dataframe) > 0

  [b for b in at.sidebar.button if b.label == "Salir"][0].click()
  at.run()

  assert len(at.dataframe) == 0 and at.text_input[0].label == "Contraseña"


def test_el_texto_que_genera_preparar_vitrina_funciona_en_la_app_de_punta_a_punta(entorno):
  """Lo que el usuario pega en Streamlit (generado por texto_secretos) tiene que abrir la vitrina."""
  import tomllib
  from vitrina import texto_secretos

  secretos_generados = tomllib.loads(texto_secretos(_excel_de_la_vitrina(entorno), CLAVE))

  incorrecta = _intentar(_abrir(entorno, secretos_generados), "otra-clave-larga-99")
  correcta = _intentar(_abrir(entorno, secretos_generados), CLAVE)

  assert len(incorrecta.dataframe) == 0
  assert ARTICULO_REAL in _texto_visible(correcta)


def test_datos_corruptos_dan_un_error_claro_sin_mostrar_nada(entorno, secretos):
  rotos = {**secretos, "VITRINA_EXCEL_B64": "esto-no-es-base64!!"}

  at = _intentar(_abrir(entorno, rotos), CLAVE)

  assert any("No pude leer los datos" in e.value for e in at.error)
  assert len(at.dataframe) == 0
