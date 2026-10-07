# ROADMAP — WishList: sistema para priorizar compras

Objetivo: registrar artículos que quiero comprar, calcular si conviene comprarlos (regla 50/30/20, fondo de emergencia, tiempo de ahorro) y verlo en dashboards, mientras aprendo Python, pandas, Streamlit, Excel y Power BI.

Última actualización: después de migrar el guardado a `guardar_excel()` (Excel como Tabla, sin duplicados).

## Cómo leer este documento

- `[x]` = implementado en el código.
- `[ ]` = pendiente.
- Las casillas de **Verificación** solo se marcan después de correr la app y comprobar el resultado. Que algo esté implementado no significa que ya esté probado.

## Cómo trabajamos (modo tutor)

- Desde la Fase 1, Claude construye el sistema paso por paso y explica cada cambio (qué hace, qué sintaxis usa y por qué). Yo leo, pregunto y practico.
- Para practicar análisis de datos, en cada fase Claude deja un ejercicio propio en Excel, pandas o Power BI para que lo haga yo.
- Si quiero volver al modo tutor (pistas en lugar de código), lo pido.
- Claude prueba los cambios (AppTest de Streamlit sobre una copia del Excel) antes de darlos por buenos.
- Cada métrica financiera se implementa tres veces: Excel, pandas y Power BI (DAX). Comparar las tres es parte del aprendizaje.

Cómo correr la app (desde la carpeta del proyecto):

```
streamlit run WishList.py
```

## Decisiones tomadas

- **Costo (en revisión).** Hoy el formulario rechaza costo 0 y los negativos los impide el campo (`min_value=0.`). Pero 12 de los 17 artículos actuales tienen costo 0 o vacío (aún sin cotizar), así que hay que decidir cómo registrar un artículo sin precio. Ver Fase 1.
- **`WishList.xlsx` es un archivo gestionado por la app.** Se reescribe completo en cada guardado. Los datos de las celdas se conservan (también las filas escritas a mano en Excel), pero se pierden hojas extra, fórmulas, gráficos, tablas dinámicas y formato propio. El análisis en Excel y Power BI va en otro libro que se conecta a este.
- **La Tabla de Excel (`TablaWishList`) se recrea en cada guardado** dentro de `guardar_excel()`. Como cada guardado crea el libro desde cero, no puede quedar una tabla duplicada.
- **La Tabla no es obligatoria para que la app funcione.** pandas lee igual un rango que una Tabla. Se mantiene porque ayuda en Excel (referencias estructuradas, ampliación automática) y en Power BI (aparece como entidad con nombre). Si diera problemas, se quita el bloque `Table` de `guardar_excel()` sin afectar el resto.
- **El Excel central es `TablaWishList.xlsx`** (variable `archivo` en `WishList.py`). Tiene las hojas `WishList` y `Perfil`, y la app guarda ambas en cada guardado. `WishList.xlsx` queda como respaldo hasta que todo funcione y después se archiva.
- **Sin CSS ni HTML propios.** Streamlit genera la interfaz. Se borraron `styles.css` y `WishList.html`.
- **Indentación:** una sola en todo el archivo (hoy 2 espacios). Mezclar niveles causó los errores de la Fase 0.

---

## Fase 0 — Arreglar la base (WishList.py)

Concepto clave: Streamlit vuelve a ejecutar el script completo en cada interacción. `submit_button` es `True` solo en la ejecución que sigue al clic.

Código:
- [x] Imports limpios: sin `os` ni `openpyxl as op`; solo se importa lo que se usa.
- [ ] Corregir el comentario de `cargar_datos`: dice "cargar los datos en el archivo excel" y la función los carga desde el archivo.
- [x] Corregir el typo "orgnizar" del título y subtítulo.
- [ ] Cambiar "inversiones" en el subtítulo por algo que describa un gasto planeado.
- [x] `st.number_input` con `min_value` para que no acepte negativos.
- [x] Validación dentro de `if submit_button` que bloquea el guardado (lista `errores`: artículo vacío y costo menor o igual a 0).
- [x] `pd.concat(..., ignore_index=True)`.
- [x] `try/except PermissionError` alrededor del guardado, con `st.error` claro. `df` solo se actualiza si el guardado salió bien (`df_actualizado`).
- [x] Ruta del archivo con `Path(__file__).parent`.
- [x] Guardado en una sola función `guardar_excel()` con `pd.ExcelWriter`: escribe los datos y agrega la Tabla en la misma operación.
- [x] Rango de la Tabla calculado con datos (`A1:E{filas+1}`), sin valores fijos.
- [x] Tabla sin duplicados (libro nuevo en cada guardado, un solo `add_table`).
- [x] Borrar `styles.css` y `WishList.html` vacíos.
- [x] `olympic.py` ya no está en esta carpeta, así que no aplica aquí. Si lo conservo en otra, corregir ahí la indentación de `register_participant`.
- [x] Evitar artículos duplicados (compara el nombre sin importar mayúsculas ni espacios y suma un mensaje a `errores`). Probado con AppTest.
- [x] Subtítulo sin la palabra "inversiones".
- [x] Aviso de deprecación de `use_container_width`: reemplazado por `width="stretch"`.
- [ ] `layout="wide"`.
- [ ] Mejora de UX: `clear_on_submit=True` borra lo escrito aunque haya errores de validación. Pensar cómo evitarlo.

Limpieza de los datos actuales (detectada al revisar el Excel):
- [ ] Artículo "Mando": el nombre empieza con un salto de línea y un espacio. Corregirlo en Excel. Los artículos nuevos ya se guardan con `.strip()`.
- [ ] Completar Tipo y Estado en "Reloj Digital", "Taza Sublimada" y "Power bank" (están vacíos porque se escribieron a mano en Excel).
- [ ] Revisar los costos de prueba (Suscripción y Mando en 2.0, Pantalones en 10.0) y poner los reales.

Verificación (marcar solo después de probar):
- [x] Revisar el `WishList.xlsx` actual: 17 artículos, sin filas duplicadas, columnas con los nombres correctos (`Articulo`, `Tipo`, `Costo Estimado`, `Estado`, `Notas`) y datos legibles. Todavía es un rango plano (`A1:E18`, sin tabla): pasa a Tabla en el primer guardado desde la app.
- [ ] Guardar un artículo normal: mensaje verde y fila en la vista previa.
- [ ] Guardar con costo 0: error claro, no guarda.
- [ ] Guardar con nombre vacío: error claro, no guarda.
- [ ] Guardar con el Excel abierto: error claro, sin crash, sin fila fantasma en la vista previa.
- [ ] Hacer una copia de `WishList.xlsx` antes de probar. La app lo reescribe completo.
- [ ] Guardar 1 artículo con costo mayor que 0 sobre el archivo actual (17 artículos): una sola tabla `TablaWishList` con rango `A1:E19`, sin aviso de reparación al abrir el Excel.
- [ ] Guardar 2 artículos más: el rango sube a `A1:E21` y sigue habiendo una sola tabla.
- [ ] Recargar la página 5 veces sin guardar: la fecha de modificación del archivo no cambia.
- [ ] Guardar un artículo duplicado: mensaje claro (cuando exista el chequeo).

## Fase 1 — Modelo de datos

Concepto clave: sin ingreso no hay 50/30/20. El modelo de datos define qué análisis son posibles.

- [x] Estrategia de guardado: `guardar_excel(hojas, ruta)` recibe un diccionario `{hoja: DataFrame}` y escribe todas las hojas en el mismo `ExcelWriter`. `cargar_datos()` lee todas con `sheet_name=None`. (Implementado, falta verificar guardando un artículo y comprobando que `Perfil` sigue ahí.)
- [x] Una Tabla por hoja con nombre único en todo el libro (`TablaWishList`, `TablaPerfil`) mediante `agregar_tabla()`. Una hoja sin filas de datos queda como rango.
- [x] Artículo sin precio: el costo es opcional. Vacío = "por cotizar", nunca 0 (el formulario rechaza 0). El análisis debe excluir o marcar los artículos sin costo, porque dividen entre 0 o dan NaN. (Decisión tomada por Claude; se puede cambiar.)
- [x] Columna `Frecuencia` (Único / Mensual / Anual) para suscripciones. Los costos que ya existían como 0 siguen en 0 hasta que los edite (ver limpieza de datos).
- [x] Columnas nuevas en `WishList`: `Frecuencia`, `Urgencia` (1–5), `Valor` (1–5) y `Fecha de alta`. Los artículos antiguos reciben valores por defecto (Único, 3, 3, fecha vacía).
- [x] Tipo vacío pasa a "Sin clasificar" y Estado vacío a "Pendiente" al cargar. (Decisión tomada por Claude.)
- [x] Código dividido: `datos_excel.py` (leer, limpiar, guardar; sin Streamlit) y `WishList.py` (interfaz). Tests en `test_datos_excel.py` (8 pasan; correr con `python -m pytest`).
- [x] Normalizar al cargar: `normalizar_wishlist()` aplica `.str.strip()` a `Articulo`, `Tipo` y `Estado` (implementado, falta verificar con `Deseo ` y similares).
- [ ] Decidir un valor por defecto o marca "Incompleto" para Tipo y Estado vacíos (hoy `read_excel` los trae como NaN).
- [x] Cabeceras de `Perfil` sin espacios sobrantes (`normalizar_perfil`) y `COLUMNAS_PERFIL` alineada con las del Excel. La hoja tiene 0 filas por ahora, así que su Tabla aparece al cargar la primera.
- [x] Hoja `Perfil` creada en `TablaWishList.xlsx` con las columnas del plan: ingreso neto mensual, gastos fijos (necesidades), deseos ya gastados este mes, ahorro actual, meses de fondo de emergencia objetivo.
- [x] Formulario en la app (pestaña "Perfil financiero") para editar el perfil y guardarlo en la hoja `Perfil`. Exige ingreso mayor que cero. Probado con AppTest.
- [ ] Ampliar hoja `WishList`: ID, Categoría, Prioridad/Urgencia (1–5), Valor percibido (1–5), Usos esperados, Fecha de alta, Fecha de compra, Costo real, Link.
- [ ] Definir qué columnas son entrada (las escribo yo) y cuáles son calculadas (no se guardan, se calculan al cargar).
- [ ] Tipos de dato correctos al cargar (fechas como fecha, costos como número).
- [ ] Manejar el caso de un Excel antiguo sin las columnas nuevas (migración simple).

Verificación:
- [ ] Puedo abrir el Excel y entender cada columna sin mirar el código.

## Fase 2 — Lógica financiera (separada de la interfaz)

Concepto clave: funciones puras que reciben datos y devuelven números. Se prueban sin abrir Streamlit.

- [x] Crear `finanzas.py` (funciones puras, sin Streamlit; usa un `Perfil` inmutable).
- [x] `presupuesto_503020(ingreso)`.
- [x] `deseos_disponibles(perfil)` (30% menos lo ya gastado, nunca negativo) y `margen_necesidades(perfil)` (50% menos gastos fijos).
- [x] `porcentaje_del_ingreso(costos, ingreso)`.
- [x] `meses_de_espera(...)`: los artículos compiten por el mismo presupuesto, ordenados por puntaje, con costo acumulado. Sin presupuesto devuelve infinito en vez de dividir entre cero.
- [x] `fecha_estimada(meses, hoy)`.
- [x] `impacto_en_fondo(...)`, `meses_fondo_cubiertos(...)` y `fondo_completo(...)` (usa los meses objetivo del perfil; 3 si está en 0).
- [ ] Función: costo por uso (costo / usos esperados). Falta la columna "Usos esperados" (Fase 1).
- [x] `puntaje_prioridad(...)`: pesos justificados abajo en "Reglas de decisión".
- [x] `decidir(...)`: semáforo con reglas explícitas y un motivo en texto. Se usó una función con reglas en orden en lugar de `np.select`, porque el motivo cambia con cada regla y es más fácil de leer y probar. Queda como ejercicio reescribirlo con `np.select`.
- [x] Reglas del semáforo documentadas en la sección "Reglas de decisión".
- [x] `analizar_wishlist(wishlist, perfil)` devuelve una copia con las columnas calculadas.
- [x] Tests con `pytest` (`test_finanzas.py`, 20 tests): casos normales, sin presupuesto, costo vacío o 0, fondo incompleto, sin perfil y que la tabla original no se modifique.
- [x] Pestaña "Análisis" en la app con las métricas 50/30/20, el estado del fondo y la tabla con semáforo.

Verificación:
- [x] Con números inventados (ingreso 1000, fijos 400, deseos gastados 100, ahorro 1200), los tests comprueban a mano los resultados: deseos de 150 y 300 dan meses 1 y 3; una necesidad de 250 da 3 meses.
- [ ] Probar la pestaña Análisis con mi perfil real y revisar que el semáforo tenga sentido.

## Fase 3 — Interfaz en Streamlit

- [ ] Organizar con `st.tabs`: Agregar · Lista · Análisis · Dashboard.
- [ ] Lista editable con `st.data_editor` (cambiar estado, editar costo, borrar).
- [ ] Guardar los cambios del editor con `guardar_excel()` y la misma protección de errores de la Fase 0.
- [ ] Mostrar la tabla con columnas calculadas (meses, % ingreso, score, semáforo).
- [ ] Filtros: estado, tipo, categoría.
- [ ] Botón de descarga que genere el Excel en memoria (`BytesIO`) en lugar de leer el archivo del disco.
- [ ] Estado de sesión (`st.session_state`) solo donde haga falta; anotar por qué.
- [ ] Revisar `@st.cache_data`: ¿conviene aquí? (el archivo cambia; entender cuándo se invalida).
- [ ] Hacer el guardado más seguro: escribir a un archivo temporal y reemplazar el original solo si todo salió bien (hoy un fallo a mitad de la escritura puede dejar el archivo vacío).

## Fase 4 — Dashboard dentro de la app

- [x] Pestaña "Dashboard" con KPIs (`st.metric`): total pendiente con precio, % de un mes de ingreso, plazo para cumplir la lista y artículos por cotizar, más el conteo por semáforo.
- [x] Gráfico 50/30/20: barras agrupadas, meta contra real (comparar dos valores por categoría).
- [x] Gráfico de ranking por puntaje: barras horizontales coloreadas por semáforo (ordenar y comparar).
- [x] Gráfico de plan de compras: presupuesto acumulado (línea) contra costo acumulado de cada compra (puntos). Un punto bajo la línea significa que ya se puede pagar. Es una proyección acumulada en el tiempo.
- [x] Colores con significado: verde, amarillo y rojo igual que el semáforo, gris para lo que falta (cotizar o clasificar). Definidos en `COLORES_SEMAFORO`.
- [x] Modo ejemplo (interruptor en la barra lateral): `datos_demo.py` carga datos inventados sin leer ni modificar tu Excel.
- [x] Módulo `graficos.py` (figuras de Plotly sin Streamlit) con 6 tests en `test_graficos.py`.
- [x] Corrección detectada con el modo ejemplo: un gasto enorme (fuera de alcance, más de 6 meses él solo) ya no bloquea la fila de los gastos pequeños.
- [ ] Revisar el dashboard con mis datos reales cuando tenga perfil y precios.
- [ ] Ejercicio: agregar un gráfico de composición (por ejemplo, costo pendiente por tipo) y justificar por qué se elige ese tipo de gráfico.

## Fase 5 — Excel y Power BI

Excel (en un libro aparte que se conecte a `WishList.xlsx`, no dentro de él):
- [x] Convertir los datos en Tabla de Excel: ya lo hace `guardar_excel()` (`TablaWishList`).
- [ ] Reproducir 3 métricas con fórmulas (`SUMIFS`, `IF`, `XLOOKUP` o `INDEX/MATCH`) usando referencias estructuradas de la Tabla.
- [ ] Formato condicional para el semáforo.
- [ ] Una tabla dinámica por tipo y por estado.

Power BI:
- [ ] Conectar al `.xlsx` y elegir la Tabla `TablaWishList` (y `TablaPerfil` cuando exista) en el navegador.
- [ ] Tipos de dato y tabla de calendario básica.
- [ ] Medidas DAX: total pendiente, % del ingreso, meses para pagar, comprado vs pendiente.
- [ ] Reporte de 1 página: KPIs, barras 50/30/20, ranking, segmentadores.
- [ ] Comparar los resultados de pandas, Excel y DAX para una misma métrica. Si no coinciden, encontrar por qué.

## Calidad y hábitos (transversal)

- [ ] `requirements.txt` con las librerías y versiones usadas (`streamlit`, `pandas`, `openpyxl`).
- [x] Repositorio git inicializado.
- [ ] Hacer commits pequeños por fase (`feat:`, `fix:`, `docs:`).
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

## Registro de dudas y aprendizajes

| Fecha | Duda o error | Qué aprendí |
|-------|--------------|-------------|
|       |              |             |
