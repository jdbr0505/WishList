# WishList

Sistema para organizar y priorizar compras con la **regla 50/30/20**: registrás lo que querés comprar y la app calcula, según tu ingreso y tu fondo de emergencia, si conviene **comprarlo ya, esperar o descartarlo**. Hecho con Python, Streamlit, pandas, Excel y Power BI. Todos los montos están en dólares (USD).

**Demostración en línea (datos inventados):** https://wishlistjd.streamlit.app/

## Qué hace

- Formulario de artículos con tipo, costo, urgencia y valor, y una lista editable.
- Perfil financiero (ingreso, gastos fijos, ahorro) y presupuesto 50/30/20.
- Análisis con un **semáforo** (comprar ya, esperar, no conviene) y el motivo de cada decisión.
- Dashboard con gráficos de Plotly. Reporte de Power BI incluido en `WishList.pbip`.

## Tres formas de usarla

| Modo | Dónde viven los datos | Cómo se activa |
|---|---|---|
| **Demostración** | Datos inventados, no guarda nada | Es el modo por defecto si no hay `TablaWishList.xlsx` |
| **Local** | Un Excel en tu computadora | Tené `TablaWishList.xlsx` junto a `WishList.py`, o `WISHLIST_DATOS_REALES=1` |
| **Privada en la nube** | Una hoja de Google, con login de Google | `WISHLIST_MODO=nube` + secretos (guía: [docs/NUBE_PRIVADA.md](docs/NUBE_PRIVADA.md)) |

Los datos reales nunca se suben a git (`.gitignore`).

### Desde el teléfono

- **Mostrar el proyecto:** abrí la demostración en línea (enlace de arriba).
- **Tus datos reales:** `TablaWishList.xlsx` está en OneDrive, así que con la app de Excel (o la de OneDrive) lo ves y lo editás desde el teléfono. La hoja `Analisis` (el semáforo) la recalcula la app cuando guardás desde la PC, no desde el teléfono. Evitá tener el archivo abierto en los dos lados a la vez.

## Empezar

```
pip install -r requirements.txt
streamlit run WishList.py
```

Para correr las pruebas: `pip install -r requirements-dev.txt` y luego `python -m pytest`.

## Documentación

- [Guía del sistema](docs/GUIA_DEL_SISTEMA.md) · [Manual de ejercicios](docs/MANUAL_EJERCICIOS.md) · [Soluciones](docs/SOLUCIONES.md)
- [Publicar la demostración](docs/DESPLIEGUE.md) · [Versión privada en la nube](docs/NUBE_PRIVADA.md)
- [Guía de Power BI](powerbi/GUIA_POWER_BI.md) · [Hoja de ruta](ROADMAP.md)

## Estructura

| Archivo | Para qué sirve |
|---|---|
| `WishList.py` | La interfaz (Streamlit) |
| `finanzas.py` | La lógica: 50/30/20, prioridad y semáforo |
| `datos_excel.py` | Leer, limpiar y guardar los datos |
| `almacenamiento.py` | Dónde se guardan: Excel local o Google Sheets |
| `acceso.py` | Quién puede entrar y qué modo usa la app |
| `graficos.py` · `datos_demo.py` | Gráficos y datos de ejemplo |
| `test_*.py` | Pruebas automáticas (pytest) |
