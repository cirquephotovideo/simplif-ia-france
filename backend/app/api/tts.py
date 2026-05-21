"""Synthèse vocale (proxy ElevenLabs)."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, AuditLog
from ..core.security import get_current_user
from ..services import tts as tts_service

router = APIRouter()


class TtsIn(BaseModel):
    text: str
    voice_id: str | None = None


@router.post("/synthesize")
async def synthesize(
    data: TtsIn,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if len(data.text) > 5000:
        raise HTTPException(status_code=413, detail="Texte trop long (max 5000 chars)")
    audio = await tts_service.synthesize(data.text, data.voice_id)
    if not audio:
        raise HTTPException(status_code=503, detail="Service TTS non configuré (ELEVENLABS_API_KEY manquant)")
    db.add(AuditLog(action="tts.synthesize", actor_id=current.id, payload={"len": len(data.text)}))
    return Response(content=audio, media_type="audio/mpeg")
