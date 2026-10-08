#importar librerias necesarias para el sistema
from pathlib import Path
import pandas as pd
import streamlit as st

from datos_excel import (
  COLUMNAS_DINERO, COLUMNAS_PERFIL, ESTADOS, FRECUENCIAS, MONEDA, TIPOS, TIPOS_VALIDOS,
  cargar_datos, excel_en_bytes, filtrar_tabla, guardar_excel, preparar_edicion,
)
from datos_demo import hojas_demo
from graficos import grafico_503020, grafico_plan_de_compras, grafico_ranking
from finanzas import (
  agregar_analisis, analizar_wishlist, deseos_disponibles, fondo_completo, margen_necesidades,
  meses_fondo_cubiertos, perfil_desde_hoja, presupuesto_503020,
)

ICONOS_SEMAFORO = {
  "Comprar ya": "🟢 Comprar ya",
  "Esperar": "🟡 Esperar",
  "No conviene": "🔴 No conviene",
  "Por cotizar": "⚪ Por cotizar",
  "Clasificar": "⚪ Clasificar",
  "Falta perfil": "⚪ Falta perfil",
  "Comprado": "✅ Comprado",
}
COLUMNAS_ANALISIS = [
  "Articulo", "Tipo", "Costo Estimado", "Puntaje", "% del Ingreso",
  "Meses de Espera", "Fecha Estimada", "Semaforo", "Motivo",
]

#ruta del archivo excel junto a este script (no depende de la carpeta desde donde se lance streamlit)
archivo = Path(__file__).parent / "TablaWishList.xlsx"

# Configuración de la página
st.set_page_config(
    page_title="WishList", page_icon="📊", layout="centered"
)

st.title("📝 WishList")
st.markdown(f"Sistema para organizar tus compras y prioridades · todos los montos en dólares ({MONEDA})")

# las columnas de dinero se muestran con el simbolo $ en todas las tablas (el valor no cambia)
# formato fijo "$50.00" (el preset "dollar" cambia segun el idioma del navegador y mostraba "50,00 $")
FORMATO_DINERO = "$%.2f"
CONFIG_DINERO = {nombre: st.column_config.NumberColumn(nombre, format=FORMATO_DINERO) for nombre in COLUMNAS_DINERO}


def dinero(valor):
  """Da formato de dolares a un monto para mostrarlo, por ejemplo $1,250."""
  return f"${valor:,.0f}"


def guardar(hojas_a_guardar):
  """Guarda todas las hojas; devuelve True si salio bien (el Excel abierto da PermissionError)."""
  if usar_demo:
    st.warning("Modo ejemplo: no se guarda nada en tu Excel. Apaga el modo ejemplo para guardar de verdad.")
    return False
  try:
    # la hoja Analisis se recalcula en cada guardado para que Excel y Power BI vean lo mismo que la app
    guardar_excel(agregar_analisis(hojas_a_guardar), archivo)
  except PermissionError:
    st.error("El Excel está abierto o OneDrive lo bloquea. Ciérralo y vuelve a guardar.")
    return False
  return True


def valor_inicial(fila, columna):
  """Valor del perfil guardado para precargar el formulario (0.0 si no hay o esta vacio)."""
  if fila is None or pd.isna(fila[columna]):
    return 0.0
  return float(fila[columna])


usar_demo = st.sidebar.toggle(
  "Ver con datos de ejemplo",
  help="Muestra el sistema con datos inventados. No lee ni modifica tu Excel.",
)
if usar_demo:
  st.sidebar.info("Modo ejemplo activo: lo que ves no son tus datos y no se guarda nada.")

hojas = hojas_demo() if usar_demo else cargar_datos(archivo)
df = hojas["WishList"]
perfil = hojas["Perfil"]

tab_articulos, tab_editar, tab_perfil, tab_analisis, tab_dashboard = st.tabs(
  ["Artículos", "Editar lista", "Perfil financiero", "Análisis", "Dashboard"]
)

with tab_articulos:
  # Formulario de entrada para los campos
  with st.form("entry_form", clear_on_submit=True):

    st.subheader("Nuevo Articulo")
    col1, col2 = st.columns(2)

    with col1:
      articulo = st.text_input("Articulo", max_chars=100)
      tipo = st.selectbox("Tipo", TIPOS)
      frecuencia = st.selectbox("Frecuencia", FRECUENCIAS)
      urgencia = st.slider("Urgencia (1 = puede esperar, 5 = ya)", 1, 5, 3)
    with col2:
      # value=None deja el campo vacio: vacio significa "por cotizar" (nunca se guarda 0)
      costo_estimado = st.number_input(f"Costo Estimado ({MONEDA}, vacío = por cotizar)", value=None, min_value=0.0)
      estado = st.selectbox("Estado", ESTADOS)
      valor = st.slider("Valor percibido (1 = poco, 5 = mucho)", 1, 5, 3)
      notas = st.text_area("Notas")

    submit_button = st.form_submit_button(label="Guardar", width="stretch")

    if submit_button:
      nombre = articulo.strip()

      # Reunir todos los problemas antes de decidir si se guarda
      errores = []
      if nombre == "":
        errores.append("Por favor, completa al menos el campo de Articulo.")
      elif df["Articulo"].str.lower().eq(nombre.lower()).fillna(False).any():
        errores.append(f"'{nombre}' ya está en la lista.")
      if costo_estimado is not None and costo_estimado <= 0:
        errores.append("Si aún no lo cotizaste, deja el costo vacío (no pongas 0).")

      if errores:
        for error in errores:
          st.error(error)
      else:
        nuevo_articulo = pd.DataFrame([{
            "Articulo": nombre,
            "Tipo": tipo,
            "Costo Estimado": float("nan") if costo_estimado is None else costo_estimado,
            "Estado": estado,
            "Notas": notas,
            "Frecuencia": frecuencia,
            "Urgencia": urgencia,
            "Valor": valor,
            "Fecha de alta": pd.Timestamp.today().normalize(),
        }])

        # Concatenar en una copia: df solo cambia si el guardado sale bien
        df_actualizado = pd.concat([df, nuevo_articulo], ignore_index=True)

        # se reenvian TODAS las hojas: lo que no se escribe se pierde
        if guardar({**hojas, "WishList": df_actualizado}):
          df = df_actualizado
          st.success("¡Datos guardados exitosamente en el Excel!")

  # Visualización rápida de los datos actuales, con filtros (solo cambian lo que se ve, no los datos)
  st.divider()
  st.subheader("Vista previa de los datos actuales")
  filtro_texto, filtro_tipo, filtro_estado = st.columns([2, 1, 1])
  buscar = filtro_texto.text_input("Buscar artículo", key="buscar_lista")
  tipos_elegidos = filtro_tipo.multiselect("Tipo", TIPOS_VALIDOS, key="filtro_tipo")
  estados_elegidos = filtro_estado.multiselect("Estado", ESTADOS, key="filtro_estado")

  df_filtrado = filtrar_tabla(df, {"Tipo": tipos_elegidos, "Estado": estados_elegidos}, buscar)
  st.caption(f"Mostrando {len(df_filtrado)} de {len(df)} artículos")
  st.dataframe(df_filtrado, width="stretch", column_config=CONFIG_DINERO)

with tab_editar:
  st.subheader("Editar lista")
  st.caption(
    "Cambia precios, estados o tipos directo en la tabla. Para borrar, marca la casilla de la fila "
    "y pulsa Suprimir. Para agregar, escribe en la última fila. Nada se guarda hasta pulsar «Guardar cambios»."
  )
  # tras guardar se recarga la pagina; el mensaje se guarda en session_state para que sobreviva a la recarga
  if "mensaje_editor" in st.session_state:
    st.success(st.session_state.pop("mensaje_editor"))

  # cambiar la clave reinicia el editor: asi no queda un "delta" viejo aplicado sobre datos ya guardados
  version_editor = st.session_state.get("version_editor", 0)
  editado = st.data_editor(
    df,
    key=f"editor_{version_editor}",
    num_rows="dynamic",
    hide_index=True,
    width="stretch",
    disabled=["Fecha de alta"],
    column_config={
      "Articulo": st.column_config.TextColumn("Articulo", required=True, max_chars=100),
      "Tipo": st.column_config.SelectboxColumn("Tipo", options=TIPOS_VALIDOS),
      "Costo Estimado": st.column_config.NumberColumn(
        "Costo Estimado", min_value=0.0, format=FORMATO_DINERO, help=f"En dólares ({MONEDA}). Vacío = por cotizar"
      ),
      "Estado": st.column_config.SelectboxColumn("Estado", options=ESTADOS),
      "Frecuencia": st.column_config.SelectboxColumn("Frecuencia", options=FRECUENCIAS),
      "Urgencia": st.column_config.NumberColumn("Urgencia", min_value=1, max_value=5, step=1),
      "Valor": st.column_config.NumberColumn("Valor", min_value=1, max_value=5, step=1),
      "Fecha de alta": st.column_config.DateColumn("Fecha de alta"),
    },
  )

  if st.button("Guardar cambios", type="primary", key=f"guardar_editor_{version_editor}"):
    lista_limpia, errores_edicion, cambios = preparar_edicion(df, editado)
    hay_cambios = cambios["agregadas"] or cambios["borradas"] or cambios["modificadas"]

    if errores_edicion:
      for error in errores_edicion:
        st.error(error)
    elif not hay_cambios:
      st.info("No hay cambios para guardar.")
    elif guardar({**hojas, "WishList": lista_limpia}):
      mensaje = (
        f"Cambios guardados. Filas modificadas: {cambios['modificadas']}, "
        f"agregadas: {cambios['agregadas']}, borradas: {cambios['borradas']}."
      )
      if cambios["costos_en_cero"]:
        mensaje += f" {cambios['costos_en_cero']} costos en 0 pasaron a «por cotizar» (vacío)."
      st.session_state["mensaje_editor"] = mensaje
      st.session_state["version_editor"] = version_editor + 1
      st.rerun()

with tab_perfil:
  st.subheader("Perfil financiero")
  st.caption("Base de la regla 50/30/20: necesidades 50%, deseos 30%, ahorro 20% de tu ingreso neto.")

  fila_actual = perfil.iloc[0] if not perfil.empty else None

  with st.form("perfil_form"):
    valores = {
        columna: st.number_input(
            f"{columna} ({MONEDA})" if columna in COLUMNAS_DINERO else columna,
            min_value=0.0,
            value=valor_inicial(fila_actual, columna),
        )
        for columna in COLUMNAS_PERFIL
    }
    guardar_perfil = st.form_submit_button(label="Guardar perfil", width="stretch")

  if guardar_perfil:
    if valores["Ingreso Neto Mensual"] <= 0:
      st.error("El ingreso neto mensual debe ser mayor que cero.")
    elif guardar({**hojas, "Perfil": pd.DataFrame([valores])}):
      st.success("Perfil guardado.")
      perfil = pd.DataFrame([valores])

  st.dataframe(perfil, width="stretch", column_config=CONFIG_DINERO)

# se calcula al final para usar el df y el perfil ya actualizados en esta ejecucion
with tab_analisis:
  perfil_actual = perfil_desde_hoja(perfil)

  if not perfil_actual.completo:
    st.info("Completa tu perfil financiero (pestaña anterior) para ver el análisis.")
  else:
    presupuesto = presupuesto_503020(perfil_actual.ingreso)
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Necesidades (50%)", dinero(presupuesto["Necesidades"]), f"quedan {dinero(margen_necesidades(perfil_actual))}")
    col_b.metric("Deseos (30%)", dinero(presupuesto["Deseos"]), f"quedan {dinero(deseos_disponibles(perfil_actual))}")
    col_c.metric("Ahorro (20%)", dinero(presupuesto["Ahorro"]))

    cubiertos = meses_fondo_cubiertos(perfil_actual)
    if fondo_completo(perfil_actual):
      st.success(f"Fondo de emergencia completo: cubre {cubiertos:.1f} meses de gastos fijos.")
    elif pd.isna(cubiertos):
      st.warning("Indica tus gastos fijos para calcular tu fondo de emergencia.")
    else:
      st.warning(f"Fondo de emergencia incompleto: cubre {cubiertos:.1f} meses. Los deseos esperan hasta completarlo.")

  analisis = analizar_wishlist(df, perfil_actual).sort_values("Puntaje", ascending=False)

  # filtros solo para la tabla; el Dashboard sigue usando `analisis` completo
  a_texto, a_tipo, a_semaforo = st.columns([2, 1, 1])
  buscar_analisis = a_texto.text_input("Buscar artículo", key="buscar_analisis")
  tipos_analisis = a_tipo.multiselect("Tipo", TIPOS_VALIDOS, key="filtro_tipo_analisis")
  semaforos_elegidos = a_semaforo.multiselect(
    "Semáforo", list(ICONOS_SEMAFORO), format_func=ICONOS_SEMAFORO.get, key="filtro_semaforo"
  )
  analisis_filtrado = filtrar_tabla(
    analisis, {"Tipo": tipos_analisis, "Semaforo": semaforos_elegidos}, buscar_analisis
  )
  st.caption(f"Mostrando {len(analisis_filtrado)} de {len(analisis)} artículos")

  vista = analisis_filtrado[COLUMNAS_ANALISIS].assign(
    Semaforo=analisis_filtrado["Semaforo"].map(ICONOS_SEMAFORO),
    **{"Meses de Espera": analisis_filtrado["Meses de Espera"].replace(float("inf"), float("nan"))},
  )
  st.dataframe(vista, width="stretch", hide_index=True, column_config=CONFIG_DINERO)

with tab_dashboard:
  if not perfil_actual.completo:
    st.info("Completa tu perfil financiero para ver el dashboard.")
  else:
    pendientes = analisis[analisis["Semaforo"] != "Comprado"]
    con_precio = pendientes[pendientes["Costo Estimado"] > 0]
    total_pendiente = con_precio["Costo Estimado"].sum()
    plazos = pendientes["Meses de Espera"].replace(float("inf"), float("nan")).dropna()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Pendiente (con precio)", dinero(total_pendiente))
    k2.metric("% de un mes de ingreso", f"{total_pendiente / perfil_actual.ingreso * 100:.0f}%")
    k3.metric("Plazo para cumplir la lista", f"{int(plazos.max())} meses" if not plazos.empty else "—")
    k4.metric("Por cotizar", int((analisis["Semaforo"] == "Por cotizar").sum()))

    cuenta = analisis["Semaforo"].value_counts()
    st.caption(
      "  ·  ".join(f"{ICONOS_SEMAFORO.get(nombre, nombre)}: {cantidad}" for nombre, cantidad in cuenta.items())
    )

    st.plotly_chart(grafico_503020(perfil_actual), width="stretch")
    st.plotly_chart(grafico_ranking(analisis), width="stretch")
    st.plotly_chart(grafico_plan_de_compras(analisis, perfil_actual), width="stretch")

# Descarga generada en memoria: usa los datos de esta ejecución (ya con lo guardado) sin leer el disco.
# Va al final del script para ver el df y el perfil más recientes.
with st.sidebar:
  st.divider()
  st.download_button(
    label="📥 Descargar Excel de ejemplo" if usar_demo else "📥 Descargar Excel actualizado",
    data=excel_en_bytes(agregar_analisis({**hojas, "WishList": df, "Perfil": perfil})),
    file_name="WishList_ejemplo.xlsx" if usar_demo else archivo.name,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  )
