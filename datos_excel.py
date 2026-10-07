"""Lectura, limpieza y escritura del Excel central (hojas WishList y Perfil).

Este modulo no usa Streamlit: asi se puede probar con pytest sin abrir la app.
"""
import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

COLUMNAS_WISHLIST = [
  "Articulo", "Tipo", "Costo Estimado", "Estado", "Notas",
  "Frecuencia", "Urgencia", "Valor", "Fecha de alta",
]
COLUMNAS_PERFIL = [
  "Ingreso Neto Mensual", "Gastos fijos", "Deseos ya gastados",
  "Ahorro actual", "Meses de Fondo de emergencia objetivo",
]

TIPOS = ["Deseo", "Necesidad"]
ESTADOS = ["Pendiente", "Comprado"]
FRECUENCIAS = ["Único", "Mensual", "Anual"]

COLUMNAS_TEXTO = ["Articulo", "Tipo", "Estado", "Frecuencia"]
COLUMNAS_PUNTAJE = ["Urgencia", "Valor"]
PUNTAJE_POR_DEFECTO = 3
TEXTO_POR_DEFECTO = {
  "Tipo": "Sin clasificar",
  "Estado": "Pendiente",
  "Frecuencia": "Único",
}


def _con_columnas(datos, columnas):
  """Devuelve una copia con las columnas esperadas primero; agrega las que falten (vacias)
  y conserva las extra que el usuario haya puesto en Excel."""
  extras = [c for c in datos.columns if c not in columnas]
  return datos.reindex(columns=columnas + extras)


def normalizar_wishlist(datos):
  """Limpia la hoja WishList: columnas completas, textos sin espacios y valores por defecto."""
  limpios = _con_columnas(datos, COLUMNAS_WISHLIST)

  for columna in COLUMNAS_TEXTO:
    # astype("string") evita el error de .str cuando la columna viene vacia; los vacios siguen vacios
    limpios[columna] = limpios[columna].astype("string").str.strip()
  for columna, defecto in TEXTO_POR_DEFECTO.items():
    limpios[columna] = limpios[columna].fillna(defecto)

  for columna in COLUMNAS_PUNTAJE:
    # errors="coerce" convierte lo que no sea numero en vacio, y luego se rellena
    numeros = pd.to_numeric(limpios[columna], errors="coerce")
    limpios[columna] = numeros.fillna(PUNTAJE_POR_DEFECTO).astype(int)

  limpios["Fecha de alta"] = pd.to_datetime(limpios["Fecha de alta"], errors="coerce")
  return limpios


def normalizar_perfil(datos):
  """Quita espacios de los nombres de columna (una cabecera con espacio final es una trampa en Excel y DAX)."""
  limpios = datos.rename(columns=lambda nombre: str(nombre).strip())
  return _con_columnas(limpios, COLUMNAS_PERFIL)


def cargar_datos(ruta):
  """Carga todas las hojas en un diccionario {nombre_de_hoja: DataFrame}."""
  vacias = {
    "WishList": pd.DataFrame(columns=COLUMNAS_WISHLIST),
    "Perfil": pd.DataFrame(columns=COLUMNAS_PERFIL),
  }
  # las hojas leidas pisan a las vacias; si falta alguna se usa la vacia
  hojas = pd.read_excel(ruta, sheet_name=None) if ruta.exists() else {}
  todas = {**vacias, **hojas}
  return {
    **todas,
    "WishList": normalizar_wishlist(todas["WishList"]),
    "Perfil": normalizar_perfil(todas["Perfil"]),
  }


def agregar_tabla(hoja, datos, nombre):
  """Convierte el rango de datos de la hoja en una Tabla oficial de Excel."""
  # Excel no acepta una tabla sin filas de datos: se deja la hoja como rango
  if datos.empty:
    return

  # Rango exacto: de A1 hasta la ultima columna y la ultima fila (cabecera + datos)
  ultima_columna = get_column_letter(datos.shape[1])
  rango = f"A1:{ultima_columna}{len(datos) + 1}"

  tabla = Table(displayName=nombre, ref=rango)
  tabla.tableStyleInfo = TableStyleInfo(
    name="TableStyleMedium9",
    showFirstColumn=False,
    showLastColumn=False,
    showRowStripes=True,
  )
  hoja.add_table(tabla)


def guardar_excel(hojas, ruta):
  """Escribe todas las hojas, cada una como Tabla. Crea el libro desde cero:
  no queda ninguna tabla anterior, asi que no puede duplicarse."""
  with pd.ExcelWriter(ruta, engine="openpyxl") as writer:
    for nombre_hoja, datos in hojas.items():
      datos.to_excel(writer, sheet_name=nombre_hoja, index=False)
      # nombre unico por hoja y sin espacios: TablaWishList, TablaPerfil
      nombre_tabla = f"Tabla{nombre_hoja.replace(' ', '')}"
      agregar_tabla(writer.sheets[nombre_hoja], datos, nombre_tabla)
