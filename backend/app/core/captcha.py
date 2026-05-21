"""
hCaptcha verification · anti-bot sur endpoints sensibles
- Inscription
- Reset mot de passe
- Envoi de LRE (potentiellement payant)
- Création de ticket support
"""
import httpx
from fastapi import HTTPException, Request
from loguru import logger

from ..config import settings

HCAPTCHA_VERIFY_URL = "https://api.hcaptcha.com/siteverify"


async def verify_hcaptcha(token: str, request: Request) -> bool:
    """
    Vérifie un token hCaptcha auprès du serveur.
    Returns True si valide, raise HTTPException sinon.
    """
    # En dev / si pas configuré, on bypass (ne pas bloquer le dev)
    if not getattr(settings, "HCAPTCHA_SECRET", None):
        if settings.APP_ENV == "production":
            logger.error("HCAPTCHA_SECRET manquant en production · captcha désactivé")
        return True

    if not token:
        raise HTTPException(status_code=400, detail="Captcha requis")

    ip = request.client.host if request.client else None

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.post(
                HCAPTCHA_VERIFY_URL,
                data={
                    "secret": settings.HCAPTCHA_SECRET,
                    "response": token,
                    "remoteip": ip,
                },
            )
            data = resp.json()
        except Exception as e:
            logger.error(f"hCaptcha verify error: {e}")
            # En cas d'indisponibilité hCaptcha, on laisse passer mais on log
            return True

    if not data.get("success"):
        codes = data.get("error-codes", [])
        logger.warning(f"hCaptcha failed · codes={codes} ip={ip}")
        raise HTTPException(status_code=400, detail="Captcha invalide")

    # Score-based (hCaptcha Enterprise)
    score = data.get("score")
    if score is not None and score < 0.5:
        logger.warning(f"hCaptcha low score · {score} ip={ip}")
        raise HTTPException(status_code=400, detail="Activité suspecte détectée")

    return True
