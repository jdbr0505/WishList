"""Crea powerbi/WishList_demo.xlsx con los datos de ejemplo (tres hojas: WishList, Perfil, Analisis).

Sirve para practicar Power BI y Excel sin tocar tu Excel real.
Uso (desde la carpeta del proyecto):  python python/herramientas/exportar_demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # para importar logica

from logica.datos_demo import hojas_demo
from logica.datos_excel import guardar_excel
from logica.finanzas import agregar_analisis

DESTINO = Path(__file__).resolve().parents[2] / "powerbi" / "WishList_demo.xlsx"


def main() -> None:
  DESTINO.parent.mkdir(exist_ok=True)
  guardar_excel(agregar_analisis(hojas_demo()), DESTINO)
  print(f"Creado: {DESTINO}")


if __name__ == "__main__":
  main()
