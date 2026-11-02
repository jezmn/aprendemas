# Model

For teaching English to kids on school PCs, **speed and direct responses** matter most.

Recommended: `microsoft/Phi-4-mini-instruct` (3.8B, MIT). No thinking mode → responds directly, fast (~500 MB RAM with mmap). Strong English for a kids' tutor. Toggle has no effect (no thinking generated).

GGUF: `bartowski/microsoft_Phi-4-mini-instruct-GGUF` (Q4_K_M ~2.2 GB, Q6_K ~3.16 GB).

Alternative (thinking controlable): `Qwen/Qwen3-4B` (4B, Apache 2.0). Thinking can be toggled (OFF = fast, ON = shows reasoning). Good Spanish. GGUF: `Qwen/Qwen3-4B-GGUF`.

Avoid for speed: `Omni-Edu-4B` (Qwen3.5 base). Its thinking cannot be reliably disabled — always generates reasoning (slow). Better pedagogy but high latency on CPU.

Download a single `.gguf` into `model/`. The first `.gguf` found is loaded.

- Env var to pick a specific file: `APRENDEMAS_MODEL=<substring>`

## Context

`n_ctx=1024` (reduced for speed). The startup warning about unused context is normal.
