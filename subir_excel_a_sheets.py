"""Copia tus datos de TablaWishList.xlsx a la hoja de Google (una sola vez, para empezar la version privada).

Uso (desde la carpeta del proyecto):   python subir_excel_a_sheets.py
- Solo LEE tu Excel; nunca lo modifica.
- ESCRIBE en Google las pestañas WishList, Perfil y Analisis. Si ya tienen datos, te lo dice y pide confirmacion.
"""
import sys
from pathlib import Path

from almacenamiento import AlmacenExcel, AlmacenGoogleSheets, ErrorAlmacen, abrir_hoja_calculo
from finanzas import agregar_analisis
from secretos_locales import datos_de_google, leer_secretos

EXCEL = Path(__file__).parent / "TablaWishList.xlsx"


def main():
  if not EXCEL.exists():
    sys.exit(f"No encuentro {EXCEL.name} en esta carpeta.")
  cuenta, hoja_id = datos_de_google(leer_secretos())

  locales = AlmacenExcel(EXCEL).cargar()
  print(f"Tu Excel tiene {len(locales['WishList'])} artículos y {len(locales['Perfil'])} fila(s) de perfil.")

  try:
    almacen = AlmacenGoogleSheets(abrir_hoja_calculo(cuenta, hoja_id))
    en_google = almacen.cargar()
  except ErrorAlmacen as error:
    sys.exit(f"NO FUNCIONA: {error}")

  ya_hay = len(en_google["WishList"]) or len(en_google["Perfil"])
  if ya_hay:
    print(f"ATENCIÓN: la hoja de Google ya tiene {len(en_google['WishList'])} artículos y "
          f"{len(en_google['Perfil'])} fila(s) de perfil. Esto los REEMPLAZA.")
  respuesta = input("Escribe SI (en mayúsculas) para copiar tus datos a Google Sheets: ").strip()
  if respuesta != "SI":
    sys.exit("Cancelado: no se escribió nada.")

  try:
    almacen.guardar(agregar_analisis(locales))
  except ErrorAlmacen as error:
    sys.exit(f"NO SE PUDO GUARDAR: {error}")
  print("Listo: tus datos están en Google Sheets. Tu Excel no se modificó.")


if __name__ == "__main__":
  main()
