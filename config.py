import os
import sys


def _get_data_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


MODEL_DIR = os.path.join(_get_data_dir(), "model")
DATABASE_PATH = os.path.join(_get_data_dir(), "aprendemas_chat.db")
DEFAULT_PORT = 5050

# Model selection: set APRENDEMAS_MODEL env var to a substring of the .gguf filename
# Example: set APRENDEMAS_MODEL=gemma to load google_gemma-3-4b-it-Q4_K_M.gguf
APRENDEMAS_MODEL = os.environ.get("APRENDEMAS_MODEL", "")
