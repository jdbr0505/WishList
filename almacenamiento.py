"""Donde se guardan los datos: un Excel local o una hoja de Google Sheets.

Las dos clases tienen la misma interfaz (cargar y guardar), asi que la app no necesita saber cual usa.
Este modulo no depende de Streamlit: se prueba con pytest, y la parte de Google se prueba con
objetos falsos que imitan a gspread (sin conectarse a internet).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from datos_excel import (
  COLUMNAS_DINERO, cargar_datos, guardar_excel, preparar_hojas,
)

# columnas que son numeros: al leer de Google Sheets se convierten (en una hoja todo puede llegar como texto)
COLUMNAS_NUMERICAS = set(COLUMNAS_DINERO) | {"Urgencia", "Valor", "Meses de Fondo de emergencia objetivo"}
HOJAS_QUE_SE_LEEN = ("WishList", "Perfil")   # "Analisis" se recalcula en cada guardado, no se lee
FORMATO_DINERO_SHEETS = {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}


class ErrorAlmacen(Exception):
  """Un problema al leer o guardar los datos, con un mensaje pensado para mostrarselo al usuario."""


class AlmacenExcel:
  """Los datos viven en un archivo .xlsx de esta computadora."""

  def __init__(self, ruta):
    self.ruta = ruta

  def cargar(self):
    return cargar_datos(self.ruta)

  def guardar(self, hojas):
    try:
      guardar_excel(hojas, self.ruta)
    except PermissionError as error:
      raise ErrorAlmacen("El Excel está abierto o OneDrive lo bloquea. Ciérralo y vuelve a guardar.") from error


def _celda(valor):
  """Convierte un valor de pandas a algo que Google Sheets acepta (numero, texto o vacio)."""
  if valor is None or valor is pd.NaT:
    return ""
  if isinstance(valor, float) and np.isnan(valor):
    return ""
  try:
    if pd.isna(valor):
      return ""
  except (TypeError, ValueError):
    pass
  if isinstance(valor, pd.Timestamp):
    return valor.strftime("%Y-%m-%d")     # texto ISO: con RAW Sheets no lo convierte en fecha
  if isinstance(valor, (bool, np.bool_)):
    return bool(valor)
  if isinstance(valor, (int, np.integer)):
    return int(valor)
  if isinstance(valor, (float, np.floating)):
    return float(valor)
  return str(valor)


def a_valores(datos):
  """DataFrame -> lista de filas (la primera es la cabecera), lista para enviar a Google Sheets."""
  cabecera = [str(c) for c in datos.columns]
  filas = [[_celda(v) for v in fila] for fila in datos.itertuples(index=False, name=None)]
  return [cabecera] + filas


def a_dataframe(valores):
  """Lista de filas leida de Google Sheets -> DataFrame con vacios como NaN y numeros convertidos."""
  if not valores or not valores[0]:
    return pd.DataFrame()
  cabecera = [str(c).strip() for c in valores[0]]
  filas = [list(f) + [""] * (len(cabecera) - len(f)) for f in valores[1:]]
  datos = pd.DataFrame([f[: len(cabecera)] for f in filas], columns=cabecera)
  datos = datos.replace("", np.nan)
  for columna in datos.columns:
    if columna in COLUMNAS_NUMERICAS:
      datos[columna] = pd.to_numeric(datos[columna], errors="coerce")
  return datos


def _letra_de_columna(numero):
  """1 -> A, 2 -> B, 27 -> AA."""
  letras = ""
  while numero:
    numero, resto = divmod(numero - 1, 26)
    letras = chr(65 + resto) + letras
  return letras


class AlmacenGoogleSheets:
  """Los datos viven en una hoja de calculo de Google (accesible desde cualquier dispositivo)."""

  def __init__(self, hoja_calculo):
    # hoja_calculo: un objeto gspread.Spreadsheet (o uno falso con la misma interfaz, en las pruebas)
    self.hoja_calculo = hoja_calculo

  def cargar(self):
    leidas = {}
    for nombre in HOJAS_QUE_SE_LEEN:
      hoja = self._buscar_hoja(nombre)
      if hoja is None:
        continue
      valores = con_errores_claros(
        lambda h=hoja: h.get_all_values(value_render_option="UNFORMATTED_VALUE")
      )
      leidas[nombre] = a_dataframe(valores)
    return preparar_hojas(leidas)

  def guardar(self, hojas):
    for nombre, datos in hojas.items():
      valores = a_valores(datos)
      con_errores_claros(lambda n=nombre, v=valores, d=datos: self._escribir_hoja(n, v, d))

  # ---- internos ----
  def _buscar_hoja(self, nombre):
    """Devuelve la hoja, o None si NO existe. Cualquier otro error se propaga: nunca se confunde un
    fallo de conexion con 'hoja vacia' (si no, un guardado posterior podria borrar tus datos)."""
    import gspread
    try:
      return con_errores_claros(lambda: self.hoja_calculo.worksheet(nombre))
    except gspread.exceptions.WorksheetNotFound:
      return None

  def _escribir_hoja(self, nombre, valores, datos):
    hoja = self._buscar_hoja(nombre)
    filas, columnas = len(valores), len(valores[0])
    if hoja is None:
      hoja = self.hoja_calculo.add_worksheet(title=nombre, rows=max(filas, 2), cols=max(columnas, 1))
    if hoja.row_count < filas or hoja.col_count < columnas:      # hace falta mas espacio
      hoja.resize(rows=max(hoja.row_count, filas), cols=max(hoja.col_count, columnas))

    # primero se escriben los datos nuevos y despues se borra lo que sobra: si algo falla a mitad de
    # camino, los datos viejos siguen en la hoja en vez de quedar vacia
    hoja.update(valores, "A1")     # raw=True por defecto: se guardan tal cual, sin interpretarlos
    sobrantes = []
    if filas < hoja.row_count:
      sobrantes.append(f"A{filas + 1}:{_letra_de_columna(hoja.col_count)}{hoja.row_count}")
    if columnas < hoja.col_count:
      sobrantes.append(f"{_letra_de_columna(columnas + 1)}1:{_letra_de_columna(hoja.col_count)}{hoja.row_count}")
    if sobrantes:
      hoja.batch_clear(sobrantes)
    self._dar_formato_dolares(hoja, datos)

  def _dar_formato_dolares(self, hoja, datos):
    """Muestra en dolares las columnas de dinero. Si falla, los datos ya estan guardados: se ignora."""
    ultima_fila = max(hoja.row_count, 2)
    reglas = [
      {"range": f"{_letra_de_columna(i + 1)}2:{_letra_de_columna(i + 1)}{ultima_fila}", "format": FORMATO_DINERO_SHEETS}
      for i, columna in enumerate(datos.columns) if columna in COLUMNAS_DINERO
    ]
    if not reglas:
      return
    try:
      hoja.batch_format(reglas)
    except Exception:   # el formato es cosmetico; nunca debe impedir guardar
      pass


def con_errores_claros(accion):
  """Ejecuta una accion contra Google y traduce los errores tipicos a mensajes entendibles."""
  import gspread
  try:
    return accion()
  except gspread.exceptions.APIError as error:
    codigo = getattr(getattr(error, "response", None), "status_code", None)
    mensajes = {
      403: "Google no deja entrar a la hoja de cálculo: compártela como Editor con el correo de la cuenta de servicio.",
      404: "No encuentro la hoja de cálculo: revisa el spreadsheet_id en los secretos.",
      429: "Google limitó las solicitudes por un momento: espera un minuto y vuelve a intentar.",
    }
    raise ErrorAlmacen(mensajes.get(codigo, f"Google devolvió un error (código {codigo}).")) from error
  except gspread.exceptions.SpreadsheetNotFound as error:
    raise ErrorAlmacen("No encuentro la hoja de cálculo: revisa el spreadsheet_id y que esté compartida.") from error
  except (ConnectionError, TimeoutError, OSError) as error:
    raise ErrorAlmacen("No pude conectar con Google. Revisa la conexión y vuelve a intentar.") from error


def abrir_hoja_calculo(cuenta_servicio, spreadsheet_id):
  """Abre la hoja de calculo de Google con una cuenta de servicio (un dict con las credenciales).

  Solo hace falta el correo de la cuenta de servicio compartido como Editor en la hoja.
  """
  import gspread
  cliente = gspread.service_account_from_dict(dict(cuenta_servicio))
  return con_errores_claros(lambda: cliente.open_by_key(spreadsheet_id))
