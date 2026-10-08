# ROADMAP — WishList: sistema para priorizar compras

Objetivo: registrar artículos que quiero comprar, calcular si conviene comprarlos (regla 50/30/20, fondo de emergencia, tiempo de ahorro) y verlo en dashboards, mientras aprendo Python, pandas, Streamlit, Excel y Power BI.

Última actualización: 2026-10-08, después de restaurar `WishList.py` y este archivo (habían vuelto a una versión vieja).

## Cómo leer este documento

- `[x]` = hecho (implementado, o marcado por mí).
- `[ ]` = pendiente.
- Las casillas de **Verificación** solo se marcan después de correr la app y comprobar el resultado. Que algo esté implementado no significa que ya esté probado.

## Cómo trabajamos

- Desde la Fase 1, Claude construye el sistema paso por paso y explica cada cambio (qué hace, qué sintaxis usa y por qué). Yo leo, pregunto y practico.
- Para practicar análisis de datos, cada fase deja ejercicios en `docs/MANUAL_EJERCICIOS.md` (Python, Excel y Power BI), con respuestas en `docs/SOLUCIONES.md`.
- Si quiero volver al modo tutor (pistas en lugar de código), lo pido.
- Claude prueba los cambios (pytest y AppTest de Streamlit sobre una copia del Excel) antes de darlos por buenos, y dice qué no pudo verificar (por ejemplo, Power BI Desktop).
- Cada métrica financiera se implementa tres veces: Excel, pandas y Power BI (DAX). Comparar las tres es parte del aprendizaje.

Cómo correr la app (desde la carpeta del proyecto):

```
streamlit run WishList.py
python -m pytest
```

## Decisiones tomadas

- **Costo vacío = por cotizar, nunca 0.** El formulario rechaza 0, y los negativos los impide el campo (`min_value=0.`).
- **El Excel central es `TablaWishList.xlsx`** (variable `archivo` en `WishList.py`). Tiene las hojas `WishList`, `Perfil` y `Analisis`. `WishList.xlsx` (de la raíz) queda como respaldo.
- **El Excel central es un archivo gestionado por la app.** Se reescribe completo en cada guardado. Los datos de las celdas se conservan (también las filas escritas a mano), pero se pierden hojas extra, fórmulas, gráficos, tablas dinámicas y formato propio. El análisis en Excel y Power BI va en otro libro que se conecta a este.
- **La hoja `Analisis` la calcula la app** en cada guardado (`agregar_analisis`). Excel y Power BI leen de ahí el mismo semáforo que muestra la app.
- **Cada hoja con datos es una Tabla de Excel** (`TablaWishList`, `TablaPerfil`, `TablaAnalisis`), recreada en cada guardado. Una hoja sin filas queda como rango.
- **Tipo vacío pasa a "Sin clasificar" y Estado vacío a "Pendiente"** al cargar (decisión de Claude, se puede cambiar).
- **Un gasto fuera de alcance** (que, solo, tardaría más de 6 meses) no bloquea la fila de espera de los gastos pequeños.
- **Sin CSS ni HTML propios.** Streamlit genera la interfaz.
- **Indentación:** una sola en todo el archivo (hoy 2 espacios). Mezclar niveles causó errores en la Fase 0.
- **Power BI:** el proyecto es `WishList.pbip` (carpetas `WishList.Report` y `WishList.SemanticModel`). Hoy lee `powerbi/WishList_demo.xlsx`. Un `.pbip` no se crea desde cero: lo guarda Power BI Desktop. Claude no puede ver Desktop, así que la verificación visual es mía.

---

## Fase 0 — Arreglar la base (WishList.py)

Concepto clave: Streamlit vuelve a ejecutar el script completo en cada interacción. `submit_button` es `True` solo en la ejecución que sigue al clic.

- [x] Quitar `import openpyxl as op` si no se usa directamente (pandas lo usa solo como motor).
- [x] Corregir el comentario de `cargar_datos` (carga datos, no los guarda).
- [x] Corregir typos del título y subtítulo ("orgnizar"). Cambiar "inversión" por algo que describa un gasto planeado.
- [x] `st.number_input`: agregar `min_value` para que no acepte negativos.
- [x] Mover la validación del costo dentro de `if submit_button` y que realmente bloquee el guardado.
- [x] `pd.concat(..., ignore_index=True)`.
- [x] Rodear `to_excel` con `try/except PermissionError` y mostrar `st.error` claro. `df` solo se actualiza si el guardado salió bien.
- [x] Ruta del archivo con `Path(__file__).parent` en lugar de ruta relativa.
- [x] Evitar artículos duplicados (compara el nombre sin importar mayúsculas ni espacios).
- [x] `layout="wide"` y revisar avisos de deprecación de `use_container_width`. El aviso de deprecación está resuelto (`width="stretch"`). Nota: la app sigue con `layout="centered"`; decidir si pasarla a "wide".
- [x] Borrar `styles.css` y `WishList.html` vacíos.
- [x] Arreglar la indentación de `olympic.py` (ya no está en esta carpeta).
- [ ] Mejora de UX: `clear_on_submit=True` borra lo escrito aunque haya errores de validación. Pensar cómo evitarlo.

Limpieza de datos reales:
- [ ] Revisar los costos de prueba (Suscripción y Mando en 2.0, Pantalones en 10.0) y poner los reales.
- [ ] Cotizar los artículos sin precio (12 de 18 en el último chequeo).

Verificación (marcar solo después de probar yo mismo en la app). Claude ya probó los casos con AppTest sobre una copia del Excel:
- [x] Revisar el `WishList.xlsx` original: 17 artículos, sin duplicados, columnas correctas.
- [ ] Hacer una copia de `TablaWishList.xlsx` antes de probar. La app lo reescribe completo.
- [ ] Guardar un artículo normal: mensaje verde y fila en la vista previa.
- [ ] Guardar con costo 0: error claro, no guarda.
- [ ] Guardar con nombre vacío: error claro, no guarda.
- [ ] Guardar un artículo duplicado: error claro, no guarda.
- [ ] Guardar con el Excel abierto: error claro, sin crash y sin fila fantasma en la vista previa.
- [ ] Recargar la página 5 veces sin guardar: la fecha de modificación del archivo no cambia.

## Fase 1 — Modelo de datos

Concepto clave: sin ingreso no hay 50/30/20. El modelo de datos define qué análisis son posibles.

- [x] Estrategia de guardado con varias hojas: `guardar_excel(hojas, ruta)` escribe todas las hojas en el mismo `ExcelWriter`, y `cargar_datos()` las lee con `sheet_name=None`.
- [x] Una Tabla por hoja con nombre único (`agregar_tabla()`).
- [x] Artículo sin precio: el costo es opcional (vacío = "por cotizar").
- [x] Columna `Frecuencia` (Único / Mensual / Anual) para suscripciones.
- [x] Columnas nuevas en `WishList`: `Frecuencia`, `Urgencia` (1–5), `Valor` (1–5) y `Fecha de alta`. Los artículos antiguos reciben valores por defecto.
- [x] Normalizar al cargar: `normalizar_wishlist()` quita espacios de `Articulo`, `Tipo`, `Estado` y `Frecuencia`; `normalizar_perfil()` limpia las cabeceras.
- [x] Hoja `Perfil` creada en el Excel con las columnas del plan.
- [x] Formulario en la app (pestaña "Perfil financiero") para editar el perfil y guardarlo. Exige ingreso mayor que cero.
- [x] Código dividido: `datos_excel.py` (leer, limpiar, guardar), `finanzas.py` (lógica), `graficos.py`, `datos_demo.py` y `WishList.py` (interfaz). Tests en `test_*.py`.
- [x] Manejar el caso de un Excel antiguo sin las columnas nuevas (`reindex` en `normalizar_wishlist`).
- [ ] **Completar mi hoja `Perfil` real** (hoy tiene 0 filas, así que el análisis y el dashboard piden completar el perfil).
- [ ] Ampliar hoja `WishList` con: ID, Categoría, Usos esperados, Fecha de compra, Costo real, Link.
- [ ] Decidir qué columnas son entrada (las escribo yo) y cuáles son calculadas.
- [ ] Tipos de dato correctos al cargar (fechas como fecha, costos como número): revisar fechas.

Verificación:
- [ ] Puedo abrir el Excel y entender cada columna sin mirar el código.

## Fase 2 — Lógica financiera (separada de la interfaz)

Concepto clave: funciones puras que reciben datos y devuelven números. Se prueban sin abrir Streamlit.

- [x] `finanzas.py` con un `Perfil` inmutable (`@dataclass(frozen=True)`).
- [x] `presupuesto_503020`, `deseos_disponibles`, `margen_necesidades`.
- [x] `porcentaje_del_ingreso`, `impacto_en_fondo`, `compromiso_mensual`.
- [x] `meses_de_espera`: los artículos compiten por el mismo presupuesto, ordenados por puntaje, con costo acumulado. Sin presupuesto devuelve infinito en vez de dividir entre cero. Los gastos fuera de alcance no entran en la fila.
- [x] `fecha_estimada`, `meses_fondo_cubiertos`, `fondo_completo`.
- [ ] Función: costo por uso (costo / usos esperados). Falta la columna "Usos esperados" (Fase 1).
- [x] `puntaje_prioridad`: pesos justificados abajo en "Reglas de decisión".
- [x] `decidir`: semáforo con reglas explícitas y un motivo en texto. Queda como ejercicio reescribirlo con `np.select`.
- [x] `analizar_wishlist` y `agregar_analisis` (la hoja `Analisis`).
- [x] Tests con `pytest` (37 pasan): casos normales, sin presupuesto, costo vacío o 0, fondo incompleto, sin perfil, y que la tabla original no se modifique.
- [x] Pestaña "Análisis" en la app.

Verificación:
- [x] Con números inventados (ingreso 1000, fijos 400, deseos gastados 100, ahorro 1200), los tests comprueban a mano los resultados.
- [ ] Probar la pestaña Análisis con mi perfil real y revisar que el semáforo tenga sentido.

## Fase 3 — Interfaz en Streamlit

- [x] Pestañas: Artículos, Perfil financiero, Análisis y Dashboard.
- [x] Interruptor "Ver con datos de ejemplo" en la barra lateral (no lee ni modifica el Excel real).
- [x] Pestaña "Editar lista" con `st.data_editor`: cambiar precios, estados y tipos, agregar y borrar filas. Nada se guarda hasta pulsar "Guardar cambios".
- [x] Guardar los cambios del editor con la misma protección de errores. La lógica está en `datos_excel.py` (`preparar_edicion`, `validar_wishlist`, `resumir_cambios`) y tiene tests (45 en total). Probado en el navegador sobre una copia: editar un costo y borrar una fila actualizan `WishList`, `Analisis` y los rangos de las Tablas.
- [x] Al guardar desde el editor, los costos en 0 pasan a vacío ("por cotizar") y la app avisa cuántos fueron.
- [ ] Probar en el navegador agregar una fila nueva desde el editor (solo está probado con tests).
- [ ] Filtros: estado, tipo, semáforo.
- [ ] Botón de descarga que genere el Excel en memoria (`BytesIO`) en lugar de leer el archivo del disco.
- [ ] Estado de sesión (`st.session_state`) solo donde haga falta; anotar por qué.
- [ ] Revisar `@st.cache_data`: ¿conviene aquí? (el archivo cambia; entender cuándo se invalida).
- [ ] Guardado más seguro: escribir a un archivo temporal y reemplazar el original solo si todo salió bien (hoy un fallo a mitad puede dejar el archivo vacío).

## Fase 4 — Dashboard dentro de la app

- [x] Pestaña "Dashboard" con KPIs: total pendiente con precio, % de un mes de ingreso, plazo para cumplir la lista, artículos por cotizar, y el conteo por semáforo.
- [x] Gráfico 50/30/20: barras agrupadas, meta contra real.
- [x] Gráfico de ranking por puntaje: barras horizontales coloreadas por semáforo.
- [x] Gráfico de plan de compras: presupuesto acumulado (línea) contra costo acumulado de cada compra (puntos).
- [x] Colores con significado (`COLORES_SEMAFORO`): verde, amarillo y rojo igual que el semáforo, gris para lo que falta.
- [x] Módulo `graficos.py` (Plotly, sin Streamlit) con tests en `test_graficos.py`.
- [ ] Revisar el dashboard con mis datos reales cuando tenga perfil y precios.
- [ ] Ejercicio: agregar un gráfico de composición (por ejemplo, costo pendiente por tipo) y justificar por qué se elige ese tipo de gráfico.

## Fase 5 — Excel y Power BI

Material preparado (en `docs/` y `powerbi/`):
- [x] `docs/GUIA_DEL_SISTEMA.md`, `docs/MANUAL_EJERCICIOS.md` y `docs/SOLUCIONES.md`.
- [x] `powerbi/WishList_demo.xlsx` (regenerable con `python exportar_demo.py`), `powerbi/medidas.dax`, `powerbi/consultas_power_query.m` y `powerbi/GUIA_POWER_BI.md`.
- [x] La app guarda la hoja `Analisis` (con `TablaAnalisis`) en cada guardado.

Excel (en un libro aparte que se conecte a `TablaWishList.xlsx`, no dentro de él). Ejercicios E1 a E10:
- [x] Convertir los datos en Tabla de Excel: lo hace `guardar_excel()`.
- [ ] Reproducir 3 métricas con fórmulas (`SUMAR.SI`, `SI`, `BUSCARX`) usando referencias estructuradas (E2 a E5).
- [ ] Formato condicional para el semáforo (E6).
- [ ] Una tabla dinámica por semáforo y por tipo (E7). Ya hice una por Estado y Tipo.
- [ ] Power Query en Excel (E10).

Power BI (siguiendo `powerbi/GUIA_POWER_BI.md`). Ejercicios B1 a B8:
- [x] Conectar al `.xlsx` y cargar `TablaAnalisis` y `TablaPerfil`.
- [x] Medidas DAX: total pendiente, % de un mes de ingreso, por cotizar, meta contra real, color del semáforo.
- [x] Reporte de una página ("Dashboard") armado a mano: tarjetas, costo por decisión, ranking, meta contra real, tabla con semáforo y segmentadores.
- [x] Guardado como `WishList.pbip`.
- [x] Claude agregó la página 2 "Plan de compras" (`pg02PlanCompras`) con medidas nuevas `Comprar Ya`, `Esperar` y `No Conviene`. **Falta abrirla y verificar visualmente.**
- [ ] Comparar los resultados de pandas, Excel y DAX para una misma métrica. Si no coinciden, encontrar por qué.
- [ ] Cambiar el origen de datos al Excel real (`TablaWishList.xlsx`), después de completar el perfil y guardar un artículo.

Ejercicios de Python (P1 a P13), reto final y preguntas de repaso: ver `docs/MANUAL_EJERCICIOS.md`.

## Calidad y hábitos (transversal)

- [x] `requirements.txt` con las librerías (`streamlit`, `pandas`, `openpyxl`, `plotly`, `pytest`). Falta fijar las versiones.
- [x] Repositorio git inicializado y con commits.
- [ ] Hacer commits pequeños por fase (`feat:`, `fix:`, `docs:`). **Hacer commit antes de cada `git pull`.**
- [ ] Funciones cortas, con nombres claros y type hints.
- [ ] Antes de cada fase: escribir con mis palabras qué pregunta del negocio responde.
- [ ] Usar Pylance (subrayados en VS Code) o `ruff check` para detectar nombres no definidos antes de correr.

## Reglas de decisión (definidas en `finanzas.py`)

Presupuesto mensual: deseos = 30% del ingreso menos lo ya gastado en deseos. Necesidades = 50% del ingreso menos los gastos fijos. Fondo completo = ahorro actual / gastos fijos mayor o igual que los meses objetivo del perfil (3 si no hay objetivo).

Meses de espera: dentro de cada tipo, los artículos pendientes con precio se ordenan por puntaje y se acumula el costo. Meses = costo acumulado / presupuesto disponible, redondeado hacia arriba. Mes 1 es este mes. Excepción: un artículo que, solo, tardaría más de 6 meses queda fuera de alcance, no entra en la fila y se evalúa por separado (así un gasto enorme no retrasa a los pequeños).

El semáforo evalúa estas reglas en orden y se queda con la primera que se cumple:
1. **Comprado:** el estado es Comprado.
2. **Por cotizar:** el costo está vacío o es 0.
3. **Clasificar:** el tipo no es Deseo ni Necesidad.
4. **Falta perfil:** el ingreso mensual es 0.
5. **No conviene:** no queda presupuesto mensual para ese tipo de gasto.
6. **Esperar:** es un deseo y el fondo de emergencia no está completo.
7. **Comprar ya:** cabe en este mes (meses menor o igual que 1).
8. **Esperar:** alcanza en 6 meses o menos.
9. **No conviene:** tardaría más de 6 meses.

Pesos del puntaje de prioridad (0 a 100): urgencia 45%, valor percibido 30%, es una necesidad 25%. La urgencia pesa más porque un artículo que ya hace falta debe ir antes. El costo no entra en el puntaje: el puntaje mide importancia y el costo lo resuelve el semáforo. Los pesos y el máximo de 6 meses son constantes en `finanzas.py`, fáciles de cambiar.

Límite conocido: las compras a plazos o suscripciones ya activas no restan del presupuesto futuro. `Compromiso Mensual` solo informa el gasto recurrente.

## Errores ya resueltos (referencia)

- `TypeError: 'str' object is not callable`: una variable llamada `Path` guardaba un string y después se llamó como función.
- `AttributeError` con `open.load_workbook`: `open` es la función de Python, no el módulo `openpyxl`.
- `NameError: name 'style' is not defined`: variable creada solo en una rama y usada fuera.
- `NameError` por indentación: un `else` que cubría una sola línea dejó el resto del código fuera del bloque.
- `KeyError` por nombre de columna: `"Artículo"` con tilde en un lugar y `"Articulo"` sin tilde en otro.
- Tabla que vuelve a ser rango: `to_excel` reescribe el archivo y borra la Tabla; hay que volver a crearla en cada guardado.
- Tabla duplicada: dos `add_table` con el mismo `displayName` en el mismo libro hacen que Excel pida reparar el archivo.
- Fila guardada dos veces: guardar con pandas y además escribir la fila a mano con `openpyxl`.
- Un gasto enorme mandaba a "No conviene" a todos los artículos pequeños: se resolvió con la regla de "fuera de alcance".
- Color del semáforo en Power BI: con "Reglas" no funciona sobre una medida que devuelve códigos de color; usar "Valor del campo".

## Registro de dudas y aprendizajes

| Fecha | Duda o error | Qué aprendí |
|-------|--------------|-------------|
| 2026-10-08 | `WishList.py` y `ROADMAP.md` volvieron a una versión vieja después de un `git pull origin main`. | Hacer commit de todo antes de un `pull`, y revisar `git status` y `git diff` después. Los archivos no confirmados pueden pisarse. |
