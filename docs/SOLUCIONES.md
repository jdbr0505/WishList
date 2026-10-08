# Soluciones del manual de ejercicios

Mirá una solución solo después de intentar el ejercicio. El código de Python de P1 a P10 y del reto final se ejecutó contra `powerbi/WishList_demo.xlsx` y dio los resultados esperados del manual. Las fórmulas de Excel y las medidas DAX no se ejecutaron en esas herramientas: sus resultados se calcularon con pandas, así que si el tuyo difiere, revisá primero separadores y nombres de columna.

Todos los fragmentos de Python parten de esto:

```python
import numpy as np
import pandas as pd

df = pd.read_excel("powerbi/WishList_demo.xlsx", sheet_name="Analisis")
```

---

## Nivel 1: Python

**P1**
```python
print(df.shape)       # (14, 17)
print(df.columns.tolist())
print(df.head())
```

**P2**
```python
print(df.groupby("Tipo").size())
print(df["Tipo"].value_counts())
```
`groupby().size()` cuenta filas por grupo. `value_counts()` hace lo mismo y ordena de mayor a menor.

**P3**
```python
pendientes = df[(df["Estado"] == "Pendiente") & df["Costo Estimado"].notna()]
print(len(pendientes), pendientes["Costo Estimado"].sum())   # 10 3847.0
```
Los paréntesis son obligatorios: `&` pesa más que `==`. Y se usa `&`, no `and`, porque se comparan series completas.

**P4**
```python
resumen = df.groupby("Estado").agg(
    articulos=("Articulo", "count"),
    con_costo=("Costo Estimado", "count"),
    total=("Costo Estimado", "sum"),
)
print(resumen)
```
En Pendiente hay 12 artículos pero solo 10 con costo: `count` no cuenta los vacíos (NaN), y 2 artículos no tienen precio.

**P5**
```python
top = df[df["Estado"] == "Pendiente"].nlargest(3, "Puntaje")[["Articulo", "Puntaje"]]
print(top)
```
Mouse y Zapatos empatan en 81.2. `nlargest` desempata por orden de aparición.

**P6**
```python
vacios = df["Costo Estimado"].isna()
print(vacios.sum(), round(vacios.mean() * 100, 1))   # 2 14.3
```
`vacios.mean()` promedia True/False como 1/0, o sea, da la proporción. Si los vacíos fueran 0, el promedio de costos bajaría (de 322.5 a 276.4) y parecería que hay artículos gratis.

**P7**
```python
por_semaforo = df.groupby("Semaforo")["Costo Estimado"].sum()
print(por_semaforo)
print(round(por_semaforo["No conviene"] / por_semaforo.sum() * 100, 1))   # 77.5
```
"Por cotizar" suma 0 porque sus costos son vacíos (la suma de vacíos es 0). Eso no significa que cuesten 0.

---

## Nivel 1: Excel

Los separadores de argumentos pueden ser `;` o `,` según la configuración regional. En una instalación en español suelen ser `;`.

**E1.** Pestaña Diseño de tabla > Nombre de la tabla. Rango: seleccioná una celda de la tabla y mirá Cambiar tamaño de tabla.

**E2**
```
=SUMAR.SI(TablaAnalisis[Estado];"Pendiente";TablaAnalisis[Costo Estimado])
```

**E3**
```
=CONTAR.SI.CONJUNTO(TablaAnalisis[Tipo];"Deseo";TablaAnalisis[Estado];"Pendiente")
=CONTAR.SI.CONJUNTO(TablaAnalisis[Tipo];"Necesidad";TablaAnalisis[Estado];"Pendiente")
```

**E4** (con "Pedalera" en A1)
```
=BUSCARX(A1;TablaAnalisis[Articulo];TablaAnalisis[Costo Estimado])
=BUSCARX(A1;TablaAnalisis[Articulo];TablaAnalisis[Semaforo])
```

**E5** (columna nueva en TablaWishList, formato porcentaje)
```
=SI(ESNUMERO([@[Costo Estimado]]);[@[Costo Estimado]]/INDICE(TablaPerfil[Ingreso Neto Mensual];1);"")
```
Sin el `SI(ESNUMERO(...))`, una celda vacía se trata como 0 y daría 0%, que es una mentira: el artículo no cuesta cero, falta cotizarlo. Es el mismo problema que NaN contra 0 en pandas.

**E6.** Seleccioná la columna Semaforo, Formato condicional > Resaltar reglas de celdas > Texto que contiene. Creá una regla por cada valor.

**E7.** Insertar > Tabla dinámica > TablaAnalisis. Filas = Semaforo, Columnas = Tipo, Valores = Suma de Costo Estimado.

---

## Nivel 1: Power BI

**B1.** Transformar datos: mirá el icono de tipo (ABC para texto, 1.2 para decimal, 123 para entero, calendario para fecha).

**B2** (están en `powerbi/medidas.dax`)
```dax
Articulos Pendientes =
CALCULATE ( COUNTROWS ( TablaAnalisis ), TablaAnalisis[Semaforo] <> "Comprado" )

Total Pendiente =
CALCULATE ( SUM ( TablaAnalisis[Costo Estimado] ), TablaAnalisis[Semaforo] <> "Comprado" )

Por Cotizar =
CALCULATE ( COUNTROWS ( TablaAnalisis ), TablaAnalisis[Semaforo] = "Por cotizar" )
```

**B3.** Medida `Costo Total = SUM ( TablaAnalisis[Costo Estimado] )` en valores y `TablaAnalisis[Semaforo]` en el eje.

**B4**
```dax
% de un Mes de Ingreso =
DIVIDE ( [Total Pendiente], MAX ( TablaPerfil[Ingreso Neto Mensual] ) )
```
`DIVIDE` devuelve vacío (o un valor alternativo) cuando el divisor es 0 o vacío. El operador `/` devuelve error o infinito, y ese error se propaga a todos los visuales que usan la medida.

---

## Nivel 2: Python

**P8**
```python
import math
import pandas as pd


def porcentaje_del_ingreso(costo, ingreso):
    if pd.isna(costo) or ingreso <= 0:
        return float("nan")
    return round(costo / ingreso * 100, 1)
```
```python
# practica/test_p08.py
import math
from practica.p08 import porcentaje_del_ingreso   # ajustá el import a tu estructura


def test_porcentaje_normal():
    assert porcentaje_del_ingreso(250, 1500) == 16.7


def test_costo_vacio_da_nan():
    assert math.isnan(porcentaje_del_ingreso(float("nan"), 1500))


def test_ingreso_cero_da_nan():
    assert math.isnan(porcentaje_del_ingreso(250, 0))
```
No se puede comparar `NaN == NaN` (da `False`), por eso se usa `math.isnan`.
Si el import falla, poné tu función y los tests en el mismo archivo `practica/test_p08.py`.

**P9**
```python
def clasificar_costo(costo):
    if pd.isna(costo):
        return "Sin precio"
    if costo < 50:
        return "Barato"
    if costo <= 200:
        return "Medio"
    return "Caro"


print(df["Costo Estimado"].map(clasificar_costo).value_counts())
```
El caso del vacío va primero: `NaN < 50` da `False` y caería hasta "Caro" por error.

**P10**
```python
import finanzas as f
from datos_demo import hojas_demo

hojas = hojas_demo()
perfil = f.perfil_desde_hoja(hojas["Perfil"])
a = f.analizar_wishlist(hojas["WishList"], perfil)   # con infinito, sin pasar por Excel
fondo_ok = f.fondo_completo(perfil)

condiciones = [
    a["Estado"] == "Comprado",
    a["Costo Estimado"].isna() | (a["Costo Estimado"] <= 0),
    ~a["Tipo"].isin(["Deseo", "Necesidad"]),
    np.isinf(a["Meses de Espera"]),
    (a["Tipo"] == "Deseo") & (not fondo_ok),
    a["Meses de Espera"] <= 1,
    a["Meses de Espera"] <= 6,
]
resultados = ["Comprado", "Por cotizar", "Clasificar", "No conviene", "Esperar", "Comprar ya", "Esperar"]

mio = np.select(condiciones, resultados, default="No conviene")
print((mio == a["Semaforo"].to_numpy()).all())   # True
```
El orden importa: `np.select` toma la primera condición verdadera, igual que la función `decidir`. Lo que no puede hacer `np.select` de forma cómoda es el Motivo con texto variable ("Alcanza en 3 meses"), por eso el sistema usa una función con reglas en orden.

---

## Nivel 2: Excel

**E8**
```
=SI(ESBLANCO([@[Costo Estimado]]);"Sin precio";SI([@[Costo Estimado]]<50;"Barato";SI([@[Costo Estimado]]<=200;"Medio";"Caro")))
```
Con `SI.CONJUNTO` es más corto, pero sigue necesitando el caso vacío primero. Como en Python, el orden de las condiciones decide el resultado.

**E9.** La tabla dinámica trata "Deseo" y "Deseo " como valores distintos. Corrección en una columna auxiliar:
```
=ESPACIOS(A2)
```
Copiá y pegá como valores sobre la columna original. En el sistema, la misma limpieza es `.str.strip()` dentro de `normalizar_wishlist`.

**E10.** Pasos en Power Query: Obtener datos > Desde libro > TablaAnalisis > Transformar. En Semaforo, filtro "no es igual a" Comprado. Transformar > Agrupar por Tipo, operación Suma sobre Costo Estimado. Cerrar y cargar. Si el origen cambia, Datos > Actualizar todo repite todos los pasos.

---

## Nivel 2: Power BI

**B5.** Con el segmentador en "Deseo", el contexto de filtro de `TablaAnalisis` queda restringido a esas filas. `CALCULATE` agrega además su propia condición (`<> "Comprado"`). Las dos se combinan, y el resultado es 3577.

**B6**
```dax
% del Costo =
DIVIDE (
    [Costo Total],
    CALCULATE ( [Costo Total], ALL ( TablaAnalisis[Semaforo] ) )
)
```
Sin `ALL`, el denominador también se filtra por el semáforo de cada barra y cada una daría 100%.

**B7**
```dax
Meta % =
SELECTEDVALUE ( Categorias[Meta] )

Real % =
SWITCH (
    SELECTEDVALUE ( Categorias[Categoria] ),
    "Necesidades", [Necesidades Real %],
    "Deseos", [Deseos Real %],
    "Ahorro", [Ahorro Real %]
)
```
Poné `Categorias[Categoria]` en el eje y las dos medidas en valores.

---

## Nivel 3

**P11.** Los cuatro cambios mínimos:
```python
# datos_excel.py
COLUMNAS_WISHLIST = [
  "Articulo", "Tipo", "Costo Estimado", "Estado", "Notas",
  "Frecuencia", "Urgencia", "Valor", "Fecha de alta", "Link",
]
```
```python
# WishList.py, dentro del formulario
link = st.text_input("Link")
...
# y en el diccionario de nuevo_articulo
"Link": link.strip(),
```
```python
# test_datos_excel.py
def test_normalizar_wishlist_agrega_link_vacio_a_un_excel_antiguo():
    limpios = normalizar_wishlist(_wishlist_antigua())

    assert "Link" in limpios.columns
    assert limpios["Link"].isna().all()
```
Las filas antiguas quedan con `Link` vacío: `reindex(columns=...)` agrega las columnas que faltan con vacíos y no toca las que ya existen. Por eso el sistema migra un Excel viejo sin romperse.
Detalle: `normalizar_wishlist` pone las columnas esperadas primero, así que `Link` queda al final del bloque esperado y antes de cualquier columna extra que hayas agregado a mano.

**P12**
```python
import pandas as pd
import finanzas as f
from datos_demo import hojas_demo

hojas = hojas_demo()
perfil = f.perfil_desde_hoja(hojas["Perfil"])
hoy = pd.Timestamp("2026-10-01")

for maximo in (1, 6, 12):
    f.MESES_MAXIMO_ESPERA = maximo
    resultado = f.analizar_wishlist(hojas["WishList"], perfil, hoy)
    print(maximo, resultado["Semaforo"].value_counts().to_dict())
```
Se cambia la constante dentro del módulo `f` (no importando el nombre suelto) porque las funciones leen la constante del módulo cada vez que corren.

Por qué con 12 "Pedalera" deja de estar en Comprar ya: la guitarra (3000 / 330 = 9.1, redondeado 10 meses) ahora entra en la fila de espera, porque 10 no supera 12. Tiene más puntaje (63.7) que Pedalera (52.5), así que va primero y Pedalera queda detrás de 3000 de costo acumulado. Con 6, la guitarra queda fuera de alcance y no bloquea.

**P13**
```python
f.PESO_URGENCIA, f.PESO_VALOR, f.PESO_NECESIDAD = 0.70, 0.20, 0.10
resultado = f.analizar_wishlist(hojas["WishList"], perfil, hoy)
pend = resultado[resultado["Semaforo"] != "Comprado"]
print(pend.nlargest(4, "Puntaje")[["Articulo", "Puntaje"]])
```
Con los pesos actuales el top 4 es Medias 85.0, Mouse 81.2, Zapatos 81.2, Guitarra nueva 63.7. Al subir el peso de la urgencia, la guitarra sube de 63.7 a 72.5 porque tiene urgencia 4.

**B8.** No tiene una solución única. Comprobá que Total Pendiente, % de un mes de ingreso, Plazo máximo y Por cotizar coincidan con las tarjetas de la pestaña Dashboard de la app.

---

## Reto final

```python
import finanzas as f

p2 = f.Perfil(
    perfil.ingreso * 1.2, perfil.gastos_fijos, perfil.deseos_gastados,
    perfil.ahorro_actual, perfil.meses_fondo_objetivo,
)
antes = f.analizar_wishlist(hojas["WishList"], perfil, hoy)
despues = f.analizar_wishlist(hojas["WishList"], p2, hoy)

print(f.deseos_disponibles(p2))                          # 420.0
print(antes["Semaforo"].value_counts().to_dict())
print(despues["Semaforo"].value_counts().to_dict())
print(despues[despues["Semaforo"] == "Comprar ya"]["Articulo"].tolist())
```
Resultado: deseos disponibles de 420 (antes 330). "Comprar ya" pasa de 3 a 5 artículos: Audífonos in ears, Pedalera, Suscripción Workspace, Medias y Mouse.
Observá que Perfil es inmutable (`frozen=True`): por eso se crea uno nuevo en vez de modificar el original.

Excel: cambiá el ingreso en una copia y recalculá `Ingreso × 0.30 − deseos ya gastados`. Power BI: Modelado > Nuevo parámetro > Rango numérico de 0 a 0.5, y una medida como
```dax
Deseos Disponibles Ajustado =
MAX ( TablaPerfil[Ingreso Neto Mensual] ) * ( 1 + [Variacion Valor] ) * 0.3
    - MAX ( TablaPerfil[Deseos ya gastados] )
```
(el nombre `[Variacion Valor]` depende de cómo nombres el parámetro).

Para una decisión real faltaría: precios reales de los dos artículos sin cotizar, validar que el ingreso extra es estable y no solo un mes, revisar si hay gastos fijos nuevos asociados al aumento y decidir si parte del ingreso extra va a ahorro antes de ir a deseos.

---

## Respuestas a las preguntas de repaso

1. Un 0 es un dato falso: significa "cuesta cero". Un vacío significa "no sé". Con 0 se falsean los promedios, los porcentajes y los totales, y el sistema marcaría como "Comprar ya" algo sin precio.
2. Una Tabla tiene nombre, cabeceras fijas, crece sola al agregar filas y se puede referenciar con `TablaX[Columna]`. Un rango es solo celdas: Power BI y las fórmulas tienen que adivinar dónde termina.
3. Es el conjunto de filtros activos cuando se evalúa una medida (ejes, segmentadores, filtros de página y los que agrega `CALCULATE`). La misma medida da resultados distintos en cada visual.
4. Para poder probarla con `pytest` sin abrir la interfaz y poder reutilizarla desde otro lugar (scripts, ejercicios, otras apps).
5. Para tener un solo lugar donde vive la regla de negocio. Si la repetís en DAX, hay dos versiones que pueden divergir. Aun así, reproducir una parte en DAX es un buen ejercicio: sirve para comparar y detectar errores.
6. La regla de "fuera de alcance": un artículo que, solo, tardaría más de 6 meses no entra en la fila de espera. Existe porque, sin ella, un gasto enorme con mucha prioridad consume todo el presupuesto acumulado y manda a "No conviene" a todos los artículos pequeños que sí se podrían comprar.
