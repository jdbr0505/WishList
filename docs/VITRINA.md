# La vitrina: una sola página, demostración para todos y tus datos reales con contraseña

Es **la misma página pública de siempre** (https://wishlistjd.streamlit.app/). Cualquiera que entra ve la **demostración con datos inventados**. Arriba hay un recuadro **"🔒 Ver mis datos reales (con contraseña)"**: si escribes la contraseña correcta, la página muestra **tus datos reales** en solo lectura. Si no la escribes, o está mal, sigue la demostración.

No hay una segunda app: son los mismos archivos y la misma dirección, y lo único que cambia son los **secretos** de esa app en Streamlit.

## Qué ve y qué no ve cada uno

| | Sin contraseña (cualquiera) | Con la contraseña |
|---|---|---|
| Datos | Inventados (demostración) | Los tuyos, incluido el **perfil** (ingreso, gastos fijos, ahorro) |
| Guardar, editar, descargar | No guarda nada; baja solo un Excel de ejemplo | No hay nada para guardar, editar ni descargar: esas pestañas y botones no existen |

Que se vea todo, perfil incluido, fue una decisión tuya ("todo igual que yo").

## Límites (léelos antes de compartir la contraseña)

- **Una sola contraseña para todos.** No distingue a una persona de otra. Quien la tenga puede reenviarla y ver tu ingreso y tus ahorros. Para quitarle el acceso a alguien hay que **cambiar la contraseña** (y eso se la quita a todos).
- **Los datos no se actualizan solos.** La página muestra una foto del Excel del momento en que corriste `preparar_vitrina.py`. Para actualizarla, repites el proceso (abajo).
- **La dirección web es pública.** La contraseña es la única protección. Por eso se exige una de 12 caracteres o más (una frase larga sirve).
- **Intentos limitados:** tras 10 contraseñas incorrectas en 10 minutos, el acceso se bloquea para todos durante ese tiempo, y cada error espera 1 segundo. Es un freno contra adivinar, no una defensa absoluta.
- **Tus datos viven en un servicio de terceros** (Streamlit guarda los secretos). Es menos grave que subirlos a GitHub, pero deja de ser "solo en mi computadora". Si no quieres eso, quita los secretos y queda solo la demostración.
- El texto de secretos contiene tus datos reales. Streamlit podría tener un tamaño máximo para secretos (no lo verifiqué): el script avisa si el texto pesa más de 200 KB.

## Cómo se activa (la primera vez)

Lo haces tú porque implica entrar a tu cuenta de Streamlit y pegar tus secretos. Yo no necesito ver ni la contraseña ni el archivo.

1. **Elige la contraseña** (12 caracteres o más) y guárdala en tu gestor de contraseñas: la app no la guarda, solo una huella que no permite recuperarla.
2. En PowerShell, desde la carpeta del proyecto:

   ```
   python preparar_vitrina.py
   ```

   Pide la contraseña dos veces (no se ve al escribirla), lee `TablaWishList.xlsx` **sin modificarlo** y crea `vitrina_secretos.toml`.
3. Abre `vitrina_secretos.toml` y copia **todo** su contenido.
4. Entra a share.streamlit.io, abre tu app y ve a **⋮ > Settings > Secrets** (los menús pueden cambiar).
5. **Borra lo que haya** en ese cuadro (incluida la línea `WISHLIST_SOLO_DEMO = "1"`), pega el contenido copiado y guarda. La app se reinicia sola.
6. Comprueba en la dirección pública: debe abrir la demostración. Prueba una contraseña equivocada (dice incorrecta y sigue la demostración) y luego la correcta (cambian los datos y aparece "Vitrina de solo lectura" en la barra lateral).
7. **Borra `vitrina_secretos.toml`.** Tiene tus datos reales. Git ya lo ignora, pero la carpeta está en OneDrive, que sí lo sincronizaría.

**Importante:** el secreto `WISHLIST_SOLO_DEMO` tiene prioridad sobre todo. Si queda en los secretos, la página muestra siempre la demostración y el recuadro de contraseña no aparece. Por eso el paso 5 pide borrarlo.

## Cómo se actualiza o se cambia la clave

- **Actualizar los datos:** guarda tus cambios en `TablaWishList.xlsx`, corre otra vez `python preparar_vitrina.py` (puede ser la misma contraseña), pega el nuevo contenido en **Settings > Secrets** y guarda. Borra el archivo.
- **Cambiar la contraseña:** igual, con la contraseña nueva. La anterior deja de funcionar al guardar los secretos.
- **Volver a solo demostración:** en **Settings > Secrets** deja únicamente `WISHLIST_SOLO_DEMO = "1"`. Los datos reales desaparecen de Streamlit (no los del Excel de tu computadora).

## Cómo funciona por dentro (para estudiar)

| Pieza | Archivo | Qué hace |
|---|---|---|
| Huella de la clave | `vitrina.py` (`generar_clave_hash`, `verificar_clave`) | `scrypt` con sal aleatoria y comparación en tiempo constante (`hmac.compare_digest`). Si falta la huella o está rota, **nadie entra**. |
| Datos codificados | `vitrina.py` (`codificar_excel`, `hojas_desde_b64`) | El Excel se guarda como texto base64 dentro del secreto. Solo se decodifica **después** de verificar la contraseña. |
| Límite de intentos | `vitrina.py` (`LimitadorIntentos`) | Un contador global compartido por todas las sesiones, no uno por visitante. |
| Elección de modo | `acceso.py` (`elegir_modo`) | `WISHLIST_SOLO_DEMO` gana; luego la vitrina; luego el Excel local; si no, demostración. |
| Una sola página | `WishList.py` (`abrir_vitrina`) | Devuelve los datos reales o `None`; con `None` la página se arma igual que la demostración. Cualquier fallo (configuración incompleta, datos ilegibles, contraseña mala, bloqueo) cae en la demostración, **nunca** en datos reales. |
| Solo lectura | `WishList.py` (`SOLO_LECTURA`) | Sin formularios, sin editor, sin descarga, y `guardar()` se niega. Ignora un Excel local aunque exista al lado. |
| Preparación | `preparar_vitrina.py` | Genera el TOML, lo valida (lee los datos de vuelta y verifica la clave) y lo escribe sin BOM. |

Las pruebas (`test_vitrina.py`, `test_vitrina_app.py`, `test_preparar_vitrina.py`) comprueban que sin contraseña solo se ve la demostración, que una incorrecta no entra, que el bloqueo vale para todas las sesiones, que sin contraseña no se guarda nada y que el archivo generado abre la vitrina de punta a punta. Para saber que esas pruebas detectan fallos, se sabotearon a propósito el verificador (siempre aceptaba), el limitador (nunca bloqueaba) y la entrada de la página (no pedía contraseña): en los tres casos las pruebas fallaron, como debía ser.

## Si algo falla

- **Sale siempre la demostración y no aparece el recuadro de contraseña:** los secretos no se aplicaron. Revisa que esté `WISHLIST_MODO = "vitrina"` y que **no** esté `WISHLIST_SOLO_DEMO`.
- **Aviso "La vitrina no está configurada del todo (falta: …)":** faltan secretos. Pega de nuevo el contenido completo del archivo.
- **"No pude leer los datos de la vitrina":** el secreto `VITRINA_EXCEL_B64` quedó cortado o con comillas rotas. Vuelve a generar y pegar.
- **El cuadro de Secrets da error de formato:** copia el archivo completo, sin agregar ni quitar nada; el script lo escribe en UTF-8 sin BOM justamente para evitar eso.
