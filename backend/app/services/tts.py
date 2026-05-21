"""Proxy ElevenLabs (TTS premium)."""
import httpx
from ..config import settings


async def synthesize(text: str, voice_id: str | None = None) -> bytes:
    """Renvoie un audio MP3 généré par ElevenLabs.
    Retourne `b''` si la clé n'est pas configurée (fallback côté client → voix navigateur).
    """
    if not settings.ELEVENLABS_API_KEY:
        return b""

    voice = voice_id or settings.ELEVENLABS_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    body = {
        "text": text[:5000],
        "model_id": settings.ELEVENLABS_MODEL,
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.75,
            "style": 0.25,
            "use_speaker_boost": True,
        },
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        return r.content
