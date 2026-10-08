# Manual de ejercicios: Python, Excel y Power BI con WishList

Cómo usar este manual:
1. Leé primero `GUIA_DEL_SISTEMA.md` (y `powerbi/GUIA_POWER_BI.md` antes de los ejercicios B).
2. Hacé cada ejercicio sin mirar `SOLUCIONES.md`. Antes de calcular, escribí qué resultado esperás.
3. Compará con el "Resultado esperado". Si no coincide, buscá por qué antes de ver la solución.
4. Marcá la casilla cuando lo logres y anotá lo que aprendiste en el ROADMAP (sección "Registro de dudas y aprendizajes").

Datos de práctica: `powerbi/WishList_demo.xlsx` (14 artículos de ejemplo, perfil con ingreso 1500). Los resultados esperados están calculados con ese libro. No edites el original: copialo antes de trabajar en Excel.

Los números de referencia de Python salen de ejecutar el código de `SOLUCIONES.md`. Los de Excel y Power BI se calcularon con pandas y no se ejecutaron en esas herramientas: usalos para comprobar tu resultado.

Para Python, creá una carpeta `practica/` en el proyecto y un archivo por ejercicio, por ejemplo `practica/p01.py`. Plantilla de arranque:

```python
import pandas as pd

df = pd.read_excel("powerbi/WishList_demo.xlsx", sheet_name="Analisis")
```

Corré tus archivos desde la carpeta del proyecto: `python practica/p01.py`.

---

## Nivel 1: Base

### Python y pandas

**P1. Conocer los datos.** [ ]
Cargá la hoja `Analisis`. Mostrá cuántas filas y columnas tiene y los nombres de las columnas.
Pista: `df.shape`, `df.columns`, `df.head()`.
Resultado esperado: 14 filas y 17 columnas.

**P2. Contar por tipo.** [ ]
¿Cuántos artículos son Deseo y cuántos Necesidad? Hacelo de dos formas.
Pista: `groupby(...).size()` y `value_counts()`.
Resultado esperado: Deseo 10, Necesidad 4.

**P3. Filtrar y sumar.** [ ]
¿Cuántos artículos están pendientes y tienen precio, y cuánto suman?
Pista: combiná dos condiciones con `&` y paréntesis: `(df["Estado"] == ...) & df["Costo Estimado"].notna()`.
Resultado esperado: 10 artículos, suma 3847.

**P4. Agrupar con varias métricas.** [ ]
Para cada Estado, calculá cuántos artículos hay, cuántos tienen costo y cuánto suman. ¿Por qué dos conteos dan distinto en Pendiente?
Pista: `groupby("Estado").agg(nombre=("columna", "función"))`. `count` no cuenta los vacíos.
Resultado esperado: Comprado 2 / 2 / 23; Pendiente 12 / 10 / 3847.

**P5. Ordenar y elegir.** [ ]
¿Cuáles son los 3 artículos pendientes con mayor puntaje?
Pista: filtrá por Estado y usá `nlargest(3, "Puntaje")`.
Resultado esperado: Medias 85.0, Mouse 81.2, Zapatos 81.2.

**P6. Valores vacíos.** [ ]
¿Cuántos costos están vacíos y qué porcentaje de la lista es? ¿Qué pasaría con el promedio si esos vacíos fueran 0?
Pista: `isna()`, `.sum()` y `.mean()` sobre una serie booleana.
Resultado esperado: 2 vacíos, 14.3%.

**P7. Costo por semáforo.** [ ]
Sumá el costo de cada categoría del semáforo. ¿Qué parte de tu lista está en "No conviene"?
Resultado esperado: Comprado 23, Comprar ya 340, Esperar 507, No conviene 3000, Por cotizar 0.

### Excel (abrí una copia de `WishList_demo.xlsx`)

**E1. Reconocer las tablas.** [ ]
Hacé clic dentro de los datos de cada hoja. ¿Aparece la pestaña Diseño de tabla? Anotá el nombre y el rango de cada tabla.
Resultado esperado: TablaWishList (A1:I15), TablaPerfil (A1:E2), TablaAnalisis (A1:Q15).

**E2. Suma condicional.** [ ]
En una celda fuera de la tabla, calculá el costo total de los artículos con Estado "Pendiente" usando referencias de tabla.
Pista: `SUMAR.SI` (en inglés `SUMIF`) con `TablaAnalisis[Estado]`.
Resultado esperado: 3847.

**E3. Contar con dos condiciones.** [ ]
¿Cuántos deseos pendientes y cuántas necesidades pendientes hay?
Pista: `CONTAR.SI.CONJUNTO` (`COUNTIFS`).
Resultado esperado: 8 deseos y 4 necesidades.

**E4. Buscar un dato.** [ ]
Dado el nombre "Pedalera" en una celda, mostrá su costo y su semáforo en otras dos.
Pista: `BUSCARX` (`XLOOKUP`).
Resultado esperado: 250 y "Comprar ya".

**E5. Columna calculada.** [ ]
Agregá a `TablaWishList` una columna "Pct ingreso" con costo dividido el ingreso de `TablaPerfil`. ¿Qué muestran los artículos sin precio? ¿Es correcto?
Pista: Excel trata una celda vacía como 0 al dividir. Usá `SI(ESNUMERO(...), ..., "")`.
Resultado esperado: Pedalera 16.7%, Guitarra 200%, y vacío (no 0%) para los que no tienen precio.

**E6. Formato condicional.** [ ]
En la columna Semaforo de `TablaAnalisis`, pintá "Comprar ya" de verde, "Esperar" de amarillo y "No conviene" de rojo.
Pista: Inicio > Formato condicional > Resaltar reglas > Texto que contiene.

**E7. Tabla dinámica.** [ ]
Creá una tabla dinámica con Semaforo en filas y suma de Costo Estimado en valores. Agregá Tipo en columnas.
Resultado esperado (total por semáforo): Comprado 23, Comprar ya 340, Esperar 507, No conviene 3000, Por cotizar vacío o 0.

### Power BI (después de la guía, pasos 1 a 3)

**B1. Conectar y revisar tipos.** [ ]
Cargá `TablaAnalisis` y `TablaPerfil` desde `WishList_demo.xlsx`. Comprobá el tipo de cada columna en Power Query.
Resultado esperado: costos y puntajes decimales, Urgencia y Valor enteros, fechas como fecha.

**B2. Primeras medidas.** [ ]
Creá `Articulos Pendientes`, `Total Pendiente` y `Por Cotizar` (están en `medidas.dax`, pero antes intentá escribirlas vos).
Resultado esperado: 12, 3,847 y 2.

**B3. Tarjetas y barras.** [ ]
Poné `Total Pendiente` y `Por Cotizar` en tarjetas. Hacé un gráfico de barras con Semaforo en el eje y `Costo Total` en valores.
Resultado esperado: las mismas sumas por semáforo que en P7.

**B4. Dividir con seguridad.** [ ]
Creá `% de un Mes de Ingreso` con `DIVIDE`. ¿Por qué `DIVIDE` y no el operador `/`?
Resultado esperado: 256%.

---

## Nivel 2: Lógica

### Python

**P8. Tu primera función y su prueba.** [ ]
Escribí `porcentaje_del_ingreso(costo, ingreso)` que devuelva el porcentaje redondeado a 1 decimal, y NaN si el costo está vacío o el ingreso es 0 o menos. Escribí 3 tests con `pytest` en `practica/test_p08.py`.
Resultados esperados: (250, 1500) da 16.7; (NaN, 1500) da NaN; (250, 0) da NaN.
Pista: `pd.isna(...)`, `float("nan")`, `math.isnan` para comparar NaN en el test.

**P9. Clasificar con una función.** [ ]
Escribí `clasificar_costo(costo)`: "Barato" si es menor que 50, "Medio" de 50 a 200 inclusive, "Caro" si es mayor que 200, "Sin precio" si está vacío. Aplicala a la columna con `map` y contá cada categoría.
Resultado esperado: Barato 5, Medio 5, Caro 2, Sin precio 2.

**P10. Reto: reescribir una regla con `np.select`.** [ ]
Reproducí la columna `Semaforo` (sin el Motivo) con `np.select`, usando las reglas de la sección "Reglas de decisión" del ROADMAP. Compará con la que calcula el sistema.
Datos: usá `analizar_wishlist(hojas_demo()["WishList"], perfil)` para tener `Meses de Espera` (con infinito).
Resultado esperado: tu columna es idéntica a la del sistema en las 14 filas.
Pista: `np.select(lista_de_condiciones, lista_de_resultados, default=...)` evalúa en orden y se queda con la primera que se cumple.

### Excel

**E8. Condición anidada.** [ ]
Agregá a `TablaAnalisis` la columna "Rango de costo" con las mismas reglas de P9. Compará los conteos con los de Python.
Pista: `SI` anidado o `SI.CONJUNTO` (`IFS`). Un costo vacío necesita su propio caso: `ESBLANCO`.
Resultado esperado: Barato 5, Medio 5, Caro 2, Sin precio 2.

**E9. El problema del espacio escondido.** [ ]
Copiá la columna Tipo a una hoja nueva. A una de las celdas "Deseo" agregale un espacio al final. Armá una tabla dinámica con esa columna. ¿Qué ves? Corregilo con una fórmula.
Resultado esperado: aparecen dos filas, "Deseo" y "Deseo " (con espacio). Con `ESPACIOS()` vuelve a ser una sola.
Pista: así se veían tus datos reales antes de que el sistema los normalizara.

**E10. Power Query en Excel.** [ ]
En un libro nuevo: Datos > Obtener datos > Desde archivo > Desde libro de Excel. Cargá `TablaAnalisis`, filtrá `Semaforo` distinto de "Comprado", agrupá por Tipo sumando el costo y cargá el resultado.
Resultado esperado: Deseo 3577, Necesidad 270.
Después: cambiá un dato en el origen y usá Datos > Actualizar todo.

### Power BI

**B5. Segmentador y contexto de filtro.** [ ]
Agregá un segmentador de Tipo. Seleccioná "Deseo" y mirá `Total Pendiente`. Predecí el valor antes de mirarlo.
Resultado esperado: Deseo 3577, Necesidad 270.

**B6. Porcentaje del total con `ALL`.** [ ]
Creá `% del Costo` (parte que representa cada semáforo del costo total). ¿Qué pasa si quitás el `ALL`?
Resultado esperado (demo): Comprar ya 8.8%, Esperar 13.1%, No conviene 77.5%, Comprado 0.6%.
Sin `ALL`, cada barra daría 100% porque el denominador también se filtra por semáforo.

**B7. Meta 50/30/20 contra real.** [ ]
Creá una tabla pequeña (Introducir datos) con Categoria: Necesidades, Deseos, Ahorro, y Meta: 0.5, 0.3, 0.2. Hacé una medida `Real %` que devuelva el valor real según la categoría seleccionada y mostrá meta y real en barras agrupadas.
Resultado esperado: Necesidades 43.3% (meta 50%), Deseos 8% (meta 30%), Ahorro 48.7% (meta 20%).
Pista: `SWITCH(SELECTEDVALUE(Categorias[Categoria]), ...)`.

---

## Nivel 3: Sistema

**P11. Agregar una columna al sistema.** [ ]
Agregá la columna `Link` (dirección web de la tienda) de punta a punta. Trabajá en una rama de git: `git switch -c agregar-link`.
Checklist:
- [ ] Agregarla a `COLUMNAS_WISHLIST` en `datos_excel.py`.
- [ ] Agregar el campo `st.text_input("Link")` al formulario y el valor al diccionario de `nuevo_articulo` en `WishList.py`.
- [ ] Escribir un test en `test_datos_excel.py`: un Excel antiguo sin `Link` se carga con la columna vacía.
- [ ] Correr `python -m pytest` (todo en verde).
- [ ] Probar en la app con el modo de ejemplo apagado sobre una copia de tu Excel.
- [ ] Anotar en el ROADMAP.
Pregunta: ¿qué pasa con las filas antiguas del Excel y por qué?

**P12. Qué pasa si cambio una regla.** [ ]
Predecí, antes de ejecutar, cuántos artículos quedan en cada semáforo si `MESES_MAXIMO_ESPERA` vale 1, y si vale 12. Después verificalo en un script de práctica que cambie esa constante en el módulo `finanzas` y llame a `analizar_wishlist` con los datos de ejemplo.
Resultados esperados:
- Con 1: No conviene 7, Comprar ya 3, Por cotizar 2, Comprado 2.
- Con 12: Esperar 8, Comprar ya 2, Por cotizar 2, Comprado 2.
- Con 6 (el valor actual): Esperar 6, Comprar ya 3, Por cotizar 2, Comprado 2, No conviene 1.
Pregunta: con 12, ¿por qué "Pedalera" deja de estar en Comprar ya?

**P13. Cambiar los pesos.** [ ]
Con urgencia 0.70, valor 0.20 y necesidad 0.10, ¿cuáles son los 4 primeros artículos pendientes por puntaje? ¿Qué cambia respecto a los pesos actuales?
Resultado esperado: Medias 90.0, Mouse 77.5, Zapatos 77.5, Guitarra nueva 72.5.

**B8. Tu reporte completo.** [ ]
Armá la página del reporte (guía de Power BI, paso 4), guardala como `.pbip` y pasale la ruta a Claude para que agregue una página con visuales. Después cambiá el origen de datos a tu Excel real.
Resultado esperado: el reporte con tus datos reales muestra los mismos números que la pestaña Dashboard de la app.

---

## Nivel 4: Análisis propio

**Reto final.** [ ]
Con los datos de ejemplo, respondé: **si mi ingreso sube 20%, qué cambia en mi lista?** Resolvelo en las tres herramientas y compará:
- **Python:** creá un perfil nuevo con `ingreso * 1.2` y compará el semáforo antes y después.
- **Excel:** cambiá el ingreso en la hoja Perfil de una copia y recalculá lo que dependa de él.
- **Power BI:** creá un parámetro "Variación del ingreso" y una medida que lo use.

Resultado esperado en Python: deseos disponibles de 420 (antes 330). Pasan a "Comprar ya" 5 artículos (Audífonos, Pedalera, Suscripción, Medias y Mouse) en vez de 3. Esperar 4, Por cotizar 2, Comprado 2, No conviene 1.
Escribí en 5 líneas qué concluís y qué haría falta para tomar una decisión real de compra.

---

## Preguntas para repasar

1. ¿Por qué un costo vacío no debe guardarse como 0?
2. ¿Qué diferencia hay entre una Tabla de Excel y un rango?
3. ¿Qué es el contexto de filtro en DAX?
4. ¿Por qué `finanzas.py` no importa Streamlit?
5. ¿Por qué se guarda la hoja `Analisis` en el Excel en lugar de recalcular todo en Power BI?
6. Un gasto enorme no bloquea a los pequeños: ¿qué regla lo hace y por qué existe?

Las respuestas de cada una están al final de `SOLUCIONES.md`.
