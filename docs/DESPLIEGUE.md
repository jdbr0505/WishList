# Cómo publicar la demostración (opción B)

La app real guarda tus finanzas en un Excel local y no tiene contraseña, así que **no se despliega con tus datos**. Lo que sí se puede publicar es una **demostración**: la misma app con datos inventados, sin acceso a tu Excel y sin guardar nada.

## Cómo funciona la demostración

- Se activa con la variable `WISHLIST_SOLO_DEMO=1` (en la nube, como "secreto").
- Con esa variable, la app **nunca lee ni escribe** `TablaWishList.xlsx`. No existe el interruptor para pedir los datos reales.
- Muestra un aviso arriba: "Demostración con datos inventados".
- Los visitantes pueden recorrer todas las pestañas y descargar un Excel de ejemplo, pero no guardar.
- Tres pruebas automáticas lo comprueban (`test_modo_demo.py`): no muestra el Excel real, no lo modifica aunque se intente guardar, y sin la variable la app funciona normal.

## Probarla en tu computadora antes de publicar

En PowerShell, desde la carpeta del proyecto:

```
$env:WISHLIST_SOLO_DEMO = "1"; streamlit run WishList.py
```

Deberías ver el aviso de demostración y ningún interruptor "Ver con datos de ejemplo". Cuando termines, cerrá esa terminal (la variable solo vive en ella) y volvé a correr la app normal.

## Publicar en Streamlit Community Cloud

Los menús pueden cambiar con el tiempo: usá esto como guía.

1. Subí el código a GitHub (ver "Antes de subir" abajo).
2. Entrá a share.streamlit.io con tu cuenta de GitHub y autorizá el acceso a tu repositorio (es privado, así que hay que darle permiso).
3. **Create app** y elegí:
   - Repositorio: `jdbr0505/WishList`, rama `main`.
   - Archivo principal: `WishList.py`.
4. En **Advanced settings**:
   - Python: 3.12 (es la versión con la que se probó el despliegue).
   - Secrets: escribí `WISHLIST_SOLO_DEMO = "1"`.
5. **Deploy** y comprobá que aparece el aviso de demostración.

**Nunca despliegues sin el secreto del paso 4.** Sin él la app buscaría `TablaWishList.xlsx` (que no está en git, así que mostraría una lista vacía), pero cualquiera podría empezar a escribir datos. Con el secreto no hay forma de hacerlo.

## Antes de subir a GitHub

Tu rama local está adelantada de la remota y la remota tiene commits que vos no tenés. Para no pisar archivos como pasó con el `git pull` anterior:

1. `git status`: que no haya cambios sin confirmar que quieras conservar.
2. `git fetch` y `git log HEAD..origin/main --oneline`: mirá qué trae la remota.
3. Integrá con `git pull` y revisá `git status` y `git diff` después. Si algo se ve raro, avisame antes de subir.
4. Recién ahí, `git push`.

## Privacidad de tus datos reales

- Los archivos con tus datos (`TablaWishList*.xlsx`, `WishList.xlsx` y los `.pbix`) están en `.gitignore`: ya no se suben. Siguen en tu computadora; su respaldo es OneDrive.
- **El historial de git todavía guarda versiones viejas** de esos archivos (el primer commit ya está en GitHub, que es privado). No hagas público el repositorio sin antes limpiar el historial (por ejemplo con `git filter-repo`) o crear un repositorio nuevo con el código limpio.
- El proyecto de Power BI guarda la ruta de tu usuario de Windows en las consultas. No es un dato financiero, pero conviene saberlo si algún día compartís el repositorio.
