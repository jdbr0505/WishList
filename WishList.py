"""Puente para Streamlit Cloud: la app publicada arranca este archivo, y el codigo real vive en python/interfaz/.

Se deja en la raiz para no tener que recrear la app publicada. En tu computadora usa directamente:
  streamlit run python/interfaz/WishList.py
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "python" / "interfaz" / "WishList.py"), run_name="__main__")
