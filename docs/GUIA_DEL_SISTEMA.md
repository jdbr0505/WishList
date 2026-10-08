# Guía del sistema WishList

Esta guía explica cómo funciona el sistema, cómo se conectan Python, Excel y Power BI, y qué conceptos de análisis de datos practicás en cada parte. Después de leerla, hacé los ejercicios de `MANUAL_EJERCICIOS.md`.

## 1. Qué hace el sistema

Registrás artículos que querés comprar. El sistema calcula, con tus ingresos y la regla 50/30/20, si conviene comprarlos ahora, esperar o descartarlos, y lo muestra en tablas y gráficos.

Flujo de datos:

```
Formulario (Streamlit)  ->  TablaWishList.xlsx  ->  finanzas.py  ->  App (Análisis y Dashboard)
                              |  hojas:                                 
                              |  WishList, Perfil, Analisis      ->  Excel (tablas dinámicas) y Power BI
```

## 2. Los archivos

| Archivo | Para qué sirve | Herramienta |
|---|---|---|
| `WishList.py` | La interfaz: pestañas, formularios, gráficos | Streamlit |
| `datos_excel.py` | Leer, limpiar y guardar el Excel | pandas, openpyxl |
| `finanzas.py` | La lógica: 50/30/20, prioridad, semáforo | pandas, numpy |
| `graficos.py` | Las figuras del dashboard | Plotly |
| `datos_demo.py` | Datos de ejemplo (modo ejemplo) | pandas |
| `exportar_demo.py` | Crea `powerbi/WishList_demo.xlsx` | pandas |
| `test_*.py` | Pruebas automáticas | pytest |
| `TablaWishList.xlsx` | Tu Excel central (el único que guardás) | Excel |
| `ROADMAP.md` | Qué está hecho y qué falta | — |

Regla de diseño: la lógica (`finanzas.py`) no sabe nada de la interfaz. Por eso se prueba con `pytest` sin abrir la app.

## 3. Las tres hojas del Excel

- **WishList:** tus artículos. Columnas que escribís vos: Articulo, Tipo, Costo Estimado, Estado, Notas, Frecuencia, Urgencia, Valor, Fecha de alta.
- **Perfil:** una sola fila con tu ingreso neto mensual, gastos fijos, deseos ya gastados, ahorro actual y meses de fondo de emergencia objetivo.
- **Analisis:** la calcula la app cada vez que guardás. No la edites a mano: se reescribe. Es la que leen Excel y Power BI para ver lo mismo que la app.

El archivo se reescribe completo en cada guardado. Los datos de las celdas se conservan. Lo que no se conserva: fórmulas, gráficos, tablas dinámicas y formato propio dentro de ese archivo. Hacé tus análisis en otro libro que se conecte a este.

## 4. Cómo decide el sistema

1. **Presupuesto del mes:**
   - Deseos disponibles = 30% del ingreso menos lo ya gastado en deseos.
   - Necesidades disponibles = 50% del ingreso menos los gastos fijos.
2. **Puntaje de prioridad (0 a 100):** urgencia 45%, valor percibido 30%, ser necesidad 25%.
3. **Fila de espera:** dentro de cada tipo, los artículos pendientes con precio se ordenan por puntaje y se acumula el costo. Meses = costo acumulado dividido el presupuesto, redondeado hacia arriba.
4. **Semáforo:** Comprado, Por cotizar, Clasificar, Falta perfil, No conviene (sin presupuesto), No conviene (más de 6 meses), Esperar (deseo con fondo de emergencia incompleto), Comprar ya (mes 1) o Esperar (hasta 6 meses). Se evalúan en ese orden y gana la primera que se cumple.
5. **Moneda:** todos los montos están en dólares (USD). Los nombres de columna no cambian; en pantalla se muestran con `$` y en el Excel con formato de dólares.

El detalle está en la sección "Reglas de decisión" del ROADMAP.

### Ejemplo resuelto a mano

Perfil de ejemplo: ingreso 1500, gastos fijos 650, deseos ya gastados 120.

- Deseos disponibles = 1500 × 0.30 − 120 = **330** por mes.
- Pedalera cuesta 250 y es el deseo con más puntaje: 250 / 330 = 0.76, redondeado hacia arriba da **mes 1** → Comprar ya.
- Audífonos (120) va después: 250 + 120 = 370, y 370 / 330 = 1.12, redondeado hacia arriba da **mes 2** → Esperar.

## 5. La misma métrica en tres herramientas

Entender esto es lo más importante del proyecto. Mismo dato, tres lenguajes:

| Pregunta | pandas (Python) | Excel | DAX (Power BI) |
|---|---|---|---|
| ¿Cuántos artículos por tipo? | `df.groupby("Tipo").size()` | Tabla dinámica (Filas = Tipo, Valores = Cuenta) | `COUNTROWS(TablaAnalisis)` con Tipo en el eje |
| Costo total pendiente | `df.loc[df.Estado=="Pendiente","Costo Estimado"].sum()` | `=SUMAR.SI(TablaAnalisis[Estado],"Pendiente",TablaAnalisis[Costo Estimado])` | `CALCULATE(SUM(...), ... <> "Comprado")` |
| Filtrar una condición | `df[df.Tipo=="Deseo"]` | Filtro de la tabla o `SUMAR.SI.CONJUNTO` | Segmentador o argumento de `CALCULATE` |
| Celdas vacías | `NaN` (se ignoran al sumar) | Celda vacía | `BLANK()` |

## 6. Conceptos que vas a practicar

- **Limpieza de datos:** espacios sobrantes (`Deseo ` y `Deseo` son distintos), vacíos, tipos de dato. Lo hace `normalizar_wishlist`.
- **Valores vacíos:** vacío no es lo mismo que 0. Un costo vacío significa "por cotizar". Un 0 falsearía promedios y porcentajes.
- **Agrupar y agregar:** `groupby` en pandas, tablas dinámicas en Excel, el contexto de filtro en DAX.
- **Funciones puras y pruebas:** una función que recibe datos y devuelve un resultado se puede probar con casos inventados.
- **Modelo de datos:** qué columnas se guardan (entrada) y cuáles se calculan (salida).
- **Visualización:** cada gráfico responde una pregunta. Comparar dos valores es barras agrupadas. Ordenar es barras horizontales. Evolución en el tiempo es líneas o puntos.

## 7. Ruta para subir de nivel como analista de datos

Cada nivel usa este mismo proyecto. Pasá al siguiente cuando puedas hacer los ejercicios sin mirar las soluciones.

| Nivel | Qué dominás | Ejercicios |
|---|---|---|
| 1. Base | Leer datos, filtrar, contar, sumar, agrupar con pandas. Fórmulas y tablas dinámicas en Excel. Conectar Power BI y armar tarjetas y barras. | P1–P7, E1–E7, B1–B4 |
| 2. Lógica | Escribir funciones, probarlas con `pytest`, entender `NaN`. Funciones condicionales y de búsqueda en Excel. Medidas DAX con `CALCULATE`. | P8–P10, E8–E10, B5–B7 |
| 3. Sistema | Modificar el sistema: agregar una columna, cambiar una regla, predecir el efecto. Power Query en Excel y Power BI. | P11–P13, B8 |
| 4. Análisis propio | Hacer una pregunta nueva sobre tus datos reales, responderla en las tres herramientas y comparar. | Reto final |

Hábitos que te hacen mejor analista:
- Antes de calcular, escribí qué resultado esperás. Si no coincide, ahí está el aprendizaje.
- Verificá un caso a mano antes de confiar en una fórmula.
- Comparar el mismo número en dos herramientas detecta errores que una sola no muestra.
- Anotá en el ROADMAP lo que aprendés (sección "Registro de dudas y aprendizajes").

## 8. Cómo correr todo

```
streamlit run WishList.py        # la app
python -m pytest                 # las pruebas
python exportar_demo.py          # regenera powerbi/WishList_demo.xlsx
```

Dentro de la app, el interruptor "Ver con datos de ejemplo" te deja explorar sin tocar tu Excel.
