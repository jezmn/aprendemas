# Project structure

```txt
aprendemas/
├── api/          # FastAPI endpoints
├── chat/         # Svelte frontend (src/ source, dist/ built)
├── config/       # prompt templates and settings
├── core/         # LLM engine, prompt building
├── database/     # SQLite chat repository
├── docs/         # documentation
├── model/        # place your .gguf here (empty in release)
├── schemas/      # Pydantic request/response models
├── voices/       # Piper voice models (git-ignored)
├── main.py       # app entry point
├── config.py     # paths and defaults
└── AprendeMas.spec # PyInstaller build spec
```
