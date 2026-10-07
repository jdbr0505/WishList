"""Datos de ejemplo para ver el dashboard sin tocar tu Excel real."""
import pandas as pd

from datos_excel import COLUMNAS_PERFIL, normalizar_wishlist

# (Articulo, Tipo, Costo Estimado, Estado, Urgencia, Valor, Frecuencia)
_ARTICULOS = [
  ("Audífonos in ears", "Deseo", 120.0, "Pendiente", 3, 4, "Único"),
  ("Teclado mecánico", "Deseo", 90.0, "Pendiente", 2, 4, "Único"),
  ("Pedalera", "Deseo", 250.0, "Pendiente", 3, 5, "Único"),
  ("Hoodie sublimada", "Deseo", 45.0, "Pendiente", 2, 2, "Único"),
  ("Luces LED con Alexa", "Deseo", 60.0, "Pendiente", 1, 3, "Único"),
  ("Guitarra nueva", "Deseo", 3000.0, "Pendiente", 4, 5, "Único"),
  ("Suscripción Workspace", "Deseo", 12.0, "Pendiente", 3, 3, "Mensual"),
  ("Medias", "Necesidad", 30.0, "Pendiente", 5, 3, "Único"),
  ("Mouse", "Necesidad", 60.0, "Pendiente", 4, 4, "Único"),
  ("Zapatos", "Necesidad", 180.0, "Pendiente", 4, 4, "Único"),
  ("Reloj digital", "Deseo", None, "Pendiente", 2, 3, "Único"),
  ("Power bank", "Necesidad", None, "Pendiente", 3, 3, "Único"),
  ("Cuerda E de guitarra", "Deseo", 8.0, "Comprado", 3, 3, "Único"),
  ("Protector de potenciómetro", "Deseo", 15.0, "Comprado", 2, 3, "Único"),
]

# ingreso 1500: deseos 450 (quedan 330), necesidades 750 (quedan 100); fondo = 3.4 meses
_PERFIL = [1500.0, 650.0, 120.0, 2200.0, 3.0]


def hojas_demo():
  """Mismo formato que cargar_datos(): {"WishList": DataFrame, "Perfil": DataFrame}."""
  wishlist = pd.DataFrame(
    _ARTICULOS,
    columns=["Articulo", "Tipo", "Costo Estimado", "Estado", "Urgencia", "Valor", "Frecuencia"],
  )
  return {
    "WishList": normalizar_wishlist(wishlist),
    "Perfil": pd.DataFrame([_PERFIL], columns=COLUMNAS_PERFIL),
  }
