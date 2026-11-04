# Model

Download a single `.gguf` into `model/`. The first `.gguf` found is loaded.

Recommended (pick one):
- `microsoft/Phi-4-mini-instruct` (3.8B, MIT). GGUF: `bartowski/microsoft_Phi-4-mini-instruct-GGUF` (Q4_K_M ~2.5 GB, Q6_K ~3.2 GB).
- `Qwen/Qwen3-4B` (4B, Apache 2.0). GGUF: `Qwen/Qwen3-4B-GGUF` (Q4_K_M ~2.5 GB, Q6_K ~3.3 GB).

- Env var to pick a specific file: `APRENDEMAS_MODEL=<substring>`

## Context

`n_ctx=1024`. The startup warning about unused context is normal.
