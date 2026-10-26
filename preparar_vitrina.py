"""Prepara los secretos de la vitrina: tu Excel codificado + la huella de una contraseña.

Uso (desde la carpeta del proyecto):
  python preparar_vitrina.py             crea vitrina_secretos.toml
  python preparar_vitrina.py --visible   igual, pero la contraseña se ve al escribirla (si la oculta da problemas)
  python preparar_vitrina.py --probar    comprueba que una contraseña coincide con vitrina_secretos.toml

- Solo LEE TablaWishList.xlsx; nunca lo modifica.
- Pide la contraseña (mínimo 12 caracteres) y la repite para confirmar.
- Crea vitrina_secretos.toml (ignorado por git) para pegarlo en Streamlit > Settings > Secrets.
  Ese archivo tiene tus datos reales: bórralo después de pegarlo.
Guía completa: docs/VITRINA.md
"""
import getpass
import sys
import tomllib
from pathlib import Path

from vitrina import (
  LONGITUD_MINIMA_CLAVE, faltantes_config, hojas_desde_b64, texto_secretos,
  tiene_caracteres_invisibles, verificar_clave,
)

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


def probar_clave(ruta_secretos: Path, clave: str) -> bool:
  """True si `clave` coincide con la huella guardada en el archivo de secretos."""
  secretos = tomllib.loads(Path(ruta_secretos).read_text(encoding="utf-8"))
  return verificar_clave(clave, secretos.get("VITRINA_SAL", ""), secretos.get("VITRINA_HASH", ""))


def describir_clave(clave: str) -> str:
  """Cuantos caracteres tiene la clave y si trae alguno invisible; nunca la muestra."""
  texto = f"{len(clave)} caracteres"
  if tiene_caracteres_invisibles(clave):
    texto += " y contiene caracteres invisibles"
  return texto


def pedir_clave(visible: bool = False) -> str:
  leer = input if visible else getpass.getpass
  clave = leer(f"Contraseña para los visitantes (mínimo {LONGITUD_MINIMA_CLAVE} caracteres): ")
  if tiene_caracteres_invisibles(clave):
    sys.exit("La contraseña tiene caracteres invisibles (a veces los mete un Ctrl+V en la terminal). "
             "Escríbela a mano, o prueba con --visible.")
  if len(clave) < LONGITUD_MINIMA_CLAVE:
    sys.exit(f"Demasiado corta: usa al menos {LONGITUD_MINIMA_CLAVE} caracteres (una frase larga sirve).")
  if leer("Repítela para confirmar: ") != clave:
    sys.exit("No coinciden: no se creó nada.")
  return clave


def comprobar() -> None:
  if not SALIDA.exists():
    sys.exit(f"No existe {SALIDA.name} (¿ya lo borraste?). Genera uno nuevo con: python preparar_vitrina.py")
  clave = getpass.getpass("Contraseña a comprobar: ")
  print(f"Escribiste {describir_clave(clave)}.")
  print("COINCIDE con el archivo." if probar_clave(SALIDA, clave) else "NO coincide con el archivo.")


def crear(visible: bool) -> None:
  if not EXCEL.exists():
    sys.exit(f"No encuentro {EXCEL.name} en esta carpeta.")
  clave = pedir_clave(visible)
  resumen = crear_archivo_secretos(EXCEL, SALIDA, clave)

  print(f"Listo: {resumen['articulos']} artículos y {resumen['filas_perfil']} fila(s) de perfil codificados ({resumen['kb']:.0f} KB).")
  print(f"Tu contraseña tiene {describir_clave(clave)}: si la app dice «recibí N caracteres» con otro N, algo se coló al escribirla.")
  if resumen["kb"] > TAMANO_AVISO_KB:
    print(f"AVISO: el texto pesa más de {TAMANO_AVISO_KB} KB; Streamlit podría rechazarlo.")
  print(f"Se creó {SALIDA.name}. Siguiente paso: ábrelo, copia TODO su contenido y pégalo en Streamlit,")
  print("Settings > Secrets de tu app (reemplaza lo que haya, incluido WISHLIST_SOLO_DEMO).")
  print("Después borra ese archivo (tiene tus datos reales).")
  print("La contraseña no se guardó en ningún lado: solo su huella. Guárdala tú en un lugar seguro.")


def main() -> None:
  argumentos = set(sys.argv[1:])
  if "--probar" in argumentos:
    comprobar()
  else:
    crear(visible="--visible" in argumentos)


if __name__ == "__main__":
  main()
