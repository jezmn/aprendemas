import asyncio
from typing import Optional
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from core.tts import available_langs, synth

router = APIRouter(prefix="/tts", tags=["tts"])


@router.get("/status")
def tts_status():
    """Whether speech is possible at all, and which languages are installed."""
    langs = available_langs()
    return {"available": bool(langs), "voices": langs}


def _form_field(body: bytes, name: str, default: str) -> str:
    """Read a x-www-form-urlencoded field sent by the frontend."""
    parsed = parse_qs(body.decode("utf-8", "replace"), keep_blank_values=True)
    values = parsed.get(name)
    return (values[0] if values and values[0] else default) or default


@router.post("/stream")
async def stream_tts(request: Request):
    """Raw 16-bit mono PCM. The real sample rate travels in X-Sample-Rate."""
    body = await request.body()
    text = _form_field(body, "text", "")
    lang = _form_field(body, "lang", "en")

    if not available_langs():
        raise HTTPException(status_code=404, detail="No voice models installed")

    result: Optional[tuple[bytes, int]] = await asyncio.to_thread(synth, text, lang)
    if not result:
        raise HTTPException(status_code=503, detail="Synthesis failed")

    raw, sample_rate = result

    async def body():
        chunk = 4096
        for i in range(0, len(raw), chunk):
            yield raw[i : i + chunk]
            await asyncio.sleep(0)

    return StreamingResponse(
        body(),
        media_type="audio/pcm",
        headers={"X-Sample-Rate": str(sample_rate)},
    )
