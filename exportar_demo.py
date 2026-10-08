"""Crea powerbi/WishList_demo.xlsx con los datos de ejemplo (tres hojas: WishList, Perfil, Analisis).

Sirve para practicar Power BI y Excel sin tocar tu Excel real.
Uso (desde la carpeta del proyecto):  python exportar_demo.py
"""
from pathlib import Path

from datos_demo import hojas_demo
from datos_excel import guardar_excel
from finanzas import agregar_analisis

DESTINO = Path(__file__).parent / "powerbi" / "WishList_demo.xlsx"


def main() -> None:
  DESTINO.parent.mkdir(exist_ok=True)
  guardar_excel(agregar_analisis(hojas_demo()), DESTINO)
  print(f"Creado: {DESTINO}")


if __name__ == "__main__":
  main()
