# Código de la app

Todo el código es **una sola aplicación**: la misma página de Streamlit muestra la **demostración pública** (datos inventados) y, con contraseña, la **sesión privada** (tus datos reales con todas las funciones; los cambios viven en la sesión). Separar el código en una carpeta «Público» y otra «Vitrina» obligaría a copiar `finanzas.py`, `datos_excel.py` y casi todo lo demás en las dos, y cada arreglo habría que hacerlo dos veces. Por eso se ordena por **función**, y esta tabla dice a qué sección sirve cada archivo.

Secciones: **Ambas** = la usan la demostración y la vitrina. **Público** = solo la demostración. **Vitrina** = solo la sesión privada con contraseña (el modo se llama `vitrina` en el código). **Local** = solo cuando se usa en tu computadora con tu Excel.

## `interfaz/` — la página

| Archivo | Sección | Qué hace |
|---|---|---|
| `WishList.py` | Ambas (y Local) | La página de Streamlit: pestañas, formularios, dashboard. Elige el modo y arma la pantalla. Es el archivo que se ejecuta. |

## `logica/` — datos y finanzas (sin interfaz)

| Archivo | Sección | Qué hace |
|---|---|---|
| `finanzas.py` | Ambas | Regla 50/30/20, puntaje de prioridad, plazos y semáforo. |
| `medidas.py` | Ambas | Las medidas de `powerbi/medidas.dax` en pandas (tarjetas del dashboard). |
| `datos_excel.py` | Ambas (y Local) | Leer, limpiar, validar y guardar el Excel. |
| `acceso.py` | Ambas | Decide el modo (demostración, vitrina o local). |
| `datos_demo.py` | Público | Los datos inventados de la demostración. |
| `vitrina.py` | Vitrina | Contraseña con huella `scrypt`, datos codificados y límite de intentos. |

## `dashboards/` — gráficos

| Archivo | Sección | Qué hace |
|---|---|---|
| `graficos.py` | Ambas | Las figuras de Plotly del dashboard (las mismas que el reporte de Power BI). |

## `herramientas/` — scripts que se corren a mano

| Archivo | Sección | Qué hace |
|---|---|---|
| `exportar_demo.py` | Público | Crea `powerbi/WishList_demo.xlsx` con los datos de ejemplo. |
| `preparar_vitrina.py` | Vitrina | Genera los secretos de la vitrina (Excel codificado + huella de la contraseña). |

## `pruebas/` — pytest

| Archivo | Sección | Qué comprueba |
|---|---|---|
| `test_finanzas.py`, `test_medidas.py`, `test_datos_excel.py`, `test_graficos.py` | Ambas | La lógica y los gráficos. `test_medidas.py` verifica que los números coinciden con la guía de Power BI. |
| `test_acceso.py` | Ambas | Qué modo se elige. |
| `test_dashboard_app.py` | Ambas | Las páginas del dashboard dentro de la app. |
| `test_modo_demo.py` | Público | La demostración nunca lee ni toca el Excel real. |
| `test_vitrina.py`, `test_vitrina_app.py`, `test_preparar_vitrina.py` | Vitrina | Contraseña, bloqueo de intentos, sesión privada y el script de secretos. |
| `test_seguridad_repositorio.py` | Ambas | Que los datos y secretos reales estén fuera de git. |
| `test_publicacion.py` | Ambas | Que los dos archivos puente de la raíz (para Streamlit Cloud) sigan funcionando y al día. |
| `conftest.py`, `ayudas.py` | — | Configuración y ayudas de las pruebas. |

## Cómo se importa

`python/` es la raíz del código: los módulos se importan como `from logica.finanzas import ...` y `from dashboards.graficos import ...`. Los archivos que se ejecutan directamente (`WishList.py` y los scripts de `herramientas/`) agregan `python/` al camino de importación en su primera línea de código. `pruebas/conftest.py` hace lo mismo para pytest.

## Comandos (desde la carpeta raíz del proyecto)

```
streamlit run python/interfaz/WishList.py
python -m pytest python/pruebas
python python/herramientas/exportar_demo.py
python python/herramientas/preparar_vitrina.py
```
