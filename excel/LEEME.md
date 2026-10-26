# Libros de Excel

Aquí viven tus libros reales, y **no se suben a git** (`.gitignore`): contienen tus ingresos, gastos y ahorro. Su respaldo es tu carpeta de OneDrive.

| Archivo | Para qué sirve |
|---|---|
| `TablaWishList.xlsx` | El Excel central que lee y guarda la app (hojas `WishList`, `Perfil` y `Analisis`). |
| `TablaWishList - copia.xlsx` | Copia de seguridad del original, hecha antes de que la app empezara a reescribir el archivo. |
| `vitrina_secretos.toml` | Solo existe un momento: lo crea `preparar_vitrina.py` para pegarlo en Streamlit. Bórralo después. |

Si clonas el proyecto, esta carpeta llega con este archivo y nada más: la app arranca en modo demostración. Para usar tus datos, crea tu `TablaWishList.xlsx` aquí (o corre la app con `WISHLIST_DATOS_REALES=1` y guarda un artículo).
