"""Ayudas compartidas por las pruebas que arrancan la app completa (AppTest) sobre una copia."""
import shutil
from pathlib import Path

CARPETA_PYTHON = Path(__file__).resolve().parents[1]
RAIZ_PROYECTO = CARPETA_PYTHON.parent


def copiar_app(destino: Path) -> Path:
  """Copia el codigo de la app a `destino/python` y devuelve la ruta de WishList.py.

  El Excel real de la copia viviria en `destino/excel/`, igual que en el proyecto. Asi las pruebas
  nunca tocan los archivos de verdad.
  """
  shutil.copytree(CARPETA_PYTHON, destino / "python", ignore=shutil.ignore_patterns("pruebas", "__pycache__"))
  return destino / "python" / "interfaz" / "WishList.py"


def excel_de_la_copia(destino: Path) -> Path:
  """Ruta donde la copia de la app espera su TablaWishList.xlsx (crea la carpeta `excel`)."""
  (destino / "excel").mkdir(exist_ok=True)
  return destino / "excel" / "TablaWishList.xlsx"
