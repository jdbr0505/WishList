"""Comprueba, SIN escribir nada, que la cuenta de servicio puede abrir tu hoja de Google.

Uso (desde la carpeta del proyecto):   python probar_conexion_sheets.py
Necesita .streamlit/secrets.toml con [gcp_service_account] y [gsheets] (guia: docs/NUBE_PRIVADA.md).
"""
import sys

from almacenamiento import ErrorAlmacen, abrir_hoja_calculo
from secretos_locales import datos_de_google, leer_secretos


def main():
  cuenta, hoja_id = datos_de_google(leer_secretos())
  print(f"Cuenta de servicio: {cuenta['client_email']}")
  try:
    hoja_calculo = abrir_hoja_calculo(cuenta, hoja_id)
    pestanas = [hoja.title for hoja in hoja_calculo.worksheets()]
  except ErrorAlmacen as error:
    sys.exit(f"NO FUNCIONA: {error}")
  print(f"OK: conectado a la hoja «{hoja_calculo.title}». Pestañas: {', '.join(pestanas) or '(ninguna)'}")
  print("No se escribió nada. Siguiente paso: python subir_excel_a_sheets.py (para copiar tus datos).")


if __name__ == "__main__":
  main()
