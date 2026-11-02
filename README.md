# AprendeMas

A local, offline-first English tutor powered by LLMs. Runs entirely on your machine — no internet, no data leaves your computer.

Designed for kids aged 9–12 at A1–A2 English level. Uses GGUF models via `llama-cpp-python` for grammar, vocabulary, stories, and conversation through a chat UI.

## Features

- **100% offline** — no API keys, cloud, or tracking.
- **Streaming responses** — tokens appear in real time.
- **Persistent history** — SQLite, restored on return.
- **Multiple sessions** — new/switch/delete chats.
- **Topic shortcuts** — colors, animals, numbers, stories.
- **Custom username** — stored in browser.
- **Voice reader** — reads responses aloud locally (Piper TTS).
- **Portable build** — runs from a folder, no install, via PyInstaller.

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3, FastAPI, uvicorn |
| LLM | llama-cpp-python |
| Storage | SQLite |
| Frontend | Svelte 5, Vite |
| Styling | Tailwind CSS, Lucide |
| TTS | Piper (local neural voices) |

## Quick start

```bash
git clone https://github.com/jezmn/aprendemas.git
cd aprendemas
python -m venv venv && venv\Scripts\activate
pip install --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu -r requirements.txt
cd chat && pnpm install && pnpm run build && cd ..
# place a .gguf in model/ (see docs/MODEL.md)
python main.py
```

Full instructions: [docs/INSTALLATION.md](docs/INSTALLATION.md)

## Documentation

- [Installation](docs/INSTALLATION.md)
- [Model selection](docs/MODEL.md)
- [Building (cross-CPU + release)](docs/BUILDING.md)
- [Database schema](docs/DATABASE.md)
- [Project structure](docs/STRUCTURE.md)

## Voice reader (Lector de voz)

Local neural voice (Piper TTS) reads responses aloud — 100% offline, engine in process. To add a voice, drop a Piper model pair into `voices/` (the language is read from the model's own config):

```
voices/en_US-libritts_r-medium.onnx
voices/en_US-libritts_r-medium.onnx.json
```

`voices/` is git-ignored and not bundled into the build, so voices can be swapped without rebuilding (see [docs/BUILDING.md](docs/BUILDING.md)). If no model exists, the reader button is hidden.

## License

MIT