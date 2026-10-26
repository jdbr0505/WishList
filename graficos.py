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
GRIS_SEMAFORO = "#8a8f98"   # lo que no es comprar/esperar/descartar (igual que la medida Color Semaforo de Power BI)
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


def _color_semaforo(semaforo: str) -> str:
  return COLORES_SEMAFORO.get(semaforo, GRIS_SEMAFORO)


def grafico_costo_por_decision(analisis: pd.DataFrame) -> go.Figure:
  """Power BI "Costo por Decisión": costo total de cada semaforo, de mayor a menor (sin barras vacias)."""
  costos = analisis.groupby("Semaforo")["Costo Estimado"].sum()
  costos = costos[costos > 0].sort_values(ascending=False)

  figura = go.Figure(go.Bar(
    x=costos.values, y=costos.index, orientation="h",
    marker_color=[_color_semaforo(s) for s in costos.index],
    text=[f"${valor:,.0f}" for valor in costos.values],
  ))
  figura.update_yaxes(autorange="reversed")
  figura.update_xaxes(title="Costo Total (USD)", tickprefix="$")
  return _base(figura, "Costo por Decisión")


def grafico_pendiente_por_tipo(analisis: pd.DataFrame) -> go.Figure:
  """Power BI "Pendiente por tipo": dona con el total pendiente (sin los comprados) de cada tipo."""
  pendientes = analisis[analisis["Semaforo"] != "Comprado"]
  totales = pendientes.groupby("Tipo")["Costo Estimado"].sum()
  totales = totales[totales > 0]
  colores = {"Deseo": COLOR_DESEO, "Necesidad": COLOR_NECESIDAD}

  figura = go.Figure(go.Pie(
    labels=list(totales.index), values=list(totales.values), hole=0.5, sort=False,
    marker=dict(colors=[colores.get(tipo, GRIS_SEMAFORO) for tipo in totales.index]),
  ))
  return _base(figura, "Pendiente por tipo")


def _con_plazo(analisis: pd.DataFrame) -> pd.DataFrame:
  """Articulos con un plazo en meses (sin precio, comprados y fuera de alcance no lo tienen)."""
  return analisis[np.isfinite(analisis["Meses de Espera"].astype(float))]


def grafico_meses_por_articulo(analisis: pd.DataFrame) -> go.Figure:
  """Power BI "Meses de espera por artículo": el que se compra antes queda arriba."""
  articulos = _con_plazo(analisis).sort_values("Meses de Espera", kind="stable")

  figura = go.Figure(go.Bar(
    x=articulos["Meses de Espera"], y=articulos["Articulo"], orientation="h", marker_color=COLOR_REAL,
  ))
  figura.update_yaxes(autorange="reversed")
  figura.update_xaxes(title="Meses de espera")
  return _base(figura, "Meses de espera por artículo")


def grafico_costo_por_mes(analisis: pd.DataFrame) -> go.Figure:
  """Power BI "Costo por mes de compra estimado": total pendiente que toca comprar cada mes."""
  pendientes = _con_plazo(analisis[analisis["Semaforo"] != "Comprado"])
  por_mes = pendientes.groupby("Meses de Espera")["Costo Estimado"].sum()

  figura = go.Figure(go.Bar(
    x=por_mes.index.astype(int), y=por_mes.values, marker_color=COLOR_REAL,
    text=[f"${valor:,.0f}" for valor in por_mes.values],
  ))
  figura.update_xaxes(title="Mes de compra estimado", type="category")
  figura.update_yaxes(title="Total Pendiente (USD)", tickprefix="$")
  return _base(figura, "Costo por mes de compra estimado")


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
