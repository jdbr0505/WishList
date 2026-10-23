"""Pruebas del almacenamiento. La parte de Google usa objetos falsos que imitan a gspread: no hay internet."""
import json
import re

import gspread
import numpy as np
import pandas as pd
import pytest

import almacenamiento
from almacenamiento import (
  AlmacenExcel, AlmacenGoogleSheets, ErrorAlmacen, a_dataframe, a_valores,
)
from datos_excel import COLUMNAS_PERFIL, COLUMNAS_WISHLIST, normalizar_wishlist
from finanzas import agregar_analisis


# ---------- imitaciones de gspread ----------
def _numero_de_columna(letras):
  numero = 0
  for letra in letras:
    numero = numero * 26 + (ord(letra) - 64)
  return numero


class HojaFalsa:
  def __init__(self, titulo, filas=1000, columnas=26):
    self.title, self.row_count, self.col_count = titulo, filas, columnas
    self.celdas = {}            # (fila, columna) -> valor, ambos desde 1
    self.reglas_de_formato = []

  def get_all_values(self, value_render_option=None):
    if not self.celdas:
      return []
    max_fila = max(f for f, _ in self.celdas)
    max_col = max(c for _, c in self.celdas)
    return [[self.celdas.get((f, c), "") for c in range(1, max_col + 1)] for f in range(1, max_fila + 1)]

  def resize(self, rows, cols):
    self.row_count, self.col_count = rows, cols

  def update(self, values, range_name=None, raw=True):
    assert range_name == "A1" and raw is True
    if len(values) > self.row_count or max(len(f) for f in values) > self.col_count:
      raise AssertionError("se escribio fuera de la cuadricula: faltó hacer resize")
    for i, fila in enumerate(values, start=1):
      for j, valor in enumerate(fila, start=1):
        self.celdas[(i, j)] = valor

  def batch_clear(self, rangos):
    for rango in rangos:
      m = re.fullmatch(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", rango)
      c1, f1, c2, f2 = _numero_de_columna(m.group(1)), int(m.group(2)), _numero_de_columna(m.group(3)), int(m.group(4))
      for clave in [k for k in self.celdas if f1 <= k[0] <= f2 and c1 <= k[1] <= c2]:
        del self.celdas[clave]

  def batch_format(self, reglas):
    self.reglas_de_formato.extend(reglas)


class HojaCalculoFalsa:
  def __init__(self):
    self.hojas = {}

  def worksheet(self, nombre):
    if nombre not in self.hojas:
      raise gspread.exceptions.WorksheetNotFound(nombre)
    return self.hojas[nombre]

  def add_worksheet(self, title, rows, cols):
    self.hojas[title] = HojaFalsa(title, rows, cols)
    return self.hojas[title]


def _error_api(codigo):
  class Respuesta:
    status_code = codigo
    text = "error"

    def json(self):
      return {"error": {"code": codigo, "message": "x", "status": "X"}}
  return gspread.exceptions.APIError(Respuesta())


def _hojas(articulos=3):
  lista = normalizar_wishlist(pd.DataFrame({
    "Articulo": [f"Cosa {i}" for i in range(articulos)],
    "Tipo": ["Deseo"] * articulos,
    "Costo Estimado": [10.5 * (i + 1) if i != 1 else None for i in range(articulos)],
    "Estado": ["Pendiente"] * articulos,
    "Fecha de alta": [pd.Timestamp("2026-10-08")] * articulos,
  }))
  perfil = pd.DataFrame([[190.0, 20.0, 15.0, 10.0, 3.0]], columns=COLUMNAS_PERFIL)
  return {"WishList": lista, "Perfil": perfil}


# ---------- conversion de datos ----------
def test_a_valores_produce_solo_tipos_que_google_acepta():
  datos = normalizar_wishlist(pd.DataFrame({"Articulo": ["A"], "Costo Estimado": [np.nan], "Fecha de alta": [pd.NaT]}))
  datos.loc[0, "Fecha de alta"] = pd.Timestamp("2026-10-08")

  valores = a_valores(datos)

  json.dumps(valores)                                   # si hay tipos numpy o NaN, esto falla
  fila = dict(zip(valores[0], valores[1]))
  assert fila["Fecha de alta"] == "2026-10-08"           # texto ISO, no se convierte en fecha
  assert fila["Costo Estimado"] == ""                    # NaN -> celda vacia, nunca "nan"
  assert fila["Urgencia"] == 3 and isinstance(fila["Urgencia"], int)


def test_a_dataframe_convierte_numeros_aunque_lleguen_como_texto_y_rellena_filas_cortas():
  valores = [
    ["Articulo", "Costo Estimado", "Urgencia", "Notas"],
    ["Mouse", "12.5", 4, "ok"],
    ["Teclado", "", 2],                                  # fila corta: falta la ultima celda
  ]

  datos = a_dataframe(valores)

  assert datos["Costo Estimado"].iloc[0] == 12.5
  assert np.isnan(datos["Costo Estimado"].iloc[1])
  assert datos["Urgencia"].tolist() == [4, 2]
  assert np.isnan(datos["Notas"].iloc[1])


def test_a_dataframe_con_hoja_vacia_no_falla():
  assert a_dataframe([]).empty
  assert a_dataframe([[]]).empty


# ---------- guardar y cargar ----------
def test_guardar_y_cargar_devuelve_los_mismos_datos():
  almacen = AlmacenGoogleSheets(HojaCalculoFalsa())
  original = _hojas()

  almacen.guardar(agregar_analisis(original))
  leidas = almacen.cargar()

  esperado, obtenido = original["WishList"], leidas["WishList"]
  assert obtenido["Articulo"].tolist() == esperado["Articulo"].tolist()
  assert obtenido["Costo Estimado"].tolist()[0] == 10.5
  assert np.isnan(obtenido["Costo Estimado"].iloc[1])       # el vacio sigue siendo vacio, no 0
  assert obtenido["Fecha de alta"].iloc[0] == pd.Timestamp("2026-10-08")
  assert leidas["Perfil"]["Ingreso Neto Mensual"].iloc[0] == 190.0


def test_se_escriben_las_tres_hojas_con_su_analisis():
  hoja_calculo = HojaCalculoFalsa()

  AlmacenGoogleSheets(hoja_calculo).guardar(agregar_analisis(_hojas()))

  assert set(hoja_calculo.hojas) == {"WishList", "Perfil", "Analisis"}
  assert "Semaforo" in hoja_calculo.hojas["Analisis"].get_all_values()[0]


def test_sin_hojas_previas_se_carga_vacio_con_las_columnas_correctas():
  leidas = AlmacenGoogleSheets(HojaCalculoFalsa()).cargar()

  assert leidas["WishList"].empty and list(leidas["WishList"].columns)[: len(COLUMNAS_WISHLIST)] == COLUMNAS_WISHLIST
  assert leidas["Perfil"].empty


def test_al_borrar_filas_no_quedan_sobrantes_de_la_version_anterior():
  almacen = AlmacenGoogleSheets(HojaCalculoFalsa())
  almacen.guardar(agregar_analisis(_hojas(articulos=5)))

  almacen.guardar(agregar_analisis(_hojas(articulos=2)))

  assert len(almacen.cargar()["WishList"]) == 2


def test_agranda_la_hoja_si_hace_falta_mas_espacio():
  hoja_calculo = HojaCalculoFalsa()
  hoja_calculo.add_worksheet("WishList", rows=2, cols=2)       # hoja chica

  AlmacenGoogleSheets(hoja_calculo).guardar(agregar_analisis(_hojas(articulos=6)))

  assert len(AlmacenGoogleSheets(hoja_calculo).cargar()["WishList"]) == 6


def test_las_columnas_de_dinero_reciben_formato_de_dolares_en_su_columna():
  hoja_calculo = HojaCalculoFalsa()

  AlmacenGoogleSheets(hoja_calculo).guardar(_hojas())

  reglas = hoja_calculo.hojas["WishList"].reglas_de_formato
  columna_costo = chr(65 + COLUMNAS_WISHLIST.index("Costo Estimado"))
  assert any(r["range"].startswith(f"{columna_costo}2:{columna_costo}") for r in reglas)
  assert all(r["format"]["numberFormat"]["type"] == "CURRENCY" for r in reglas)


def test_un_fallo_de_formato_no_impide_guardar():
  hoja_calculo = HojaCalculoFalsa()
  original = HojaFalsa.batch_format
  HojaFalsa.batch_format = lambda self, reglas: (_ for _ in ()).throw(RuntimeError("formato"))
  try:
    AlmacenGoogleSheets(hoja_calculo).guardar(_hojas())
  finally:
    HojaFalsa.batch_format = original

  assert len(AlmacenGoogleSheets(hoja_calculo).cargar()["WishList"]) == 3


# ---------- errores ----------
@pytest.mark.parametrize("codigo, palabra", [(403, "compártela"), (404, "spreadsheet_id"), (429, "espera")])
def test_los_errores_de_google_se_traducen_a_mensajes_claros(codigo, palabra):
  hoja_calculo = HojaCalculoFalsa()
  hoja_calculo.worksheet = lambda nombre: (_ for _ in ()).throw(_error_api(codigo))

  with pytest.raises(ErrorAlmacen, match=palabra):
    AlmacenGoogleSheets(hoja_calculo).cargar()


def test_un_fallo_de_conexion_al_leer_no_se_confunde_con_hoja_vacia():
  """Si se confundiera, la app mostraria la lista vacia y el siguiente guardado borraria todo."""
  hoja_calculo = HojaCalculoFalsa()
  hoja_calculo.worksheet = lambda nombre: (_ for _ in ()).throw(ConnectionError("sin internet"))

  with pytest.raises(ErrorAlmacen, match="conectar"):
    AlmacenGoogleSheets(hoja_calculo).cargar()


def test_si_falla_la_escritura_los_datos_anteriores_siguen_en_la_hoja():
  hoja_calculo = HojaCalculoFalsa()
  almacen = AlmacenGoogleSheets(hoja_calculo)
  almacen.guardar(agregar_analisis(_hojas(articulos=3)))
  original = HojaFalsa.update
  HojaFalsa.update = lambda self, values, range_name=None, raw=True: (_ for _ in ()).throw(_error_api(500))
  try:
    with pytest.raises(ErrorAlmacen):
      almacen.guardar(agregar_analisis(_hojas(articulos=1)))
  finally:
    HojaFalsa.update = original

  assert len(almacen.cargar()["WishList"]) == 3             # no se borro nada


def test_excel_abierto_se_reporta_como_error_claro(tmp_path, monkeypatch):
  def bloqueado(hojas, ruta):
    raise PermissionError("bloqueado")
  monkeypatch.setattr(almacenamiento, "guardar_excel", bloqueado)

  with pytest.raises(ErrorAlmacen, match="Excel está abierto"):
    AlmacenExcel(tmp_path / "x.xlsx").guardar(_hojas())


def test_el_almacen_excel_guarda_y_carga(tmp_path):
  almacen = AlmacenExcel(tmp_path / "datos.xlsx")

  almacen.guardar(agregar_analisis(_hojas()))

  assert almacen.cargar()["WishList"]["Articulo"].tolist() == ["Cosa 0", "Cosa 1", "Cosa 2"]
