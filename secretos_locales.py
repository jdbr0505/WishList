"""Lee los secretos de .streamlit/secrets.toml para las herramientas de linea de comandos (no para la app)."""
import sys
import tomllib
from pathlib import Path

RUTA_SECRETOS = Path(__file__).parent / ".streamlit" / "secrets.toml"


def leer_secretos():
  """Devuelve los secretos como diccionario, o termina el programa con un mensaje claro si no existen."""
  if not RUTA_SECRETOS.exists():
    sys.exit(
      f"No encuentro {RUTA_SECRETOS}.\n"
      "Copia .streamlit/secrets.toml.example como .streamlit/secrets.toml y completa tus valores "
      "(guia: docs/NUBE_PRIVADA.md)."
    )
  with RUTA_SECRETOS.open("rb") as archivo:
    return tomllib.load(archivo)


def datos_de_google(secretos):
  """Devuelve (cuenta_de_servicio, spreadsheet_id) o termina con un mensaje si falta algo (sin mostrar valores)."""
  cuenta = secretos.get("gcp_service_account") or {}
  hoja_id = (secretos.get("gsheets") or {}).get("spreadsheet_id")
  faltan = [c for c in ("client_email", "private_key") if not cuenta.get(c)]
  if faltan or not hoja_id:
    sys.exit("Faltan datos en secrets.toml: " + ", ".join([f"[gcp_service_account] {c}" for c in faltan]
                                                           + ([] if hoja_id else ["[gsheets] spreadsheet_id"])))
  return cuenta, hoja_id
