"""API IA · Gemini multimodal · Simplif'IA France.

Routes exposées :
  POST /ai/chat               · Maître Léa · chat juridique sourcé
  POST /ai/translate-jargon   · Traduction 3 niveaux (original/FALC/impact)
  POST /ai/ocr                · OCR multimodal d'un document scanné
  POST /ai/cerfa/prefill      · Pré-remplissage d'un CERFA
  POST /ai/classify-mail      · Classification d'un courrier entrant
  POST /ai/detect-aids        · Détection d'aides éligibles
  POST /ai/letter             · Génération RAPO / courrier formel
  POST /ai/summarize          · Résumé d'un texte long
  POST /ai/translate          · Traduction multilingue
  POST /ai/extract-entities   · Extraction d'entités structurées
  POST /ai/check-consistency  · Audit de cohérence d'un dossier
  POST /ai/email-reply        · Réponse contextuelle à un mail
  POST /ai/voice-text         · Texte adapté pour TTS
  POST /ai/fact-check         · Vérification factuelle sourcée
  GET  /ai/health             · Statut du service
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, AuditLog
from ..core.security import get_current_user
from ..services import ai as ai_service

router = APIRouter()


# ============================================================
# SCHEMAS
# ============================================================

class ChatIn(BaseModel):
    question: str
    falc: bool = False
    context: Optional[str] = None


class TranslateJargonIn(BaseModel):
    text: str


class CerfaPrefillIn(BaseModel):
    cerfa_id: str
    user_data: dict[str, Any]
    cerfa_schema: Optional[dict[str, Any]] = None


class ClassifyMailIn(BaseModel):
    subject: str
    body: str
    sender: Optional[str] = None


class DetectAidsIn(BaseModel):
    profile: dict[str, Any] = Field(..., description="rfr, situation, foyer, age, logement, statut, etc.")


class FormalLetterIn(BaseModel):
    purpose: str
    context: dict[str, Any]
    recipient: str
    tone: str = "formel"


class SummarizeIn(BaseModel):
    text: str
    max_words: int = 100


class TranslateIn(BaseModel):
    text: str
    target_lang: str = "en"


class ExtractEntitiesIn(BaseModel):
    text: str


class CheckConsistencyIn(BaseModel):
    dossier_data: dict[str, Any]


class EmailReplyIn(BaseModel):
    original_mail: dict[str, Any]
    intent: str = "respond_helpfully"
    style: str = "cordial"


class VoiceTextIn(BaseModel):
    text: str
    slow: bool = False


class FactCheckIn(BaseModel):
    claim: str


# ============================================================
# UTIL · audit log
# ============================================================

async def _audit(db: AsyncSession, action: str, user: User, payload: dict | None = None):
    db.add(AuditLog(action=action, actor_id=user.id, payload=payload or {}))


# ============================================================
# ROUTES
# ============================================================

@router.get("/health")
async def health():
    return ai_service.health()


@router.post("/chat")
async def chat(data: ChatIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.chat(data.question, data.context, falc=data.falc)
    await _audit(db, "ai.chat", current, {"len": len(data.question), "falc": data.falc})
    return response


@router.post("/translate-jargon")
async def translate_jargon(data: TranslateJargonIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.translate_jargon(data.text)
    await _audit(db, "ai.translate_jargon", current, {"len": len(data.text)})
    return response


@router.post("/ocr")
async def ocr(
    file: UploadFile = File(...),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """OCR multimodal d'un document scanné · accepte image/jpg, png, pdf."""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB max
        raise HTTPException(413, "Fichier trop volumineux (max 10 MB)")
    mime = file.content_type or "image/jpeg"
    response = await ai_service.ocr_document(content, mime_type=mime)
    await _audit(db, "ai.ocr", current, {"filename": file.filename, "size": len(content)})
    return response


@router.post("/cerfa/prefill")
async def cerfa_prefill(data: CerfaPrefillIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.prefill_cerfa(data.cerfa_id, data.user_data, data.cerfa_schema)
    await _audit(db, "ai.cerfa_prefill", current, {"cerfa_id": data.cerfa_id})
    return response


@router.post("/classify-mail")
async def classify_mail(data: ClassifyMailIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.classify_mail(data.subject, data.body, data.sender)
    await _audit(db, "ai.classify_mail", current)
    return response


@router.post("/detect-aids")
async def detect_aids(data: DetectAidsIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.detect_eligible_aids(data.profile)
    await _audit(db, "ai.detect_aids", current)
    return response


@router.post("/letter")
async def letter(data: FormalLetterIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.generate_formal_letter(data.purpose, data.context, data.recipient, data.tone)
    await _audit(db, "ai.letter", current, {"purpose": data.purpose})
    return response


@router.post("/summarize")
async def summarize(data: SummarizeIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.summarize(data.text, max_words=data.max_words)
    await _audit(db, "ai.summarize", current, {"len": len(data.text)})
    return response


@router.post("/translate")
async def translate(data: TranslateIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.translate(data.text, target_lang=data.target_lang)
    await _audit(db, "ai.translate", current, {"target": data.target_lang})
    return response


@router.post("/extract-entities")
async def extract_entities(data: ExtractEntitiesIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.extract_entities(data.text)
    await _audit(db, "ai.extract_entities", current)
    return response


@router.post("/check-consistency")
async def check_consistency(data: CheckConsistencyIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.check_consistency(data.dossier_data)
    await _audit(db, "ai.check_consistency", current)
    return response


@router.post("/email-reply")
async def email_reply(data: EmailReplyIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.generate_email_reply(data.original_mail, data.intent, data.style)
    await _audit(db, "ai.email_reply", current, {"intent": data.intent})
    return response


@router.post("/voice-text")
async def voice_text(data: VoiceTextIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.voice_friendly_text(data.text, slow=data.slow)
    await _audit(db, "ai.voice_text", current, {"slow": data.slow})
    return response


@router.post("/fact-check")
async def fact_check(data: FactCheckIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await ai_service.fact_check(data.claim)
    await _audit(db, "ai.fact_check", current)
    return response
