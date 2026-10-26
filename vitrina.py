"""Vitrina de solo lectura protegida con una contrasena compartida.

La idea: mostrar tus datos reales en el navegador a quien le des la contrasena, sin guardar nada en git
ni en un servidor propio. Los datos viajan como un texto (el Excel codificado en base64) dentro de los
"secretos" de Streamlit, junto con una huella (hash) de la contrasena: la contrasena en si no se guarda.

Este modulo no depende de Streamlit: se prueba con pytest.
Limite honesto: una contrasena compartida no distingue personas. Quien la sepa ve todo.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import threading
import time
from io import BytesIO

import pandas as pd

from datos_excel import preparar_hojas

LONGITUD_MINIMA_CLAVE = 12
CAMPOS_SECRETOS = ("VITRINA_SAL", "VITRINA_HASH", "VITRINA_EXCEL_B64")
PAUSA_TRAS_FALLO = 1.0          # segundos de espera tras una clave incorrecta (frena los intentos)
_SCRYPT = {"n": 2 ** 14, "r": 8, "p": 1, "dklen": 32}


def _huella(clave: str, sal: bytes) -> bytes:
  return hashlib.scrypt(clave.encode("utf-8"), salt=sal, **_SCRYPT)


def generar_clave_hash(clave: str) -> tuple[str, str]:
  """Devuelve (sal, huella) en hexadecimal. Rechaza claves cortas: la contrasena compartida es lo unico que protege los datos."""
  if len(clave) < LONGITUD_MINIMA_CLAVE:
    raise ValueError(f"La contraseña debe tener al menos {LONGITUD_MINIMA_CLAVE} caracteres.")
  sal = secrets.token_bytes(16)
  return sal.hex(), _huella(clave, sal).hex()


def verificar_clave(clave: str, sal_hex: str, huella_hex: str) -> bool:
  """True solo si la clave coincide. Cualquier dato roto o ausente da False (falla cerrado)."""
  try:
    esperada = bytes.fromhex(str(huella_hex))
    calculada = _huella(str(clave), bytes.fromhex(str(sal_hex)))
  except (ValueError, TypeError):
    return False
  return bool(esperada) and hmac.compare_digest(calculada, esperada)


def codificar_excel(contenido: bytes) -> str:
  """Excel (bytes) -> texto base64 para guardarlo como secreto."""
  return base64.b64encode(contenido).decode("ascii")


def hojas_desde_b64(texto_b64: str) -> dict[str, pd.DataFrame]:
  """Texto base64 -> hojas listas para usar en la app (mismo formato que cargar_datos)."""
  contenido = base64.b64decode(str(texto_b64), validate=True)
  return preparar_hojas(pd.read_excel(BytesIO(contenido), sheet_name=None))


def texto_secretos(contenido_excel: bytes, clave: str) -> str:
  """El texto TOML que se pega en los secretos de Streamlit: modo, huella de la clave y el Excel codificado.

  La contrasena NO queda en el texto, solo su huella. Lanza ValueError si la clave es demasiado corta.
  """
  sal, huella = generar_clave_hash(clave)
  return (
    "# Secretos de la VITRINA. Contiene tus datos reales: pegalo en Streamlit y despues borra este archivo.\n"
    'WISHLIST_MODO = "vitrina"\n'
    f'VITRINA_SAL = "{sal}"\n'
    f'VITRINA_HASH = "{huella}"\n'
    f'VITRINA_EXCEL_B64 = "{codificar_excel(contenido_excel)}"\n'
  )


def faltantes_config(secretos) -> list[str]:
  """Nombres de los secretos que faltan (nunca sus valores)."""
  return [campo for campo in CAMPOS_SECRETOS if not str(secretos.get(campo, "")).strip()]


class LimitadorIntentos:
  """Bloquea los intentos de contrasena si hay demasiados fallos recientes, entre TODAS las sesiones.

  Con una contrasena compartida, un atacante puede abrir muchas sesiones: por eso el conteo es global.
  El costo: si alguien insiste, tambien se bloquea al visitante legitimo unos minutos (falla cerrado).
  """

  def __init__(self, max_fallos: int = 10, ventana_segundos: int = 600):
    self.max_fallos, self.ventana = max_fallos, ventana_segundos
    self._fallos: list[float] = []
    self._cerrojo = threading.Lock()

  def _recientes(self, ahora: float) -> list[float]:
    return [t for t in self._fallos if ahora - t < self.ventana]

  def bloqueado(self, ahora: float | None = None) -> bool:
    ahora = time.time() if ahora is None else ahora
    with self._cerrojo:
      return len(self._recientes(ahora)) >= self.max_fallos

  def registrar_fallo(self, ahora: float | None = None) -> None:
    ahora = time.time() if ahora is None else ahora
    with self._cerrojo:
      self._fallos = self._recientes(ahora) + [ahora]

  def reiniciar(self) -> None:
    with self._cerrojo:
      self._fallos = []


# un solo limitador por proceso: lo comparten todas las sesiones de la app
LIMITADOR = LimitadorIntentos()
