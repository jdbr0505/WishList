import openpyxl
import pandas as pd

from datos_excel import (
  COLUMNAS_PERFIL, COLUMNAS_WISHLIST,
  cargar_datos, guardar_excel, normalizar_perfil, normalizar_wishlist,
)


def _wishlist_antigua():
  """Hoja como estaba antes de las columnas nuevas, con los defectos reales de tu Excel."""
  return pd.DataFrame({
    "Articulo": ["Medias ", "\n Mando", "Power bank"],
    "Tipo": ["Deseo ", "Deseo", None],
    "Costo Estimado": [50.0, 2.0, None],
    "Estado": ["Comprado", None, None],
    "Notas": [None, None, None],
  })


def test_normalizar_wishlist_quita_espacios_y_saltos_de_linea():
  limpios = normalizar_wishlist(_wishlist_antigua())

  assert limpios["Articulo"].tolist() == ["Medias", "Mando", "Power bank"]
  assert limpios["Tipo"].iloc[0] == "Deseo"


def test_normalizar_wishlist_rellena_vacios_sin_inventar_costos():
  limpios = normalizar_wishlist(_wishlist_antigua())

  assert limpios["Tipo"].iloc[2] == "Sin clasificar"
  assert limpios["Estado"].tolist() == ["Comprado", "Pendiente", "Pendiente"]
  assert limpios["Costo Estimado"].isna().iloc[2]


def test_normalizar_wishlist_agrega_columnas_nuevas_con_defectos():
  limpios = normalizar_wishlist(_wishlist_antigua())

  assert list(limpios.columns[: len(COLUMNAS_WISHLIST)]) == COLUMNAS_WISHLIST
  assert (limpios["Urgencia"] == 3).all()
  assert (limpios["Frecuencia"] == "Único").all()


def test_normalizar_wishlist_no_modifica_el_original():
  original = _wishlist_antigua()
  normalizar_wishlist(original)

  assert original["Articulo"].iloc[0] == "Medias "


def test_normalizar_wishlist_acepta_dataframe_vacio():
  limpios = normalizar_wishlist(pd.DataFrame(columns=COLUMNAS_WISHLIST))

  assert limpios.empty
  assert list(limpios.columns) == COLUMNAS_WISHLIST


def test_normalizar_perfil_limpia_cabeceras():
  sucio = pd.DataFrame(columns=["Ingreso Neto Mensual ", "Gastos fijos ", "Deseos ya gastados ",
                                "Ahorro actual", "Meses de Fondo de emergencia objetivo"])

  assert list(normalizar_perfil(sucio).columns) == COLUMNAS_PERFIL


def test_guardar_y_cargar_conserva_ambas_hojas_con_una_tabla_cada_una(tmp_path):
  ruta = tmp_path / "prueba.xlsx"
  perfil = pd.DataFrame([[1000.0, 400.0, 100.0, 500.0, 3.0]], columns=COLUMNAS_PERFIL)
  hojas = {"WishList": normalizar_wishlist(_wishlist_antigua()), "Perfil": perfil}

  guardar_excel(hojas, ruta)
  guardar_excel(cargar_datos(ruta), ruta)  # segundo guardado: no debe duplicar tablas

  libro = openpyxl.load_workbook(ruta)
  assert libro.sheetnames == ["WishList", "Perfil"]
  assert dict(libro["WishList"].tables.items()) == {"TablaWishList": f"A1:I4"}
  assert dict(libro["Perfil"].tables.items()) == {"TablaPerfil": "A1:E2"}
  assert cargar_datos(ruta)["Perfil"]["Ingreso Neto Mensual"].iloc[0] == 1000.0


def test_hoja_sin_filas_queda_sin_tabla(tmp_path):
  ruta = tmp_path / "vacio.xlsx"

  guardar_excel(cargar_datos(ruta), ruta)

  libro = openpyxl.load_workbook(ruta)
  assert dict(libro["Perfil"].tables.items()) == {}
