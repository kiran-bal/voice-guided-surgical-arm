import os
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "application"
sys.path.insert(0, str(APP))
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("LLM_MODEL", "llama3.1")
os.environ.setdefault("USE_CAMERA", "False")
os.environ.setdefault("USE_ESP32", "False")
