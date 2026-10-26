"""Una sola pagina: sin contrasena se ve la demostracion; con la contrasena, tus datos reales en solo lectura.

Se simula con AppTest (sin internet).
"""
import hashlib

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from ayudas import copiar_app, excel_de_la_copia
from logica import vitrina
from logica.datos_excel import COLUMNAS_PERFIL, guardar_excel, normalizar_wishlist
from logica.vitrina import codificar_excel, generar_clave_hash

CLAVE = "clave-de-prueba-123"
ARTICULO_REAL = "ARTICULO-DE-LA-VITRINA"
ARTICULO_DEMO = "Guitarra nueva"          # viene de datos_demo.py


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
  copiar_app(tmp_path)
  monkeypatch.setattr(vitrina, "PAUSA_TRAS_FALLO", 0)      # las pruebas no necesitan esperar
  vitrina.LIMITADOR.reiniciar()
  yield tmp_path
  vitrina.LIMITADOR.reiniciar()


def _abrir(carpeta, secretos):
  at = AppTest.from_file(str(carpeta / "python" / "interfaz" / "WishList.py"), default_timeout=60)
  for clave, valor in secretos.items():
    at.secrets[clave] = valor
  return at.run()


def _campo_clave(at):
  return [t for t in at.text_input if t.label == "Contraseña"]


def _intentar(at, clave):
  _campo_clave(at)[0].set_value(clave)
  [b for b in at.button if b.label == "Entrar"][0].click()
  return at.run()


def _texto_visible(at):
  return " ".join(str(df.value.to_dict()) for df in at.dataframe) + " ".join(m.value for m in at.metric)


def _huella(ruta):
  return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _es_la_demostracion(at):
  return ARTICULO_DEMO in _texto_visible(at) and ARTICULO_REAL not in _texto_visible(at)


# ---------- sin contrasena: la demostracion ----------
def test_sin_contrasena_se_abre_la_demostracion_y_ningun_dato_real(entorno, secretos):
  at = _abrir(entorno, secretos)

  assert not at.exception
  assert _es_la_demostracion(at)
  assert any("Demostración" in i.value for i in at.info)
  assert "$750" in [m.value for m in at.metric]                 # 50% del ingreso inventado (1500)
  assert "$95" not in [m.value for m in at.metric]              # nada del perfil real
  assert len(_campo_clave(at)) == 1                             # y hay donde escribir la contrasena


def test_una_contrasena_incorrecta_no_deja_pasar_y_sigue_la_demostracion(entorno, secretos):
  at = _intentar(_abrir(entorno, secretos), "contrasena-equivocada")

  assert not at.exception
  assert any("incorrecta" in e.value for e in at.error)
  assert _es_la_demostracion(at)


def test_el_error_dice_cuantos_caracteres_llegaron_para_detectar_pegados_raros(entorno, secretos):
  intento = "esta-clave-esta-mal"                       # 19 caracteres

  at = _intentar(_abrir(entorno, secretos), intento)

  assert any("incorrecta" in e.value and "19 caracteres" in e.value for e in at.error)
  assert not any(intento in e.value for e in at.error)   # cuenta los caracteres, no repite la clave


def test_sin_contrasena_no_se_puede_guardar_nada(entorno, secretos):
  decoy = excel_de_la_copia(entorno)
  guardar_excel(
    {"WishList": normalizar_wishlist(pd.DataFrame({"Articulo": ["SOLO-LOCAL"], "Costo Estimado": [1.0]})),
     "Perfil": pd.DataFrame([[1.0, 1.0, 1.0, 1.0, 1.0]], columns=COLUMNAS_PERFIL)},
    decoy,
  )
  antes = _huella(decoy)
  at = _abrir(entorno, secretos)

  [t for t in at.text_input if t.label == "Articulo"][0].set_value("Articulo nuevo")
  at.number_input[0].set_value(10.0)
  [b for b in at.button if b.label == "Guardar"][0].click().run()

  assert any("no se guarda nada" in w.value for w in at.warning)
  assert _huella(decoy) == antes
  assert "SOLO-LOCAL" not in _texto_visible(at)


# ---------- con contrasena: tus datos reales ----------
def test_la_contrasena_correcta_muestra_los_datos_en_solo_lectura(entorno, secretos):
  at = _intentar(_abrir(entorno, secretos), CLAVE)

  assert not at.exception
  assert ARTICULO_REAL in _texto_visible(at) and ARTICULO_DEMO not in _texto_visible(at)
  etiquetas = [t.label for t in at.tabs]
  assert etiquetas[:4] == ["Artículos", "Perfil financiero", "Análisis", "Dashboard"]   # sin "Editar lista"
  assert "Editar lista" not in etiquetas
  assert not [b for b in at.button if "Guardar" in b.label]          # ni formularios ni botones para guardar
  assert not _campo_clave(at)                                        # ya no pide la contrasena
  assert len(at.text_input) == 2                                     # solo los buscadores, ningun campo para escribir datos
  assert not at.get("download_button")                               # tampoco se puede bajar el Excel
  assert any("solo lectura" in i.value for i in at.sidebar.info)
  assert not any("Demostración" in i.value for i in at.info)


def test_el_dashboard_con_la_clave_muestra_los_numeros_reales_y_sin_ella_los_de_ejemplo(entorno, secretos):
  bloqueada = _abrir(entorno, secretos)
  abierta = _intentar(_abrir(entorno, secretos), CLAVE)

  tarjetas = {m.label: m.value for m in abierta.metric}
  assert {m.label: m.value for m in bloqueada.metric}["Total Pendiente"] == "$3,847"      # demostracion
  assert tarjetas["Total Pendiente"] == "$70"                                              # 50 + 20 de los datos reales
  assert tarjetas["% de un Mes de Ingreso"] == "37%"                                       # 70 / 190


def test_con_la_clave_se_ve_todo_incluido_el_perfil_porque_asi_se_eligio(entorno, secretos):
  at = _intentar(_abrir(entorno, secretos), CLAVE)

  etiquetas = [m.label for m in at.metric]
  assert "Necesidades (50%)" in etiquetas and "Ahorro (20%)" in etiquetas
  assert "$95" in [m.value for m in at.metric]                       # 50% de un ingreso de 190


def test_salir_vuelve_a_la_demostracion_y_a_pedir_la_contrasena(entorno, secretos):
  at = _intentar(_abrir(entorno, secretos), CLAVE)
  assert ARTICULO_REAL in _texto_visible(at)

  [b for b in at.sidebar.button if b.label == "Salir"][0].click()
  at.run()

  assert _es_la_demostracion(at)
  assert len(_campo_clave(at)) == 1


def test_la_vitrina_ignora_un_excel_local_que_este_al_lado(entorno, secretos):
  guardar_excel(
    {"WishList": normalizar_wishlist(pd.DataFrame({"Articulo": ["SOLO-LOCAL"], "Costo Estimado": [1.0]})),
     "Perfil": pd.DataFrame([[1.0, 1.0, 1.0, 1.0, 1.0]], columns=COLUMNAS_PERFIL)},
    excel_de_la_copia(entorno),
  )

  bloqueada = _abrir(entorno, secretos)
  abierta = _intentar(_abrir(entorno, secretos), CLAVE)

  assert "SOLO-LOCAL" not in _texto_visible(bloqueada) and _es_la_demostracion(bloqueada)
  assert "SOLO-LOCAL" not in _texto_visible(abierta) and ARTICULO_REAL in _texto_visible(abierta)


# ---------- intentos limitados ----------
def test_con_demasiados_fallos_se_bloquea_aunque_despues_se_ponga_la_clave_correcta(entorno, secretos):
  at = _abrir(entorno, secretos)
  for _ in range(vitrina.LIMITADOR.max_fallos):
    at = _intentar(at, "mala-clave-numero-x")

  at = _intentar(at, CLAVE)

  assert any("Demasiados intentos" in e.value for e in at.error)
  assert _es_la_demostracion(at)


def test_el_bloqueo_vale_para_todas_las_sesiones(entorno, secretos):
  at1 = _abrir(entorno, secretos)
  for _ in range(vitrina.LIMITADOR.max_fallos):
    at1 = _intentar(at1, "mala-clave-numero-x")

  at2 = _intentar(_abrir(entorno, secretos), CLAVE)       # otra sesion distinta, clave correcta

  assert any("Demasiados intentos" in e.value for e in at2.error)
  assert _es_la_demostracion(at2)


# ---------- configuracion rota: nunca datos reales, siempre demostracion ----------
def test_configuracion_incompleta_cae_en_la_demostracion_y_avisa_sin_pedir_clave(entorno, secretos):
  incompletos = {k: v for k, v in secretos.items() if k != "VITRINA_HASH"}

  at = _abrir(entorno, incompletos)

  assert not at.exception
  assert any("VITRINA_HASH" in w.value for w in at.warning)
  assert not _campo_clave(at)
  assert _es_la_demostracion(at)


def test_datos_corruptos_dan_un_error_claro_y_se_queda_en_la_demostracion(entorno, secretos):
  rotos = {**secretos, "VITRINA_EXCEL_B64": "esto-no-es-base64!!"}

  at = _intentar(_abrir(entorno, rotos), CLAVE)

  assert not at.exception
  assert any("No pude leer los datos" in e.value for e in at.error)
  assert _es_la_demostracion(at)


def test_el_texto_que_genera_preparar_vitrina_funciona_en_la_app_de_punta_a_punta(entorno):
  """Lo que el usuario pega en Streamlit (generado por texto_secretos) tiene que abrir la vitrina."""
  import tomllib
  from logica.vitrina import texto_secretos

  secretos_generados = tomllib.loads(texto_secretos(_excel_de_la_vitrina(entorno), CLAVE))

  incorrecta = _intentar(_abrir(entorno, secretos_generados), "otra-clave-larga-99")
  correcta = _intentar(_abrir(entorno, secretos_generados), CLAVE)

  assert _es_la_demostracion(incorrecta)
  assert ARTICULO_REAL in _texto_visible(correcta)
