# Guía de Power BI para WishList

Objetivo: construir un reporte de una página que muestre lo mismo que el Dashboard de la app, y entender qué hace cada paso.

Archivos de esta carpeta:
- `WishList_demo.xlsx`: datos de ejemplo con las hojas WishList, Perfil y Analisis (regenerable con `python exportar_demo.py`).
- `consultas_power_query.m`: las consultas M para cargar las tablas.
- `medidas.dax`: las medidas DAX, de nivel 1 a 3.

Los resultados de referencia de esta guía están calculados con pandas sobre el libro de ejemplo. No los ejecuté dentro de Power BI. Si tu número no coincide, es parte del ejercicio: buscá por qué.

## Paso 1. Conectar los datos

1. Abrí Power BI Desktop y elegí un informe en blanco.
2. Inicio > Obtener datos > Excel. Elegí `WishList_demo.xlsx`.
3. En el navegador, marcá las tablas **TablaAnalisis** y **TablaPerfil** (con el icono de tabla, no las hojas) y pulsá **Transformar datos**.

Por qué las tablas y no las hojas: una Tabla de Excel tiene nombre, cabeceras fijas y solo trae las filas con datos. Una hoja puede traer filas vacías.

## Paso 2. Revisar tipos de datos (Power Query)

En el editor, mirá el icono junto a cada columna:
- Costo Estimado, Puntaje, % del Ingreso, Meses de Espera: número decimal.
- Urgencia y Valor: número entero.
- Fecha de alta y Fecha Estimada: fecha.
- Articulo, Tipo, Estado, Semaforo, Motivo: texto.

Si preferís escribirlo como código, usá `consultas_power_query.m` (Editor avanzado). Cambiá la ruta por la tuya. Después pulsá **Cerrar y aplicar**.

Concepto: Power Query limpia y da forma a los datos antes de cargarlos. El modelo y las medidas viven en otra capa.

## Paso 3. Crear las medidas

En la pestaña Inicio > Nueva medida, pegá las medidas de `medidas.dax` una por una. Empezá por las de nivel 1 y comprobá cada resultado antes de seguir.

| Medida | Resultado esperado (demo) |
|---|---|
| Articulos Pendientes | 12 |
| Total Pendiente | 3,847 |
| Por Cotizar | 2 |
| Ingreso Mensual | 1,500 |
| % de un Mes de Ingreso (formato %) | 256% |
| Comprar Ya / Esperar / No Conviene | 3 / 6 / 1 |
| Plazo Maximo (meses) | 10 |
| Necesidades / Deseos / Ahorro Real % | 43.3% / 8% / 48.7% |

Concepto central, el **contexto de filtro**: una medida no tiene un valor fijo. Cambia según los filtros del visual (el eje, los segmentadores). `CALCULATE` es la función que modifica ese contexto.

## Paso 4. Construir la página

Diseño sugerido (lienzo 16:9):

1. **Fila de tarjetas:** Total Pendiente, % de un Mes de Ingreso, Plazo Maximo (meses), Por Cotizar.
2. **Barras agrupadas** (meta contra real): necesitás una tabla auxiliar con las categorías Necesidades, Deseos, Ahorro. Es el ejercicio B7.
3. **Barras horizontales:** eje = Articulo, valor = Puntaje, ordenado de mayor a menor, color por Semaforo (formato condicional con la medida `Color Semaforo`).
4. **Segmentadores:** Tipo y Estado.
5. **Tabla:** Articulo, Costo Estimado, Meses de Espera, Fecha Estimada, Semaforo, Motivo.

Reglas de diseño: un gráfico por pregunta, colores con significado (el verde, amarillo y rojo del semáforo no se usan para otra cosa), títulos que digan lo que se ve.

## Paso 5. Guardar como proyecto (para que Claude agregue la página de visuales)

1. Archivo > Guardar como > **Proyecto de Power BI (.pbip)**. Guardalo en la carpeta `powerbi/` o donde prefieras.
   Si no ves esa opción, activala en Archivo > Opciones > Características en versión preliminar.
2. Cerrá Power BI Desktop.
3. Avisame la ruta del `.pbip`. Puedo agregar una página con los visuales escribiendo los archivos del proyecto (formato PBIR) y las medidas directamente en el modelo.
4. Reabrí el `.pbip` y revisá el resultado. Si algo no se ve bien, contame qué y lo ajusto.

Importante: no puedo ver Power BI Desktop desde aquí, así que el resultado lo verificás vos al abrirlo.

## Paso 6. Usar tus datos reales

1. Guardá un artículo desde la app para que `TablaWishList.xlsx` tenga la hoja Analisis.
2. En Power BI: Transformar datos > Configuración de origen de datos > Cambiar origen, y elegí `TablaWishList.xlsx`.
3. Actualizar. Las medidas y los visuales se mantienen porque las tablas tienen los mismos nombres.

Cuidado: si la app está guardando mientras actualizás, puede salir un error de archivo en uso. Esperá unos segundos y reintentá.

## Glosario rápido

- **Modelo semántico:** las tablas, relaciones y medidas.
- **Medida:** un cálculo que se evalúa en el contexto del visual. Por ejemplo, una suma con una condición.
- **Columna calculada:** un valor por fila que se guarda en el modelo. Usala solo si no podés resolverlo con una medida.
- **Segmentador:** filtro visual que el lector puede cambiar.
- **Contexto de filtro:** el conjunto de filtros activos cuando se calcula una medida.
