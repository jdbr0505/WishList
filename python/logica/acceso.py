"""Que modo usa la app (demostracion o local) y una ayuda para detectar secretos ilegibles.

Funciones sin Streamlit: reciben datos simples y devuelven una decision, asi que se prueban con pytest.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

MODO_DEMO = "demo"          # publica: datos inventados, no guarda nada
MODO_LOCAL = "local"        # tu computadora: Excel local
MODO_VITRINA = "vitrina"    # tus datos reales de solo lectura, detras de una contrasena compartida


def elegir_modo(solo_demo: bool, vitrina: bool, hay_excel_local: bool, datos_reales: bool) -> str:
  """Decide el modo. La demostracion gana siempre; sin Excel ni permiso explicito, es demostracion."""
  if solo_demo:
    return MODO_DEMO
  if vitrina:
    return MODO_VITRINA
  if hay_excel_local or datos_reales:
    return MODO_LOCAL
  return MODO_DEMO


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
