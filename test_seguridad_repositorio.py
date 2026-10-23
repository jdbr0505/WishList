"""Red de seguridad: que los secretos y los datos personales nunca terminen en git."""
import re
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent


def _git(*argumentos):
  return subprocess.run(["git", *argumentos], cwd=RAIZ, capture_output=True, text=True)


pytestmark = pytest.mark.skipif(
  _git("rev-parse", "--is-inside-work-tree").returncode != 0, reason="no es un repositorio git"
)


@pytest.mark.parametrize("ruta", [
  ".streamlit/secrets.toml",
  ".env",
  "mi-service-account-key.json",
  "client_secret_123.json",
  "TablaWishList.xlsx",
  "TablaWishList - copia.xlsx",
  "WishList.xlsx",
  "powerbi/WishList.pbix",
])
def test_estos_archivos_los_ignora_git(ruta):
  assert _git("check-ignore", "-q", ruta).returncode == 0, f"{ruta} deberia estar en .gitignore"


def test_la_plantilla_de_secretos_si_se_puede_subir():
  assert _git("check-ignore", "-q", ".streamlit/secrets.toml.example").returncode != 0


def test_ningun_archivo_rastreado_contiene_claves_privadas_reales():
  rastreados = _git("ls-files").stdout.splitlines()
  clave_real = re.compile(r"-----BEGIN (RSA )?PRIVATE KEY-----[\\nA-Za-z0-9+/=\s]{200,}")
  secreto_google = re.compile(r"GOCSPX-[A-Za-z0-9_-]{10,}")
  sospechosos = []
  for ruta in rastreados:
    archivo = RAIZ / ruta
    if archivo.suffix in {".xlsx", ".pbix", ".png", ".pyc", ".abf"} or not archivo.is_file():
      continue
    texto = archivo.read_text(encoding="utf-8", errors="ignore")
    if clave_real.search(texto) or secreto_google.search(texto):
      sospechosos.append(ruta)
  assert sospechosos == [], f"posibles secretos en archivos rastreados: {sospechosos}"


def test_la_plantilla_no_tiene_valores_reales():
  plantilla = (RAIZ / ".streamlit" / "secrets.toml.example").read_text(encoding="utf-8")

  assert "xxxxxxxx" in plantilla and "tu-correo@gmail.com" in plantilla
  assert not re.search(r"client_secret\s*=\s*\"GOCSPX", plantilla)
