# La vitrina: tus datos reales en el navegador, con contraseña

La **vitrina** es una segunda copia de la app publicada en Streamlit Community Cloud que muestra **tus datos reales** a quien tenga la contraseña. Es **solo lectura**: no se puede guardar, editar ni descargar el Excel. Sirve para enseñar el proyecto con datos de verdad desde cualquier navegador, sin encender la laptop.

La demostración pública (datos inventados) sigue siendo otra app distinta y no cambia.

## Qué ve y qué no ve el visitante

- Con la contraseña ve **todo**: artículos, análisis, dashboard y el **perfil financiero** (ingreso, gastos fijos y ahorro). Se eligió así a propósito ("todo igual que yo").
- No puede: guardar, editar la lista, cambiar el perfil ni descargar el Excel. Las pestañas y botones de edición no existen en este modo.
- Sin la contraseña no ve ningún dato: el Excel viaja codificado dentro de los secretos de Streamlit y la app solo lo abre después de verificar la clave.

## Límites (léelos antes de compartir la contraseña)

- **Una sola contraseña para todos.** No distingue a una persona de otra. Quien la tenga puede reenviarla y ver tu ingreso y tus ahorros. Para quitarle el acceso a alguien hay que **cambiar la contraseña** (y eso se la quita a todos).
- **Los datos no se actualizan solos.** La vitrina muestra una foto del Excel del momento en que corriste `preparar_vitrina.py`. Cada vez que quieras actualizarla, repetís el proceso (abajo).
- **La dirección web es pública.** La contraseña es la única protección. Por eso se exige una de 12 caracteres o más (una frase larga sirve).
- **Intentos limitados:** tras 10 contraseñas incorrectas en 10 minutos, la vitrina se bloquea para todos durante ese tiempo, y cada error espera 1 segundo. Es un freno contra adivinar, no una defensa absoluta.
- **Tus datos viven en un servicio de terceros** (Streamlit guarda los secretos). Es menos grave que subirlos a GitHub, pero deja de ser "solo en mi computadora". Si no querés eso, no uses la vitrina y quedate con la demostración.
- El texto de secretos contiene tus datos reales. Streamlit podría tener un tamaño máximo para secretos (no lo verifiqué): el script avisa si el texto pesa más de 200 KB.

## Cómo se arma (la primera vez)

Lo hacés vos porque implica elegir una contraseña y entrar a tu cuenta de Streamlit. Yo no necesito ver ni la contraseña ni el archivo.

1. **Elegí la contraseña** (12 caracteres o más). Guardala en tu gestor de contraseñas: la app no la guarda en ningún lado, solo una huella que no permite recuperarla.
2. En PowerShell, desde la carpeta del proyecto:

   ```
   python preparar_vitrina.py
   ```

   Te pide la contraseña dos veces (no se ve al escribirla). Lee `TablaWishList.xlsx` **sin modificarlo** y crea `vitrina_secretos.toml`.
3. Abrí `vitrina_secretos.toml` y copiá **todo** su contenido.
4. En share.streamlit.io: **Create app** con el mismo repositorio (`jdbr0505/WishList`), rama `main` y archivo `WishList.py`. Si el menú no te deja repetir repositorio y archivo, avisame antes de seguir.
5. En **Advanced settings**: Python 3.12 y, en **Secrets**, pegá el contenido copiado. Elegí una dirección difícil de adivinar (no `wishlist`).
6. **Deploy**. Debe aparecer "Esta es una vitrina de solo lectura" y un campo de contraseña. Probá primero una contraseña equivocada (debe decir incorrecta y no mostrar nada) y luego la correcta.
7. **Borrá `vitrina_secretos.toml`.** Tiene tus datos reales. Git ya lo ignora, pero la carpeta está en OneDrive, que sí lo sincronizaría.

Importante: **la app de la vitrina no debe tener** el secreto `WISHLIST_SOLO_DEMO`. Ese secreto es de la demostración y, si estuviera en la vitrina, tendría prioridad y mostraría datos inventados.

## Cómo se actualiza o se cambia la clave

- **Actualizar los datos:** guardá tus cambios en `TablaWishList.xlsx`, corré otra vez `python preparar_vitrina.py` (puede ser la misma contraseña), pegá el nuevo contenido en **Settings > Secrets** de la app de la vitrina y guardá. Borrá el archivo.
- **Cambiar la contraseña:** igual que arriba, con la contraseña nueva. La anterior deja de funcionar al guardar los secretos.
- **Quitar la vitrina:** en share.streamlit.io, borrá la app. Los datos desaparecen de ahí (no los del Excel de tu computadora).

## Cómo funciona por dentro (para estudiar)

| Pieza | Archivo | Qué hace |
|---|---|---|
| Huella de la clave | `vitrina.py` (`generar_clave_hash`, `verificar_clave`) | `scrypt` con sal aleatoria y comparación en tiempo constante (`hmac.compare_digest`). Si falta la huella o está rota, **nadie entra**. |
| Datos codificados | `vitrina.py` (`codificar_excel`, `hojas_desde_b64`) | El Excel se guarda como texto base64 dentro del secreto y se lee de vuelta en memoria. |
| Límite de intentos | `vitrina.py` (`LimitadorIntentos`) | Un contador global compartido por todas las sesiones, no uno por visitante. |
| Elección de modo | `acceso.py` (`elegir_modo`) | `WISHLIST_SOLO_DEMO` gana; luego la vitrina; luego el Excel local; si no, demostración. |
| Solo lectura | `WishList.py` (`SOLO_LECTURA`) | Sin formularios, sin editor, sin descarga, y `guardar()` se niega. Ignora un Excel local aunque exista al lado. |
| Preparación | `preparar_vitrina.py` | Genera el TOML, lo valida (lee los datos de vuelta y verifica la clave) y lo escribe sin BOM. |

Las pruebas (`test_vitrina.py`, `test_vitrina_app.py`, `test_preparar_vitrina.py`) comprueban que sin contraseña no se ve ningún dato, que una incorrecta no entra, que el bloqueo vale para todas las sesiones y que el archivo generado abre la vitrina de punta a punta. Para saber que esas pruebas detectan fallos, se sabotearon a propósito el verificador (siempre aceptaba) y el limitador (nunca bloqueaba): en ambos casos fallaron, como debía ser.

## Si algo falla

- **"La vitrina no está configurada del todo. Falta: …"**: faltan secretos. Pegá de nuevo el contenido completo.
- **"No pude leer los datos de la vitrina"**: el secreto `VITRINA_EXCEL_B64` quedó cortado o con comillas rotas. Volvé a generar y pegar.
- **Muestra la demostración en vez de la vitrina**: los secretos no se aplicaron (revisá que `WISHLIST_MODO = "vitrina"` esté) o la app tiene `WISHLIST_SOLO_DEMO`.
- **Sigue en blanco o pide datos**: revisá que el archivo no tenga caracteres raros al copiar; el script lo escribe en UTF-8 sin BOM justamente para evitar eso.
