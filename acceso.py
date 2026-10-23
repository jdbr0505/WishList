"""Reglas de acceso: que modo usa la app y quien puede entrar en la version privada.

Funciones puras (sin Streamlit): reciben datos simples y devuelven una decision, asi que se prueban con
pytest. Todas fallan "cerradas": si falta un dato o hay dudas, NO se da acceso.
"""
from __future__ import annotations

import tomllib
from collections.abc import Mapping
from pathlib import Path

MODO_DEMO = "demo"      # publica: datos inventados, no guarda nada
MODO_NUBE = "nube"      # privada: Google Sheets + login de Google
MODO_LOCAL = "local"    # tu computadora: Excel local

SIN_SESION = "sin_sesion"
DENEGADO = "denegado"
PERMITIDO = "ok"

# lo que tiene que existir en los secretos de Streamlit para que la version privada pueda arrancar
SECCION_AUTH = ("client_id", "client_secret", "cookie_secret", "redirect_uri", "server_metadata_url")
CAMPOS_CUENTA_SERVICIO = ("client_email", "private_key")


def elegir_modo(solo_demo: bool, modo_nube: bool, hay_excel_local: bool, datos_reales: bool) -> str:
  """Decide el modo. La demostracion gana siempre; sin Excel ni permiso explicito, es demostracion."""
  if solo_demo:
    return MODO_DEMO
  if modo_nube:
    return MODO_NUBE
  if hay_excel_local or datos_reales:
    return MODO_LOCAL
  return MODO_DEMO


def normalizar_correo(correo) -> str:
  return str(correo or "").strip().lower()


def correos_permitidos(valor) -> set[str]:
  """Acepta una lista de correos o un texto separado por comas. Devuelve un conjunto en minusculas."""
  if valor is None:
    return set()
  elementos = valor.split(",") if isinstance(valor, str) else list(valor)
  return {normalizar_correo(e) for e in elementos if normalizar_correo(e)}


def evaluar_acceso(usuario: Mapping | None, permitidos) -> str:
  """Devuelve SIN_SESION, DENEGADO o PERMITIDO.

  usuario: los datos del login (is_logged_in, email, email_verified). Solo entra quien inicio sesion,
  tiene el correo verificado y su correo esta en la lista. Una lista vacia no deja entrar a nadie.
  """
  if not usuario or not usuario.get("is_logged_in"):
    return SIN_SESION
  lista = correos_permitidos(permitidos)
  correo = normalizar_correo(usuario.get("email"))
  if not lista or not correo:
    return DENEGADO
  if usuario.get("email_verified") is not True:
    return DENEGADO
  return PERMITIDO if correo in lista else DENEGADO


def diagnosticar_archivo_secretos(ruta) -> str | None:
  """Si el archivo de secretos existe pero Streamlit no podria leerlo, devuelve la causa probable.

  Sin este aviso, un archivo ilegible se ignora en silencio y la app cae en modo demostracion sin
  explicar por que. No muestra nunca el contenido del archivo.
  """
  ruta = Path(ruta)
  if not ruta.exists():
    return None
  contenido = ruta.read_bytes()
  if contenido.startswith(b"\xef\xbb\xbf"):
    return ("El archivo de secretos tiene una marca BOM al inicio y Streamlit no puede leerlo. "
            "Guárdalo como «UTF-8» sin BOM (en VS Code: abajo a la derecha, «UTF-8»).")
  try:
    tomllib.loads(contenido.decode("utf-8"))
  except UnicodeDecodeError:
    return "El archivo de secretos no está guardado como UTF-8: guárdalo como UTF-8 sin BOM."
  except tomllib.TOMLDecodeError as error:
    return f"El archivo de secretos tiene un error de formato y se ignora: {error}"
  return None


def faltantes_config_nube(secretos: Mapping) -> list[str]:
  """Lista lo que falta configurar para la version privada (vacia si esta todo). Sin mostrar valores."""
  faltan = []

  auth = secretos.get("auth") or {}
  for campo in SECCION_AUTH:
    if not auth.get(campo):
      faltan.append(f"[auth] {campo}")

  cuenta = secretos.get("gcp_service_account") or {}
  for campo in CAMPOS_CUENTA_SERVICIO:
    if not cuenta.get(campo):
      faltan.append(f"[gcp_service_account] {campo}")

  if not (secretos.get("gsheets") or {}).get("spreadsheet_id"):
    faltan.append("[gsheets] spreadsheet_id")

  if not correos_permitidos(secretos.get("correos_permitidos")):
    faltan.append("correos_permitidos")
  return faltan
