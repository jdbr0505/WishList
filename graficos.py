"""Graficos del dashboard (figuras de Plotly). Sin Streamlit: se pueden probar con pytest."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from finanzas import (
  MESES_MAXIMO_ESPERA, PORC_AHORRO, PORC_DESEOS, PORC_NECESIDADES,
  Perfil, deseos_disponibles, fuera_de_alcance, margen_necesidades,
)

# El color del semaforo significa lo mismo en todos los graficos
COLORES_SEMAFORO = {
  "Comprar ya": "#2e9e5b",
  "Esperar": "#e0a800",
  "No conviene": "#d64545",
  "Por cotizar": "#8a8f98",
  "Clasificar": "#8a8f98",
  "Falta perfil": "#8a8f98",
}
COLOR_META = "#9aa3b2"
COLOR_REAL = "#3b6fd4"
COLOR_DESEO = "#7b5cd6"
COLOR_NECESIDAD = "#1f9db5"
MAX_MESES_GRAFICO = 12


def _base(figura: go.Figure, titulo: str) -> go.Figure:
  figura.update_layout(
    title=titulo,
    margin=dict(l=10, r=10, t=50, b=10),
    legend=dict(orientation="h", y=-0.2),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
  )
  return figura


def grafico_503020(perfil: Perfil) -> go.Figure:
  """Barras agrupadas: meta 50/30/20 contra como se reparte realmente tu mes."""
  categorias = ["Necesidades", "Deseos", "Ahorro"]
  metas = [PORC_NECESIDADES * 100, PORC_DESEOS * 100, PORC_AHORRO * 100]
  ahorro_real = perfil.ingreso - perfil.gastos_fijos - perfil.deseos_gastados
  reales = [
    perfil.gastos_fijos / perfil.ingreso * 100,
    perfil.deseos_gastados / perfil.ingreso * 100,
    ahorro_real / perfil.ingreso * 100,
  ]

  figura = go.Figure([
    go.Bar(name="Meta", x=categorias, y=metas, marker_color=COLOR_META, text=[f"{v:.0f}%" for v in metas]),
    go.Bar(name="Real", x=categorias, y=reales, marker_color=COLOR_REAL, text=[f"{v:.0f}%" for v in reales]),
  ])
  figura.update_layout(barmode="group", yaxis_title="% del ingreso")
  return _base(figura, "Meta 50/30/20 contra tu mes real")


def grafico_ranking(analisis: pd.DataFrame, limite: int = 10) -> go.Figure:
  """Barras horizontales con los articulos pendientes de mayor prioridad, coloreados por semaforo."""
  pendientes = analisis[analisis["Semaforo"] != "Comprado"].nlargest(limite, "Puntaje")
  colores = [COLORES_SEMAFORO.get(s, COLOR_META) for s in pendientes["Semaforo"]]

  figura = go.Figure(go.Bar(
    x=pendientes["Puntaje"],
    y=pendientes["Articulo"],
    orientation="h",
    marker_color=colores,
    text=pendientes["Semaforo"],
    hovertext=pendientes["Motivo"],
  ))
  figura.update_yaxes(autorange="reversed")
  figura.update_xaxes(title="Puntaje de prioridad (0-100)", range=[0, 100])
  return _base(figura, "Ranking de prioridad (color = semáforo)")


def _puntos_de_compra(analisis: pd.DataFrame, tipo: str, aporte: float) -> pd.DataFrame:
  """Articulos de un tipo que estan en la fila de espera (plazo finito y al alcance), con su costo acumulado."""
  grupo = analisis[(analisis["Tipo"] == tipo) & analisis["Meses de Espera"].notna()]
  # np.isfinite funciona tambien con listas vacias (apply devolvia un tipo que rompia el filtro)
  grupo = grupo[np.isfinite(grupo["Meses de Espera"].astype(float))]
  grupo = grupo[~fuera_de_alcance(grupo["Costo Estimado"], aporte)]
  grupo = grupo.sort_values("Puntaje", ascending=False, kind="stable")
  return grupo.assign(acumulado=grupo["Costo Estimado"].cumsum())


def grafico_plan_de_compras(analisis: pd.DataFrame, perfil: Perfil) -> go.Figure:
  """Linea = presupuesto acumulado; cada punto = una compra en el mes en que el presupuesto la alcanza."""
  meses = list(range(0, MAX_MESES_GRAFICO + 1))
  figura = go.Figure()
  acumulados = []

  for tipo, plural, aporte, color in (
    ("Deseo", "deseos", deseos_disponibles(perfil), COLOR_DESEO),
    ("Necesidad", "necesidades", margen_necesidades(perfil), COLOR_NECESIDAD),
  ):
    figura.add_trace(go.Scatter(
      x=meses, y=[aporte * m for m in meses], mode="lines",
      name=f"Presupuesto acumulado: {plural}", line=dict(color=color, dash="dot"),
    ))
    puntos = _puntos_de_compra(analisis, tipo, aporte)
    acumulados.extend(puntos["acumulado"].tolist())
    figura.add_trace(go.Scatter(
      x=puntos["Meses de Espera"], y=puntos["acumulado"], mode="markers",
      name=f"Compras: {plural}", marker=dict(color=color, size=11),
      hovertext=puntos["Articulo"], hoverinfo="text+y",
    ))

  figura.update_xaxes(title="Meses desde hoy", range=[0, MESES_MAXIMO_ESPERA + 1])
  # el eje Y se ajusta a las compras (la linea de presupuesto sigue sin tope y se sale del cuadro)
  tope_y = max(acumulados) * 1.3 if acumulados else None
  figura.update_yaxes(title="Costo acumulado (USD)", range=[0, tope_y] if tope_y else None, tickprefix="$")
  return _base(figura, "Plan de compras: costo acumulado contra presupuesto")
