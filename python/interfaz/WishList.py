#importar librerias necesarias para el sistema
import os
import sys
import time
from pathlib import Path
import pandas as pd
import streamlit as st

# la app se lanza desde esta carpeta (python/interfaz): se agrega python/ para poder importar logica y dashboards
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logica import vitrina
from logica.acceso import MODO_DEMO, MODO_VITRINA, diagnosticar_archivo_secretos, elegir_modo
from logica.datos_excel import (
  COLUMNAS_DINERO, COLUMNAS_PERFIL, ESTADOS, FRECUENCIAS, MONEDA, TIPOS, TIPOS_VALIDOS,
  cargar_datos, excel_en_bytes, filtrar_tabla, guardar_excel, preparar_edicion,
)
from logica.datos_demo import hojas_demo
from dashboards.graficos import (
  grafico_503020, grafico_costo_por_decision, grafico_costo_por_mes, grafico_meses_por_articulo,
  grafico_pendiente_por_tipo, grafico_plan_de_compras, grafico_ranking,
)
from logica.medidas import calcular_medidas
from logica.finanzas import (
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

#ruta del Excel central: carpeta excel/ en la raiz del proyecto (no depende de la carpeta desde donde se lance streamlit)
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
archivo = RAIZ_PROYECTO / "excel" / "TablaWishList.xlsx"

VALORES_SI = {"1", "true", "si", "sí", "yes"}


def valor_variable(nombre):
  """Texto de la variable de entorno (o del secreto de Streamlit) `nombre`; vacio si no existe."""
  valor = os.environ.get(nombre, "")
  if valor.strip():
    return valor.strip()
  try:
    return str(st.secrets.get(nombre, "")).strip()
  except Exception:  # sin archivo de secretos
    return ""


def variable_activa(nombre):
  """True si la variable `nombre` vale 1, true, si o yes."""
  return valor_variable(nombre).lower() in VALORES_SI


def modo_de_la_app():
  """Decide entre demostracion, vitrina de solo lectura y uso local (ver acceso.elegir_modo).

  Es seguro por defecto: sin TablaWishList.xlsx al lado y sin permiso explicito, es solo demostracion
  (en una app publicada el Excel no existe: esta ignorado por git).
  """
  return elegir_modo(
    solo_demo=variable_activa("WISHLIST_SOLO_DEMO"),
    vitrina=valor_variable("WISHLIST_MODO").lower() == "vitrina",
    hay_excel_local=archivo.exists(),
    datos_reales=variable_activa("WISHLIST_DATOS_REALES"),
  )

# Configuración de la página
st.set_page_config(
    page_title="WishList", page_icon="📊", layout="wide"
)

st.title("📝 WishList")

# un archivo de secretos ilegible se ignora en silencio: se avisa para no quedar en demostracion sin saber por que
for carpeta in (Path.cwd(), Path.home()):
  problema_secretos = diagnosticar_archivo_secretos(carpeta / ".streamlit" / "secrets.toml")
  if problema_secretos:
    st.warning(problema_secretos)
    break
st.markdown(f"Sistema para organizar tus compras y prioridades · todos los montos en dólares ({MONEDA})")

# las columnas de dinero se muestran con el simbolo $ en todas las tablas (el valor no cambia)
# formato fijo "$50.00" (el preset "dollar" cambia segun el idioma del navegador y mostraba "50,00 $")
FORMATO_DINERO = "$%.2f"
CONFIG_DINERO = {nombre: st.column_config.NumberColumn(nombre, format=FORMATO_DINERO) for nombre in COLUMNAS_DINERO}


def dinero(valor):
  """Da formato de dolares a un monto para mostrarlo, por ejemplo $1,250."""
  return f"${valor:,.0f}"


def guardar(hojas_a_guardar):
  """Guarda todas las hojas en el Excel; devuelve True si salio bien (el Excel abierto da PermissionError)."""
  if SOLO_LECTURA:
    st.error("Esta vitrina es de solo lectura: no se puede modificar nada.")
    return False
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


def pedir_contrasena_vitrina():
  """Formulario de contrasena para ver los datos reales. Devuelve True solo si la clave es correcta."""
  hubo_intento = st.session_state.get("vitrina_intento", False)
  with st.expander("🔒 Ver mis datos reales (con contraseña)", expanded=hubo_intento):
    with st.form("vitrina_clave"):
      clave = st.text_input("Contraseña", type="password")
      entrar = st.form_submit_button("Entrar")
  if not entrar:
    return False

  st.session_state["vitrina_intento"] = True
  ahora = time.time()
  if vitrina.LIMITADOR.bloqueado(ahora):
    st.error("Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.")
    return False
  if vitrina.verificar_clave(clave, st.secrets["VITRINA_SAL"], st.secrets["VITRINA_HASH"]):
    return True
  vitrina.LIMITADOR.registrar_fallo(ahora)
  time.sleep(vitrina.PAUSA_TRAS_FALLO)
  # se cuentan los caracteres (no se repite la clave) para detectar espacios o pegados raros
  st.error(f"Contraseña incorrecta (recibí {len(clave)} caracteres).")
  return False


def salir_de_la_vitrina():
  """Olvida el acceso de esta sesion: la pagina vuelve a la demostracion."""
  st.session_state.pop("vitrina_ok", None)
  st.session_state.pop("vitrina_intento", None)


def abrir_vitrina():
  """Una sola pagina: devuelve las hojas REALES si se dio la contrasena, o None (y se muestra la demostracion).

  Los datos reales no se decodifican hasta que la contrasena es correcta. Si algo falla (configuracion
  incompleta, datos ilegibles) nunca se muestran datos reales: se queda la demostracion y se avisa.
  """
  faltan = vitrina.faltantes_config(st.secrets)
  if faltan:
    st.warning("La vitrina no está configurada del todo (falta: " + ", ".join(faltan) + "), así que se muestra la demostración. Ver docs/VITRINA.md.")
    return None

  if not st.session_state.get("vitrina_ok"):
    if not pedir_contrasena_vitrina():
      return None
    st.session_state["vitrina_ok"] = True
    st.rerun()      # vuelve a dibujar la pagina ya con los datos reales (y sin el formulario)

  try:
    hojas_reales = vitrina.hojas_desde_b64(st.secrets["VITRINA_EXCEL_B64"])
  except Exception:  # no se muestra el detalle: podria incluir datos
    st.session_state.pop("vitrina_ok", None)
    st.error("No pude leer los datos de la vitrina. Revisa el secreto VITRINA_EXCEL_B64. Se muestra la demostración.")
    return None

  st.sidebar.info("Vitrina de solo lectura: no se puede modificar nada.")
  st.sidebar.button("Salir", on_click=salir_de_la_vitrina)
  return hojas_reales


def opciones_de(tabla, columna):
  """Valores distintos de una columna, para llenar un segmentador."""
  return sorted(tabla[columna].dropna().unique())


def tabla_para_mostrar(tabla, columnas):
  """Las columnas elegidas, con el semaforo en iconos y los plazos infinitos como vacios.

  `columnas` debe incluir "Semaforo" y "Meses de Espera".
  """
  return tabla[columnas].assign(
    Semaforo=tabla["Semaforo"].map(ICONOS_SEMAFORO),
    **{"Meses de Espera": tabla["Meses de Espera"].replace(float("inf"), float("nan"))},
  )


def porcentaje_o_guion(valor):
  return "—" if pd.isna(valor) else f"{valor * 100:.0f}%"


def pagina_resumen(analisis, perfil_actual):
  """Pagina "Dashboard" del reporte de Power BI: 3 tarjetas, 2 graficos, meta contra real y una tabla."""
  col_filtros, col_contenido = st.columns([1, 5])
  with col_filtros:
    tipos = st.multiselect("Tipo", opciones_de(analisis, "Tipo"), key="dash_tipo")
    estados = st.multiselect("Estado", opciones_de(analisis, "Estado"), key="dash_estado")
  filtrado = filtrar_tabla(analisis, {"Tipo": tipos, "Estado": estados})

  with col_contenido:
    if filtrado.empty:
      st.info("No hay artículos con esos filtros.")
      return
    medidas = calcular_medidas(filtrado, perfil_actual.ingreso)
    tarjeta_pendiente, tarjeta_mes, tarjeta_cotizar = st.columns(3)
    tarjeta_pendiente.metric("Total Pendiente", dinero(medidas["Total Pendiente"]))
    tarjeta_mes.metric("% de un Mes de Ingreso", porcentaje_o_guion(medidas["% de un Mes de Ingreso"]))
    tarjeta_cotizar.metric("Por Cotizar", medidas["Por Cotizar"])

    izquierda, derecha = st.columns(2)
    izquierda.plotly_chart(grafico_costo_por_decision(filtrado), width="stretch")
    derecha.plotly_chart(grafico_ranking(filtrado, limite=len(filtrado)), width="stretch")

    meta_real, detalle = st.columns([2, 3])
    meta_real.plotly_chart(grafico_503020(perfil_actual), width="stretch")      # no depende de los segmentadores
    detalle.dataframe(
      tabla_para_mostrar(
        filtrado.sort_values("Articulo"), ["Articulo", "Costo Estimado", "Semaforo", "Motivo", "Meses de Espera"]
      ),
      width="stretch", hide_index=True, column_config=CONFIG_DINERO,
    )


def pagina_plan_de_compras(analisis, perfil_actual):
  """Pagina "Plan de compras" del reporte de Power BI: 4 tarjetas, dona, 2 graficos y la tabla de detalle."""
  col_filtros, col_contenido = st.columns([1, 5])
  with col_filtros:
    tipos = st.multiselect("Tipo", opciones_de(analisis, "Tipo"), key="plan_tipo")
    semaforos = st.multiselect("Semáforo", list(ICONOS_SEMAFORO), format_func=ICONOS_SEMAFORO.get, key="plan_semaforo")
  filtrado = filtrar_tabla(analisis, {"Tipo": tipos, "Semaforo": semaforos})

  with col_filtros:
    if not filtrado.empty:
      st.plotly_chart(grafico_pendiente_por_tipo(filtrado), width="stretch")
  with col_contenido:
    if filtrado.empty:
      st.info("No hay artículos con esos filtros.")
      return
    medidas = calcular_medidas(filtrado, perfil_actual.ingreso)
    for tarjeta, nombre, etiqueta in zip(
      st.columns(4),
      ("Articulos Pendientes", "Comprar Ya", "Esperar", "No Conviene"),
      ("Artículos Pendientes", "Comprar Ya", "Esperar", "No Conviene"),
    ):
      tarjeta.metric(etiqueta, medidas[nombre])
    if not pd.isna(medidas["Plazo Maximo (meses)"]):
      st.caption(f"Plazo para cumplir la lista: {int(medidas['Plazo Maximo (meses)'])} meses")

    izquierda, derecha = st.columns(2)
    izquierda.plotly_chart(grafico_meses_por_articulo(filtrado), width="stretch")
    derecha.plotly_chart(grafico_costo_por_mes(filtrado), width="stretch")

    st.subheader("Detalle por prioridad")
    columnas = [
      "Articulo", "Tipo", "Frecuencia", "Costo Estimado", "Puntaje", "Meses de Espera", "Fecha Estimada", "Semaforo", "Motivo",
    ]
    st.dataframe(
      tabla_para_mostrar(filtrado.sort_values("Puntaje", ascending=False), columnas),
      width="stretch", hide_index=True, column_config=CONFIG_DINERO,
    )


def valor_inicial(fila, columna):
  """Valor del perfil guardado para precargar el formulario (0.0 si no hay o esta vacio)."""
  if fila is None or pd.isna(fila[columna]):
    return 0.0
  return float(fila[columna])


modo = modo_de_la_app()

# Vitrina = una sola pagina: sin la contrasena se ve la demostracion; con ella, los datos reales en solo lectura
hojas_reales_vitrina = abrir_vitrina() if modo == MODO_VITRINA else None
SOLO_LECTURA = hojas_reales_vitrina is not None

if SOLO_LECTURA:
  usar_demo = False
elif modo in (MODO_DEMO, MODO_VITRINA):
  # demostracion publica: el interruptor no existe, asi que no hay forma de pedir datos reales sin la contrasena
  usar_demo = True
  st.info("Demostración con datos inventados. Aquí no se guarda nada; puedes explorar todas las pestañas.")
  st.sidebar.info("Versión de demostración: los datos son inventados y no se guarda nada.")
  if modo == MODO_DEMO and not variable_activa("WISHLIST_SOLO_DEMO"):
    st.sidebar.caption("Para usar tus propios datos en tu equipo, define WISHLIST_DATOS_REALES=1 (ver docs/DESPLIEGUE.md).")
else:
  usar_demo = st.sidebar.toggle(
    "Ver con datos de ejemplo",
    help="Muestra el sistema con datos inventados. No lee ni modifica tu Excel.",
  )
  if usar_demo:
    st.sidebar.info("Modo ejemplo activo: lo que ves no son tus datos y no se guarda nada.")

if SOLO_LECTURA:
  hojas = hojas_reales_vitrina
elif usar_demo:
  hojas = hojas_demo()
else:
  hojas = cargar_datos(archivo)
df = hojas["WishList"]
perfil = hojas["Perfil"]

if SOLO_LECTURA:
  tab_articulos, tab_perfil, tab_analisis, tab_dashboard = st.tabs(
    ["Artículos", "Perfil financiero", "Análisis", "Dashboard"]
  )
  tab_editar = None
else:
  tab_articulos, tab_editar, tab_perfil, tab_analisis, tab_dashboard = st.tabs(
    ["Artículos", "Editar lista", "Perfil financiero", "Análisis", "Dashboard"]
  )

with tab_articulos:
  if not SOLO_LECTURA:
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

if not SOLO_LECTURA:
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

  if not SOLO_LECTURA:
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

  st.dataframe(
    tabla_para_mostrar(analisis_filtrado, COLUMNAS_ANALISIS),
    width="stretch", hide_index=True, column_config=CONFIG_DINERO,
  )

with tab_dashboard:
  if not perfil_actual.completo:
    st.info("Completa tu perfil financiero para ver el dashboard.")
  else:
    st.caption("Mismo contenido que las páginas «Dashboard» y «Plan de compras» del reporte de Power BI (WishList.pbip).")
    sub_resumen, sub_plan, sub_presupuesto = st.tabs(["Resumen", "Plan de compras", "Presupuesto acumulado"])
    with sub_resumen:
      pagina_resumen(analisis, perfil_actual)
    with sub_plan:
      pagina_plan_de_compras(analisis, perfil_actual)
    with sub_presupuesto:
      st.plotly_chart(grafico_plan_de_compras(analisis, perfil_actual), width="stretch")

# Descarga generada en memoria: usa los datos de esta ejecución (ya con lo guardado) sin leer el disco.
# Va al final del script para ver el df y el perfil más recientes.
if not SOLO_LECTURA:
  with st.sidebar:
    st.divider()
    st.download_button(
      label="📥 Descargar Excel de ejemplo" if usar_demo else "📥 Descargar Excel actualizado",
      data=excel_en_bytes(agregar_analisis({**hojas, "WishList": df, "Perfil": perfil})),
      file_name="WishList_ejemplo.xlsx" if usar_demo else archivo.name,
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
