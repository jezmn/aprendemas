import os
import subprocess
import sys
import threading
import time
import webbrowser
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.endpoints import router as api_router
from api.tts_endpoints import router as tts_router
from config import DATABASE_PATH, DEFAULT_PORT, MODEL_DIR
from core.chat_engine import ChatEngine
from database.chat_repository import ChatRepository

BANNER = "\n  AprendeMas\n"


def get_base_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", "")  # present whenever frozen
    return os.path.dirname(os.path.abspath(__file__))


def open_browser_after_start(port: int, delay: float = 3.0):
    def _open():
        time.sleep(delay)
        url = f"http://127.0.0.1:{port}"
        try:
            if os.name == "nt":
                os.startfile(url)  # Windows: silent
            else:
                # Detached with stdio discarded: Chromium leaks zygote noise otherwise
                try:
                    subprocess.Popen(
                        ["xdg-open", url],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                except FileNotFoundError:
                    webbrowser.open(url)
        except Exception:  # noqa: BLE001 - opening the browser must never crash the app
            webbrowser.open(url)

    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.chat_engine = ChatEngine(MODEL_DIR)
    app.state.chat_repository = ChatRepository(DATABASE_PATH)
    app.state.model_name = app.state.chat_engine.model_name

    # Warm up models in the background so the first request is not slow.
    def _warmup():
        try:
            from core.tts import available_langs, synth

            if available_langs():
                synth("hi", "en")
        except Exception:  # noqa: BLE001
            pass
    threading.Thread(target=_warmup, daemon=True).start()

    yield


app = FastAPI(
    title="AprendeMas",
    description="Chatbot persistente con LLM y SQLite",
    version="1.0.0",
    lifespan=lifespan,
)

BASE_DIR = get_base_dir()
FRONTEND_DIR = os.path.join(BASE_DIR, "chat", "dist")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(tts_router, prefix="/api")


@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok", "model": getattr(app.state, "model_name", "not loaded")}


if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")


if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    print(BANNER)
    print("-" * 50)
    if not getattr(sys, "frozen", False):
        print("[*] Construyendo frontend...")
        frontend_dir = os.path.join(BASE_DIR, "chat")
        pkg_json = os.path.join(frontend_dir, "package.json")
        if os.path.exists(pkg_json) and os.path.exists(
            os.path.join(frontend_dir, "node_modules")
        ):
            subprocess.run(["pnpm", "run", "build"], cwd=frontend_dir, check=False)
    print(f"[*] Iniciando servidor en el puerto {DEFAULT_PORT}")
    open_browser_after_start(DEFAULT_PORT)
    print("-" * 50)
    print("[OK] AprendeMas esta listo! Abriendo navegador...")
    print(f"     http://127.0.0.1:{DEFAULT_PORT}")
    print("-" * 50)
    print("     Cierra esta ventana cuando quieras salir\n")
    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT)
