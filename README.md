# WishList

Sistema para organizar y priorizar compras con la **regla 50/30/20**: registrás lo que querés comprar y la app calcula, según tu ingreso y tu fondo de emergencia, si conviene **comprarlo ya, esperar o descartarlo**. Hecho con Python, Streamlit, pandas, Excel y Power BI. Todos los montos están en dólares (USD).

**Demostración en línea (datos inventados):** https://wishlistjd.streamlit.app/

## Qué hace

- Formulario de artículos con tipo, costo, urgencia y valor, y una lista editable.
- Perfil financiero (ingreso, gastos fijos, ahorro) y presupuesto 50/30/20.
- Análisis con un **semáforo** (comprar ya, esperar, no conviene) y el motivo de cada decisión.
- Dashboard con gráficos de Plotly que replica el reporte de Power BI (`WishList.pbip`): las páginas «Dashboard» y «Plan de compras», con las mismas medidas y los mismos números, tanto con datos de ejemplo como con los reales.

## Tres formas de usarla

| Modo | Dónde viven los datos | Cómo se activa |
|---|---|---|
| **Demostración** | Datos inventados, no guarda nada | Es el modo por defecto si no hay `excel/TablaWishList.xlsx` |
| **Local** | Un Excel en tu computadora | Tené `excel/TablaWishList.xlsx`, o `WISHLIST_DATOS_REALES=1` |
| **Vitrina** | La demostración para todos; con una contraseña compartida, tus datos reales en solo lectura (una sola página) | Secretos de la app publicada (ver [la guía](docs/VITRINA.md)) |

Los datos reales nunca se suben a git (`.gitignore`).

### Desde el teléfono

- **Mostrar el proyecto con datos inventados:** abrí la demostración en línea (enlace de arriba).
- **Mostrar tus datos reales en el navegador:** la vitrina, en la misma página pública: arriba hay un recuadro de contraseña y, sin ella, se ve la demostración. Se prepara una vez y se vuelve a preparar cuando quieras actualizar los datos: [docs/VITRINA.md](docs/VITRINA.md).
- **Ver o editar tu Excel:** `excel/TablaWishList.xlsx` está en OneDrive, así que con la app de Excel (o la de OneDrive) lo ves y lo editás desde el teléfono. La hoja `Analisis` (el semáforo) la recalcula la app cuando guardás desde la PC, no desde el teléfono. Evitá tener el archivo abierto en los dos lados a la vez.

## Empezar

```
pip install -r requisitos/requirements.txt
streamlit run python/interfaz/WishList.py
```

Para correr las pruebas: `pip install -r requisitos/requirements-dev.txt` y luego `python -m pytest python/pruebas`.

## Documentación

- [Guía del sistema](docs/GUIA_DEL_SISTEMA.md) · [Manual de ejercicios](docs/MANUAL_EJERCICIOS.md) · [Soluciones](docs/SOLUCIONES.md)
- [Publicar la demostración](docs/DESPLIEGUE.md) · [Armar la vitrina con contraseña](docs/VITRINA.md)
- [Guía de Power BI](docs/GUIA_POWER_BI.md) · [Hoja de ruta](docs/ROADMAP.md)

## Estructura

```
WishList/
├── python/          el código de la app (ver python/README.md)
│   ├── interfaz/      la página de Streamlit (WishList.py)
│   ├── logica/        datos, finanzas, medidas y modos de acceso
│   ├── dashboards/    los gráficos (Plotly)
│   ├── herramientas/  scripts que se corren a mano
│   └── pruebas/       pruebas automáticas (pytest)
├── excel/           tus libros reales (no se suben a git; ver excel/LEEME.md)
├── powerbi/         el proyecto de Power BI: WishList.pbip, consultas y medidas DAX
├── docs/            guías, manual de ejercicios y hoja de ruta
├── requisitos/      requirements.txt y requirements-dev.txt
├── .github/         pruebas automáticas en GitHub (CI)
├── .devcontainer/   entorno para Codespaces
└── .vscode/         ajustes del editor
```

Todo el código es **una sola app**: la misma página sirve la demostración pública y la vitrina con contraseña. Por eso no hay dos carpetas de código (una por sección): `python/README.md` indica, archivo por archivo, a cuál sirve cada uno.
