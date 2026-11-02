"""Local text-to-speech with Piper (in-process, offline).

Models are `*.onnx` + `*.onnx.json` pairs in `voices/` (next to the app) or
`~/.local/share/piper-voices`; the language comes from the model config or
filename prefix.
"""

import hashlib
import json
import os
import sys
import threading

from piper import PiperVoice, SynthesisConfig

from config import _get_data_dir

_VOICE_DIRS = [os.path.join(_get_data_dir(), "voices")]
if getattr(sys, "frozen", False):
    _VOICE_DIRS.append(os.path.join(getattr(sys, "_MEIPASS", ""), "voices"))
_PIPER_SHARE = os.path.expanduser("~/.local/share/piper-voices")

# espeak-ng data override for PyInstaller builds
_ESPEAK_DATA = os.environ.get("PIPER_ESPEAK_DATA") or None

_cache_lock = threading.Lock()
_cache: dict[str, tuple[bytes, int]] = {}
_cache_limit = 128

_models: dict[str, str] | None = None
_loaded: dict[str, PiperVoice] = {}


def _language_of(onnx_path: str) -> str | None:
    """Language code ("en", "es") of a model, from its config or filename."""
    try:
        with open(onnx_path + ".json", encoding="utf-8") as f:
            code = (json.load(f).get("language") or {}).get("code")
        if code:
            return code.split("_")[0].split("-")[0].lower()
    except Exception:  # noqa: S110, BLE001 - a malformed config falls back to the filename
        pass
    name = os.path.basename(onnx_path)
    prefix = name.split("_", 1)[0]
    return prefix.lower() if len(prefix) == 2 else None


def discover() -> dict[str, str]:
    """Map of language -> model path. Rescans if a new model shows up."""
    global _models
    with _cache_lock:
        if _models is None:
            found: dict[str, str] = {}
            for directory in (*_VOICE_DIRS, _PIPER_SHARE):
                if not os.path.isdir(directory):
                    continue
                for name in sorted(os.listdir(directory)):
                    if not name.endswith(".onnx"):
                        continue
                    path = os.path.join(directory, name)
                    if not os.path.exists(path + ".json"):
                        continue
                    lang = _language_of(path)
                    if lang and lang not in found:
                        found[lang] = path
            _models = found
    return dict(_models)


def available_langs() -> list[str]:
    return sorted(discover())


def _voice_for(lang: str) -> PiperVoice | None:
    """Loaded voice for a language, falling back to any installed voice."""
    models = discover()
    if not models:
        return None
    path = models.get(lang) or models.get("en") or next(iter(models.values()))
    with _cache_lock:
        if path in _loaded:
            return _loaded[path]
    kwargs = {"espeak_data_dir": _ESPEAK_DATA} if _ESPEAK_DATA else {}
    voice = PiperVoice.load(path, **kwargs)  # type: ignore[arg-type]
    with _cache_lock:
        _loaded[path] = voice
    return voice


# Speaking rate: >1 sounds slower, <1 faster
_LENGTH_SCALE = float(os.environ.get("PIPER_LENGTH_SCALE", "1.2"))


def synth(text: str, lang: str = "en") -> tuple[bytes, int] | None:
    """Synthesize speech. Returns (16-bit mono PCM, sample_rate) or None."""
    text = (text or "").strip()
    if not text:
        return None

    key = hashlib.md5(f"{lang}:{text}".encode()).hexdigest()
    with _cache_lock:
        cached = _cache.get(key)
    if cached is not None:
        return cached

    voice = _voice_for(lang)
    if voice is None:
        return None

    pcm = bytearray()
    sample_rate = voice.config.sample_rate
    try:
        config = SynthesisConfig(length_scale=_LENGTH_SCALE)
        for chunk in voice.synthesize(text, syn_config=config):
            pcm.extend(chunk.audio_int16_bytes)
            sample_rate = chunk.sample_rate or sample_rate
    except Exception:  # noqa: BLE001
        return None
    if not pcm:
        return None

    result = (bytes(pcm), sample_rate)
    with _cache_lock:
        if len(_cache) >= _cache_limit:
            _cache.clear()
        _cache[key] = result
    return result
