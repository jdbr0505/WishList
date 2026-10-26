"""Prepara los secretos de la vitrina: tu Excel codificado + la huella de una contraseña.

Uso (desde la carpeta del proyecto):   python preparar_vitrina.py
- Solo LEE TablaWishList.xlsx; nunca lo modifica.
- Te pide la contraseña (no se ve al escribirla) y la repite para confirmar. Mínimo 12 caracteres.
- Crea vitrina_secretos.toml (ignorado por git) para pegarlo en Streamlit > Settings > Secrets.
  Ese archivo tiene tus datos reales: bórralo después de pegarlo.
Guía completa: docs/VITRINA.md
"""
import getpass
import sys
import tomllib
from pathlib import Path

from vitrina import LONGITUD_MINIMA_CLAVE, faltantes_config, hojas_desde_b64, texto_secretos, verificar_clave

CARPETA = Path(__file__).parent
EXCEL = CARPETA / "TablaWishList.xlsx"
SALIDA = CARPETA / "vitrina_secretos.toml"
TAMANO_AVISO_KB = 200


def crear_archivo_secretos(excel: Path, salida: Path, clave: str) -> dict:
  """Genera `salida` con los secretos y devuelve un resumen. Comprueba todo antes de escribir:
  el texto es TOML valido, completo, los datos se leen de vuelta y la clave verifica."""
  texto = texto_secretos(excel.read_bytes(), clave)

  secretos = tomllib.loads(texto)
  if faltantes_config(secretos):
    raise ValueError("Los secretos generados estan incompletos.")
  hojas = hojas_desde_b64(secretos["VITRINA_EXCEL_B64"])
  if not verificar_clave(clave, secretos["VITRINA_SAL"], secretos["VITRINA_HASH"]):
    raise ValueError("La contraseña no verifica contra su huella.")

  salida.write_text(texto, encoding="utf-8", newline="\n")      # UTF-8 sin BOM
  return {
    "articulos": len(hojas["WishList"]),
    "filas_perfil": len(hojas["Perfil"]),
    "kb": len(texto.encode("utf-8")) / 1024,
  }


def pedir_clave() -> str:
  clave = getpass.getpass(f"Contraseña para los visitantes (mínimo {LONGITUD_MINIMA_CLAVE} caracteres, no se ve): ")
  if len(clave) < LONGITUD_MINIMA_CLAVE:
    sys.exit(f"Demasiado corta: usa al menos {LONGITUD_MINIMA_CLAVE} caracteres (una frase larga sirve).")
  if getpass.getpass("Repítela para confirmar: ") != clave:
    sys.exit("No coinciden: no se creó nada.")
  return clave


def main() -> None:
  if not EXCEL.exists():
    sys.exit(f"No encuentro {EXCEL.name} en esta carpeta.")
  resumen = crear_archivo_secretos(EXCEL, SALIDA, pedir_clave())

  print(f"Listo: {resumen['articulos']} artículos y {resumen['filas_perfil']} fila(s) de perfil codificados ({resumen['kb']:.0f} KB).")
  if resumen["kb"] > TAMANO_AVISO_KB:
    print(f"AVISO: el texto pesa más de {TAMANO_AVISO_KB} KB; Streamlit podría rechazarlo.")
  print(f"Se creó {SALIDA.name}. Siguiente paso: ábrelo, copia TODO su contenido y pégalo en Streamlit,")
  print("Settings > Secrets de la app de la vitrina. Después borra ese archivo (tiene tus datos reales).")
  print("La contraseña no se guardó en ningún lado: solo su huella. Guárdala tú en un lugar seguro.")


if __name__ == "__main__":
  main()
