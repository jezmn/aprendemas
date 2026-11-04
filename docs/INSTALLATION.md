# Installation

## Prerequisites

- Python 3.11+
- Node.js 22+ and pnpm

To compile `llama-cpp-python` from source (cross-CPU), see [docs/BUILDING.md](BUILDING.md).

## Development

```bash
git clone https://github.com/jezmn/aprendemas.git
cd aprendemas

# Backend
python -m venv venv
venv\Scripts\activate
pip install --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu -r requirements.txt

# Frontend
cd chat
pnpm install
pnpm run build
cd ..

# Place a .gguf model in model/ (see docs/MODEL.md)
python main.py
```

The app builds the frontend, starts the server on `http://127.0.0.1:5050`.

### Voices

```bash
# English (~78 MB)
curl -L -o voices/en_US-libritts_r-medium.onnx      https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx
curl -L -o voices/en_US-libritts_r-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx.json
```

The reader button only appears if a model exists in `voices/`.
Any Piper voice works; the language is read from the model's config.

## Cross-CPU compatibility

Prebuilt `llama-cpp-python` wheels may use AVX512 and crash on older CPUs. See [docs/BUILDING.md](BUILDING.md).
