# Installation

## Prerequisites

- Python 3.10+
- Node.js 18+ and pnpm
- **Windows:** Visual Studio 2022 Build Tools (to compile `llama-cpp-python`)

```powershell
winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

## Quick start (from source)

```bash
git clone https://github.com/jezmn/aprendemas.git
cd aprendemas

# Backend
python -m venv venv
venv\Scripts\activate     # Windows
pip install --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu -r requirements.txt

# Frontend
cd chat
pnpm install
pnpm run build
cd ..

# Place a .gguf model in model/ (see docs/MODEL.md)
python main.py
```

The app builds the frontend, starts the server on `http://127.0.0.1:5050`, and opens your browser.

### Voices (optional)

The reader button only appears if there is a model in `voices/`. They are
git-ignored, so a fresh clone has none — download the pair you want:

```bash
# English (~78 MB)
curl -L -o voices/en_US-libritts_r-medium.onnx      https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx
curl -L -o voices/en_US-libritts_r-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx.json

# Spanish (~63 MB)
curl -L -o voices/es_ES-mls_10246-low.onnx      https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_10246/low/es_ES-mls_10246-low.onnx
curl -L -o voices/es_ES-mls_10246-low.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_10246/low/es_ES-mls_10246-low.onnx.json
```

Any Piper voice works; the language is read from the model's config.

## Prebuilt release

1. Download the latest `AprendeMas-vX.X.X-win-x64.zip` from [Releases](https://github.com/jezmn/aprendemas/releases).
2. Unzip it. You get a folder containing `AprendeMas.exe` (the TTS engine is bundled, so it is a folder and not a single file).
3. Place the `.gguf` in `model/` (see [docs/MODEL.md](MODEL.md)).
4. Place the voice models in `voices/` (optional — without them the reader button is hidden).
5. Run `AprendeMas.exe`.

No Python, Node, or dependencies needed.

## Cross-CPU compatibility

Prebuilt `llama-cpp-python` wheels may use AVX512 and crash on older CPUs. See [docs/BUILDING.md](BUILDING.md).
