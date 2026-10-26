"""Las medidas del reporte de Power BI (powerbi/medidas.dax) escritas en pandas.

Asi las tarjetas de la app dan los mismos numeros que las de Power BI. Reciben el analisis ya filtrado
(como un segmentador) y el ingreso mensual. Sin Streamlit: se prueban con pytest.
"""
import math

import numpy as np
import pandas as pd

COMPRADO = "Comprado"


def plazos_de_espera(analisis: pd.DataFrame) -> pd.Series:
  """Meses de espera que son un numero (sin vacios ni infinitos: esos articulos no tienen plazo)."""
  meses = analisis["Meses de Espera"].astype(float)
  return meses[np.isfinite(meses)]


def _contar(analisis: pd.DataFrame, semaforo: str) -> int:
  return int((analisis["Semaforo"] == semaforo).sum())


def calcular_medidas(analisis: pd.DataFrame, ingreso: float) -> dict[str, float]:
  """Una entrada por medida DAX, con el mismo nombre que en medidas.dax."""
  pendientes = analisis[analisis["Semaforo"] != COMPRADO]
  total_pendiente = float(pendientes["Costo Estimado"].sum())    # los costos vacios no suman
  plazos = plazos_de_espera(pendientes)
  return {
    "Costo Total": float(analisis["Costo Estimado"].sum()),
    "Articulos Pendientes": len(pendientes),
    "Total Pendiente": total_pendiente,
    "Por Cotizar": _contar(analisis, "Por cotizar"),
    # DIVIDE: si no hay ingreso queda vacio en vez de dar error
    "% de un Mes de Ingreso": total_pendiente / ingreso if ingreso > 0 else math.nan,
    "Comprar Ya": _contar(analisis, "Comprar ya"),
    "Esperar": _contar(analisis, "Esperar"),
    "No Conviene": _contar(analisis, "No conviene"),
    "Plazo Maximo (meses)": float(plazos.max()) if not plazos.empty else math.nan,
  }
