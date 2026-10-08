# ROADMAP — WishList: sistema para priorizar compras

Objetivo: registrar artículos que quiero comprar, calcular si conviene comprarlos (regla 50/30/20, fondo de emergencia, tiempo de ahorro) y verlo en dashboards, mientras aprendo Python, pandas, Streamlit, Excel y Power BI.

## Cómo trabajamos (modo tutor)

- Yo escribo el código. Claude audita, guía y revisa.
- Si me confundo, pido ayuda en niveles: 1) pista, 2) pregunta guía, 3) ejemplo mínimo de la idea (no mi solución), 4) revisión de mi código.
- Claude no edita `WishList.py` salvo que yo lo pida explícitamente.
- Al terminar cada fase: pego mi código, Claude lo revisa y me dice qué mejorar y por qué.
- Cada métrica financiera se implementa tres veces: Excel, pandas y Power BI (DAX). Comparar las tres es parte del aprendizaje.

Cómo correr la app (desde la carpeta del proyecto):

```
streamlit run WishList.py
```

---

## Fase 0 — Arreglar la base (WishList.py)

Concepto clave: Streamlit vuelve a ejecutar el script completo en cada interacción.

- [X] Quitar `import openpyxl as op` si no se usa directamente (pandas lo usa solo como motor).
- [X] Corregir el comentario de `cargar_datos` (carga datos, no los guarda).
- [X] Corregir typos del título y subtítulo ("orgnizar"). Cambiar "inversión" por algo que describa un gasto planeado.
- [X] `st.number_input`: agregar `min_value` para que no acepte negativos.
- [X] Mover la validación del costo dentro de `if submit_button` y que realmente bloquee el guardado (decidir: ¿0 es válido?).
- [X]`pd.concat(..., ignore_index=True)`. Entender por qué.
- [X] Rodear `to_excel` con `try/except PermissionError` y mostrar `st.error` claro (pasa si el Excel está abierto u OneDrive lo bloquea).
- [X]Ruta del archivo con `Path(__file__).parent` en lugar de ruta relativa.
- [X] Evitar artículos duplicados (comparar nombre sin importar mayúsculas/espacios).
- [X] `layout="wide"` y revisar avisos de deprecación de `use_container_width` en la versión instalada de Streamlit.
- [X] Borrar `styles.css` y `WishList.html` vacíos, o conectarlos de verdad (decidir y anotar por qué).
- [X] Arreglar la indentación de `olympic.py` (línea 17: `register_participant` usa 4 espacios y el resto de la clase 3).

Verifico: guardo un artículo, uno con costo 0, uno negativo, uno duplicado y uno con el Excel abierto. Cada caso debe dar un mensaje claro y no romper la app.

## Fase 1 — Modelo de datos

Concepto clave: sin ingreso no hay 50/30/20. El modelo de datos define qué análisis son posibles.

- [X] Definir hoja `Perfil` en el Excel: ingreso neto mensual, gastos fijos (necesidades), deseos ya gastados este mes, ahorro actual, meses de fondo de emergencia objetivo.
- [ ] Formulario o sección en la app para editar el perfil y guardarlo.
- [ ] Ampliar hoja `WishList`: ID, Categoría, Prioridad/Urgencia (1–5), Valor percibido (1–5), Usos esperados, Fecha de alta, Fecha de compra, Costo real, Link.
- [ ] Decidir qué columnas son entrada (las escribo yo) y cuáles son calculadas (no se guardan, se calculan al cargar).
- [ ] Definir tipos de dato correctos al cargar (fechas como fecha, costos como número).
- [ ] Manejar el caso de Excel antiguo sin las columnas nuevas (migración simple).

Verifico: puedo abrir el Excel y entender cada columna sin mirar el código.

## Fase 2 — Lógica financiera (separada de la interfaz)

Concepto clave: funciones puras que reciben datos y devuelven números. Se prueban sin abrir Streamlit.

- [ ] Crear `finanzas.py`.
- [ ] Función: presupuesto 50/30/20 a partir del ingreso (necesidades, deseos, ahorro).
- [ ] Función: presupuesto de deseos disponible este mes (30% menos lo ya gastado).
- [ ] Función: % del ingreso que representa un artículo.
- [ ] Función: meses necesarios para pagarlo con lo que puedo apartar por mes (cuidar división entre cero).
- [ ] Función: fecha estimada de compra.
- [ ] Función: impacto en el fondo de emergencia (costo / ahorro actual) y bandera si el fondo es menor a 3 meses de gastos.
- [ ] Función: costo por uso (costo / usos esperados).
- [ ] Función: score de prioridad (decidir pesos de urgencia, valor y tipo; anotar la justificación).
- [ ] Función: semáforo "Comprar ya / Esperar N meses / No conviene" con reglas explícitas (probar `np.select`).
- [ ] Documentar las reglas del semáforo en este archivo (sección "Reglas de decisión").
- [ ] Tests con `pytest` (`test_finanzas.py`): casos normales, ingreso 0, costo 0, DataFrame vacío.

Verifico: con números inventados, calculo a mano 2 casos y el código da el mismo resultado.

## Fase 3 — Interfaz en Streamlit

- [ ] Organizar con `st.tabs`: Agregar · Lista · Análisis · Dashboard.
- [ ] Lista editable con `st.data_editor` (cambiar estado, editar costo, borrar).
- [ ] Guardar los cambios del editor al Excel con la misma protección de errores de la Fase 0.
- [ ] Mostrar la tabla con columnas calculadas (meses, % ingreso, score, semáforo).
- [ ] Filtros: estado, tipo, categoría.
- [ ] Botón de descarga que genere el Excel en memoria (`BytesIO`) en lugar de leer el archivo del disco.
- [ ] Estado de sesión (`st.session_state`) solo donde haga falta; anotar por qué.
- [ ] Revisar `@st.cache_data`: ¿conviene aquí? (el archivo cambia; entender cuándo invalida).

## Fase 4 — Dashboard dentro de la app

- [ ] KPIs con `st.metric`: ingreso, total en wishlist, % del ingreso, meses totales para cumplir la lista.
- [ ] Gráfico 50/30/20: meta contra real (barras).
- [ ] Gráfico de ranking de artículos por score.
- [ ] Gráfico de línea: proyección de ahorro hasta cada fecha de compra.
- [ ] Elegir bien cada tipo de gráfico y anotar por qué (comparar, evolución, composición).
- [ ] Revisar legibilidad: títulos, etiquetas, colores con significado (rojo/amarillo/verde coherente con el semáforo).

## Fase 5 — Excel y Power BI

Excel:
- [ ] Convertir el rango en Tabla de Excel.
- [ ] Reproducir 3 métricas con fórmulas (`SUMIFS`, `IF`, `XLOOKUP` o `INDEX/MATCH`).
- [ ] Formato condicional para el semáforo.
- [ ] Una tabla dinámica por tipo y por estado.

Power BI:
- [ ] Conectar al `.xlsx` (hojas `WishList` y `Perfil`).
- [ ] Tipos de dato y tabla de calendario básica.
- [ ] Medidas DAX: total pendiente, % del ingreso, meses para pagar, comprado vs pendiente.
- [ ] Reporte de 1 página: KPIs, barras 50/30/20, ranking, segmentadores.
- [ ] Comparar los resultados de pandas, Excel y DAX para una misma métrica. Si no coinciden, encontrar por qué.

## Calidad y hábitos (transversal)

- [ ] `requirements.txt` con las librerías y versiones usadas.
- [ ] Inicializar git y hacer commits pequeños por fase (`feat:`, `fix:`, `docs:`).
- [ ] Funciones cortas, con nombres claros y type hints.
- [ ] Antes de cada fase: escribir con mis palabras qué pregunta del negocio responde.

## Reglas de decisión (se completa en la Fase 2)

- Semáforo "Comprar ya": _pendiente de definir_
- Semáforo "Esperar": _pendiente de definir_
- Semáforo "No conviene": _pendiente de definir_
- Pesos del score: _pendiente de definir_

## Registro de dudas y aprendizajes

| Fecha | Duda o error | Qué aprendí |
|-------|--------------|-------------|
|       |              |             |
