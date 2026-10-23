# Versión privada en la nube (Google Sheets + login de Google)

Esta versión te deja usar WishList con **tus datos reales desde el teléfono o cualquier dispositivo**, sin encender la laptop. Es una segunda app de Streamlit, aparte de la demostración pública.

## Cómo está protegida (cuatro capas)

1. **Login de Google.** Sin iniciar sesión no se ve ningún dato.
2. **Lista de correos permitidos** (`correos_permitidos`). Una cuenta de Google ajena que inicie sesión ve "Esta cuenta no tiene acceso". Si la lista está vacía, no entra nadie. El correo debe estar verificado por Google.
3. **Pantalla de consentimiento de Google en modo "Prueba"**: solo los usuarios de prueba que agregues pueden ni siquiera iniciar sesión.
4. **(Opcional) Privacidad de la app en Streamlit**: restringir quién puede abrirla, como segunda barrera.

Tus datos viven en **una hoja de Google privada**, compartida solo contigo y con una "cuenta de servicio" (un robot con su propio correo) que usa la app. Los secretos (claves) están en la configuración de Streamlit, nunca en git.

**Lo que NO hace:** no hay roles. Todo correo de la lista puede **ver y modificar** tus datos. Y el código no se despliega solo: tenés que hacer los pasos de abajo con tu cuenta de Google y de Streamlit.

> **Si querés mostrar tus datos a otra persona**, agregá su correo a `correos_permitidos`: verá todo y podrá editarlo. Para mostrar el proyecto sin datos personales, usá la demostración pública.

## Lo que se probó y lo que no

El código se probó con **simulaciones** de Google y del login (más de 50 pruebas automáticas, incluida una prueba de que una cuenta ajena no ve nada y de que un fallo de conexión nunca muestra una lista vacía). También se probó en un servidor real de Streamlit con valores falsos: sin sesión solo se ve el botón de login, y ese botón redirige a Google. **No se pudo probar con tus credenciales reales de Google**: eso lo verificás vos en los pasos 5 a 7. Si algo falla, pasame el mensaje exacto de error (sin claves).

---

## Paso 1. Crear la hoja de Google

1. En Google Sheets, creá una hoja de cálculo **vacía** (por ejemplo, "WishList datos").
2. Copiá su **ID**: es el texto largo de la dirección entre `/d/` y `/edit`.

No hace falta crear las pestañas: la app crea `WishList`, `Perfil` y `Analisis` sola al guardar.

## Paso 2. Cuenta de servicio (el "robot" que escribe en la hoja)

En console.cloud.google.com (los nombres de menú pueden cambiar):

1. Creá un **proyecto** nuevo (por ejemplo, "wishlist-privada").
2. **APIs y servicios > Biblioteca**: activá **Google Sheets API** (y, por si acaso, **Google Drive API**).
3. **APIs y servicios > Credenciales > Crear credenciales > Cuenta de servicio**. Ponele un nombre y terminá.
4. Entrá a esa cuenta > pestaña **Claves > Agregar clave > Crear clave nueva > JSON**. Se descarga un archivo: **es un secreto, no lo subas ni lo pegues en un chat**.
5. Copiá el `client_email` del archivo (termina en `.iam.gserviceaccount.com`).
6. En tu hoja de Google: **Compartir**, pegá ese correo y dale permiso de **Editor**. No la compartas con nadie más ni como "cualquiera con el enlace".

## Paso 3. Login de Google (OAuth)

En el mismo proyecto de Google Cloud:

1. **Pantalla de consentimiento de OAuth** (a veces llamada "Google Auth Platform"): tipo de usuario **Externo**, un nombre de aplicación y tu correo de contacto. Dejá la publicación en **Prueba (Testing)** y agregá tu correo como **usuario de prueba**.
2. **Credenciales > Crear credenciales > ID de cliente de OAuth > Aplicación web**.
3. En **URI de redireccionamiento autorizados** agregá las dos direcciones (la segunda la sabrás después del paso 8; podés volver a editarla):
   - `http://localhost:8501/oauth2callback`
   - `https://TU-APP-PRIVADA.streamlit.app/oauth2callback`
4. Copiá el **ID de cliente** y el **secreto de cliente**.

## Paso 4. Armar los secretos en tu computadora

1. Copiá `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` (ese archivo está en `.gitignore`).
2. Completá los valores:
   - `correos_permitidos`: tu correo de Google.
   - `[auth]`: `client_id`, `client_secret`, `redirect_uri` (la de localhost por ahora) y un `cookie_secret` aleatorio:
     ```
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - `[gsheets] spreadsheet_id`: el ID del paso 1.
   - `[gcp_service_account]`: cada campo del archivo JSON del paso 2, escrito como `campo = "valor"`. La `private_key` va con sus `\n` tal cual vienen.
3. **No pongas** `WISHLIST_MODO` en tu archivo local: así tu app de la PC sigue usando tu Excel. Solo va en los secretos de la nube.
4. **Guardá el archivo como UTF-8 sin BOM** (VS Code lo hace por defecto; el Bloc de notas antiguo agrega un BOM). Si el archivo no se puede leer, la app lo avisa arriba con un mensaje amarillo en lugar de ignorarlo en silencio.

## Paso 5. Probar la conexión (no escribe nada)

```
python probar_conexion_sheets.py
```

Debería decir `OK: conectado a la hoja «…»`. Si falla, el mensaje te dice qué revisar (casi siempre: la hoja no está compartida con el correo de la cuenta de servicio, o el ID está mal).

## Paso 6. Copiar tus datos a Google (una sola vez)

```
python subir_excel_a_sheets.py
```

Lee tu `TablaWishList.xlsx` (no lo modifica), te muestra cuántos artículos va a copiar y te pide escribir `SI`. Si la hoja de Google ya tenía datos, te avisa que los va a reemplazar.

## Paso 7. Probar el login en tu computadora

En PowerShell, desde la carpeta del proyecto:

```
$env:WISHLIST_MODO = "nube"; streamlit run WishList.py
```

Deberías ver "Esta es la versión privada…", entrar con Google y ver tus datos. Probá guardar un artículo y mirá que aparezca en la hoja de Google. Cerrá esa terminal después (la variable solo vive ahí).

## Paso 8. Publicar la app privada

1. En share.streamlit.io, **Create app** con el mismo repositorio (`jdbr0505/WishList`, rama `main`, archivo `WishList.py`).
2. **Una dirección que nadie adivine**, distinta de la de la demostración (por ejemplo, con letras al azar al final).
3. **Advanced settings**: Python 3.12, y en **Secrets** pegá el contenido de tu `secrets.toml` **más** la línea `WISHLIST_MODO = "nube"`, con `redirect_uri = "https://TU-APP-PRIVADA.streamlit.app/oauth2callback"` (la dirección real).
4. Volvé al paso 3 y agregá esa dirección de redireccionamiento en Google si no lo hiciste.
5. Entrá a la app y comprobá que pide login.
6. (Opcional) En **Settings > Sharing** de la app, restringí quién puede verla a tu correo.

La demostración pública sigue siendo otra app y no cambia.

## En el teléfono

Abrí la dirección, iniciá sesión con Google y listo. En el navegador podés usar "Agregar a pantalla de inicio" para que quede como un ícono.

## Qué tener en cuenta

- **Si dos dispositivos guardan a la vez, gana el último** que guarda. El botón "Recargar desde Google Sheets" de la barra lateral trae lo más reciente.
- **Copias de seguridad:** Google Sheets guarda el historial (Archivo > Historial de versiones). También podés descargar el Excel con el botón de la barra lateral.
- **Límites gratuitos:** la app se duerme tras un tiempo sin uso (tocá para despertarla) y Google limita las solicitudes por minuto. Es suficiente para uso personal.
- **Power BI:** tu reporte sigue leyendo tu Excel local. Para actualizarlo, descargá el Excel desde la app.
- **Si se filtra una clave:** en Google Cloud, borrá la clave de la cuenta de servicio y creá otra; cambiá el secreto de cliente de OAuth y el `cookie_secret`.
- **Tu Excel local sigue funcionando** como siempre. La versión privada es otra forma de usar la misma app.

## Si algo falla

| Mensaje | Qué revisar |
|---|---|
| "La versión privada no está configurada del todo. Falta: …" | Esos campos faltan en los secretos. La lista nunca muestra valores. |
| "Esta cuenta no tiene acceso a esta aplicación." | Tu correo no está en `correos_permitidos`, o no está verificado. |
| "Google no deja entrar a la hoja de cálculo…" | Compartí la hoja como Editor con el `client_email` de la cuenta de servicio. |
| "No encuentro la hoja de cálculo…" | Revisá el `spreadsheet_id`. |
| "Google limitó las solicitudes…" | Esperá un minuto. |
| El login no vuelve a la app | La `redirect_uri` de los secretos debe coincidir **exactamente** con una de las autorizadas en Google. |
| Google dice "acceso bloqueado" al iniciar sesión | Agregá tu correo como usuario de prueba en la pantalla de consentimiento. |
