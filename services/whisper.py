from services.groq_client import groq
from config import MODEL_WHISPER
from pathlib import Path


async def transcribe(path: str) -> str:
    with open(path, "rb") as f:
        result = await groq.audio.transcriptions.create(
            model=MODEL_WHISPER,
            file=(Path(path).name, f.read()),
            language="ru",
        )
    return getattr(result, "text", None) or str(result)
