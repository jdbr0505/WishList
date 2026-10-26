"""Configuracion de pytest: pone python/ en el camino de importacion para poder usar `logica`, `dashboards`, etc."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
