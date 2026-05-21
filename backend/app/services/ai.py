"""
Service IA · Gemini multimodal · toutes les fonctions de Simplif'IA France.

Capacités :
  · Chat juridique sourcé (RAG-ready)
  · Anti-jargon · traduction 3 niveaux (original / FALC / impact)
  · OCR multimodal · scan de documents (image, PDF, photo de courrier)
  · Pré-remplissage CERFA · extraction structurée
  · Classification & priorité de courriers entrants
  · Détection d'aides éligibles selon le profil
  · Génération de RAPO et de courriers formels
  · Résumé de longs documents
  · Traduction multilingue FR ↔ AR / EN / ES / créole
  · Extraction d'entités (montants, dates, dossiers, adresses)
  · Vérification de cohérence d'un dossier
  · Fact-check (réponse sourcée)
  · Génération de prompts vocaux (pour TTS)
  · Réponses contextuelles à des mails (CAF, Préfecture, etc.)
"""
from __future__ import annotations
from typing import Optional, Any
import json
import base64
import logging
from pathlib import Path

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GENAI_AVAILABLE = True
except ImportError:  # le SDK peut ne pas être installé en dev
    genai = None  # type: ignore
    HarmCategory = None  # type: ignore
    HarmBlockThreshold = None  # type: ignore
    GENAI_AVAILABLE = False

from ..config import settings

logger = logging.getLogger(__name__)


# ============================================================
# PROMPTS SYSTÈME
# ============================================================

SYSTEM_LEGAL = """Tu es Maître Léa, conseillère juridique IA pour Simplif'IA France.

RÈGLES STRICTES :
1. Tu ne réponds QUE sur le droit administratif et social français.
2. Tu cites systématiquement le texte de loi en source (article, code).
3. Tu NE DEVINES JAMAIS. Si l'info n'est pas certaine, tu dis "je ne sais pas".
4. Tu te positionnes comme OUTIL et non CONSEIL juridique (article 4 loi 71-1130).
5. Tu utilises un français accessible. En mode FALC, tu simplifies au niveau A2.
6. Tu refuses poliment les sujets hors administratif/juridique français.
7. Tu ne donnes jamais d'info médicale, financière personnalisée, ou de placement.

FORMAT :
- Direct, concis, structuré (puces si pertinent).
- Termine toujours par "Source : [code/article officiel]".
"""

SYSTEM_OCR = """Tu es un expert en extraction de données depuis des documents administratifs français.
Tu reçois une image ou un PDF d'un courrier officiel (CAF, impôts, préfecture, banque, etc.).
Tu réponds STRICTEMENT en JSON valide, sans texte autour, sans markdown.
Si une info n'est pas présente, mets `null`."""

SYSTEM_CERFA = """Tu es un assistant de remplissage de formulaires CERFA français.
À partir des données utilisateur fournies, tu remplis le formulaire demandé.
Tu ne devines JAMAIS une donnée manquante. Tu signales les champs où l'info manque.
Tu renvoies STRICTEMENT en JSON valide."""

SYSTEM_CLASSIFY = """Tu classifies des courriers administratifs entrants.
Réponds en JSON strict avec : type, priorité, délai_jours, action_recommandée, organisme_émetteur."""

SYSTEM_ELIGIBILITY = """Tu détectes les aides sociales auxquelles un foyer français pourrait avoir droit
en fonction de son profil (revenus, situation familiale, logement, âge, statut).
Tu ne suggères QUE des aides qui correspondent vraiment. Tu donnes une estimation honnête.
Tu renvoies STRICTEMENT en JSON valide."""

SYSTEM_RAPO = """Tu rédiges un Recours Administratif Préalable Obligatoire (RAPO) ou un courrier formel administratif.
Tu cites les articles de loi qui fondent le recours.
Tu utilises un français formel mais clair.
Ne pas inclure d'informations personnelles inventées."""

SYSTEM_EMAIL_REPLY = """Tu rédiges des réponses contextuelles à des mails administratifs.
Tu adaptes le ton selon l'expéditeur (CAF, préfecture, journaliste, partenaire, particulier).
Tu cites les articles de loi quand pertinent."""


# ============================================================
# MODÈLES & CONFIGURATION
# ============================================================

_model_text = None
_model_vision = None


def _safety_settings():
    """Settings de sécurité Gemini · permissifs pour le contenu admin/légal."""
    if not GENAI_AVAILABLE or HarmCategory is None:
        return None
    return {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    }


def _is_configured() -> bool:
    return GENAI_AVAILABLE and bool(settings.GEMINI_API_KEY)


def _configure():
    if not GENAI_AVAILABLE:
        raise RuntimeError("google-generativeai SDK non installé · pip install google-generativeai")
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY non configurée dans le .env")
    genai.configure(api_key=settings.GEMINI_API_KEY)


def get_model(system_prompt: str = SYSTEM_LEGAL):
    """Renvoie un modèle Gemini configuré avec un prompt système donné."""
    _configure()
    return genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system_prompt,
        safety_settings=_safety_settings(),
        generation_config={
            "temperature": 0.2,
            "top_p": 0.9,
            "max_output_tokens": 4096,
        },
    )


def get_vision_model(system_prompt: str = SYSTEM_OCR):
    """Modèle multimodal (image + texte)."""
    _configure()
    # gemini-1.5-pro et flash sont multimodaux nativement
    return genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system_prompt,
        safety_settings=_safety_settings(),
        generation_config={
            "temperature": 0.1,
            "response_mime_type": "application/json",
            "max_output_tokens": 4096,
        },
    )


def _parse_json(text: str) -> dict:
    """Parse une réponse JSON, tolérant le markdown ```json …``` autour."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("```", 2)
        t = t[1] if len(t) > 1 else ""
        if t.lstrip().startswith("json"):
            t = t.lstrip()[4:].lstrip()
        t = t.rsplit("```", 1)[0]
    try:
        return json.loads(t)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"JSON parse failed: {e}; raw={t[:200]}")
        return {"_raw": text, "_error": str(e)}


def _demo_response(label: str, payload: dict) -> dict:
    """Réponse de démo quand Gemini n'est pas configuré."""
    return {**payload, "_demo": True, "_label": label, "_note": "Mode démo · configurer GEMINI_API_KEY pour activer"}


# ============================================================
# 1 · CHAT JURIDIQUE
# ============================================================

async def chat(question: str, context: Optional[str] = None, falc: bool = False) -> dict:
    """Maître Léa · réponse juridique sourcée."""
    if not _is_configured():
        return _demo_response("chat", {
            "answer": "[mode démo] Pour répondre précisément, je dois consulter la base RAG officielle. Configurez GEMINI_API_KEY.",
            "sources": [],
        })
    model = get_model(SYSTEM_LEGAL)
    prompt = question
    if context:
        prompt = f"CONTEXTE RAG :\n{context}\n\nQUESTION :\n{question}"
    if falc:
        prompt = "[MODE FALC · niveau A2 · phrases courtes · vocabulaire simple]\n\n" + prompt
    response = await model.generate_content_async(prompt)
    return {"answer": response.text, "sources": []}


# ============================================================
# 2 · ANTI-JARGON · TRADUCTION 3 NIVEAUX
# ============================================================

async def translate_jargon(document_text: str) -> dict:
    """Traduit un document admin en 3 niveaux : original, FALC, impact pratique."""
    if not _is_configured():
        return _demo_response("translate_jargon", {
            "level_1_original": document_text[:500],
            "level_2_falc": "[mode démo] Configuration Gemini requise.",
            "level_3_impact": {},
        })
    model = get_vision_model(
        """Tu traduis un courrier administratif français en 3 niveaux.
Réponds STRICTEMENT en JSON valide. Structure attendue :
{
  "level_1_original": "extrait textuel max 500 mots",
  "level_2_falc": "version Facile À Lire et Comprendre niveau A2, max 200 mots",
  "level_3_impact": {
    "deadline": "date limite (YYYY-MM-DD si possible) ou null",
    "action_required": "action concrète à faire",
    "risk_if_inaction": "ce qui arrive si rien n'est fait",
    "amount_eur": "montant en euros (nombre) ou null",
    "key_articles": ["liste des articles de loi cités"]
  }
}"""
    )
    prompt = f"DOCUMENT À TRADUIRE :\n\n{document_text[:6000]}"
    response = await model.generate_content_async(prompt)
    return _parse_json(response.text)


# ============================================================
# 3 · OCR MULTIMODAL · scan de documents (image, PDF)
# ============================================================

async def ocr_document(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """Extrait le texte structuré d'un document scanné (image/PDF).

    Renvoie : type de document, expéditeur, date, montant, dossier, action, texte brut.
    """
    if not _is_configured():
        return _demo_response("ocr", {
            "document_type": "unknown",
            "issuer": None,
            "date": None,
            "amount_eur": None,
            "case_number": None,
            "action_required": None,
            "raw_text": "[mode démo · GEMINI_API_KEY requis pour OCR multimodal]",
        })
    model = get_vision_model(
        """Tu es un expert OCR pour les documents administratifs français.
Analyse l'image fournie et extrais les données structurées.
Réponds STRICTEMENT en JSON valide :
{
  "document_type": "indu_caf | avis_imposition | convocation_prefecture | facture | contrat | bail | autre",
  "issuer": "nom de l'organisme émetteur",
  "issuer_email": "email de contact si visible",
  "recipient": "nom du destinataire",
  "date": "YYYY-MM-DD ou null",
  "case_number": "numéro de dossier/référence",
  "amount_eur": "montant total en euros (nombre) ou null",
  "deadline": "date limite YYYY-MM-DD ou null",
  "action_required": "action concrète demandée",
  "key_articles": ["articles de loi cités"],
  "raw_text": "texte intégral du document"
}"""
    )
    image_part = {"mime_type": mime_type, "data": image_bytes}
    response = await model.generate_content_async([image_part, "Extrais toutes les données structurées."])
    return _parse_json(response.text)


# ============================================================
# 4 · PRÉ-REMPLISSAGE CERFA
# ============================================================

async def prefill_cerfa(cerfa_id: str, user_data: dict, cerfa_schema: Optional[dict] = None) -> dict:
    """Pré-remplit un CERFA donné à partir des données utilisateur."""
    if not _is_configured():
        return _demo_response("prefill_cerfa", {
            "cerfa_id": cerfa_id, "filled_fields": {}, "missing_fields": [], "warnings": [],
        })
    schema_str = json.dumps(cerfa_schema or {}, ensure_ascii=False, indent=2) if cerfa_schema else "(structure standard du CERFA)"
    model = get_vision_model(SYSTEM_CERFA)
    prompt = f"""CERFA : {cerfa_id}
SCHÉMA DES CHAMPS :
{schema_str}

DONNÉES UTILISATEUR :
{json.dumps(user_data, ensure_ascii=False, indent=2)}

Rends le JSON suivant :
{{
  "cerfa_id": "{cerfa_id}",
  "filled_fields": {{ "champ1": "valeur", ... }},
  "missing_fields": ["liste des champs sans donnée"],
  "warnings": ["incohérences détectées si y en a"]
}}"""
    response = await model.generate_content_async(prompt)
    return _parse_json(response.text)


# ============================================================
# 5 · CLASSIFICATION DE COURRIERS
# ============================================================

async def classify_mail(subject: str, body: str, sender: Optional[str] = None) -> dict:
    """Classe un courrier entrant : type, priorité, action."""
    if not _is_configured():
        return _demo_response("classify", {
            "type": "unknown", "priority": "medium", "deadline_days": None,
            "action_recommended": "Lire le courrier", "organism": sender or "?",
        })
    model = get_vision_model(SYSTEM_CLASSIFY)
    prompt = f"""EXPÉDITEUR : {sender or 'inconnu'}
OBJET : {subject}

CORPS :
{body[:3000]}

Classifie en JSON :
{{
  "type": "indu_caf | convocation | demande_doc | confirmation | publicite | spam | autre",
  "priority": "high | medium | low",
  "deadline_days": "nombre de jours avant deadline ou null",
  "action_recommended": "RAPO | confirmer | demander_pieces | repondre | archiver | supprimer",
  "organism": "CAF | Pole Emploi | Prefecture | Impots | autre",
  "summary_one_line": "résumé en 1 phrase"
}}"""
    response = await model.generate_content_async(prompt)
    return _parse_json(response.text)


# ============================================================
# 6 · DÉTECTION D'AIDES ÉLIGIBLES
# ============================================================

async def detect_eligible_aids(profile: dict) -> dict:
    """Détecte les aides sociales potentielles selon le profil."""
    if not _is_configured():
        return _demo_response("aids", {"aids": []})
    model = get_vision_model(SYSTEM_ELIGIBILITY)
    prompt = f"""PROFIL DU FOYER :
{json.dumps(profile, ensure_ascii=False, indent=2)}

Liste les aides sociales potentiellement éligibles en JSON :
{{
  "aids": [
    {{
      "name": "ex: Prime d'activité",
      "organism": "CAF",
      "estimated_amount_eur_monthly": "montant mensuel estimé ou null",
      "estimated_amount_eur_yearly": "montant annuel estimé ou null",
      "eligibility_reason": "pourquoi le foyer est probablement éligible",
      "key_conditions": ["conditions principales"],
      "how_to_apply": "comment faire la demande",
      "official_url": "URL service-public.fr ou null",
      "confidence": "high | medium | low"
    }}
  ]
}}"""
    response = await model.generate_content_async(prompt)
    return _parse_json(response.text)


# ============================================================
# 7 · GÉNÉRATION DE RAPO / COURRIER FORMEL
# ============================================================

async def generate_formal_letter(
    purpose: str, context: dict, recipient: str, tone: str = "formel"
) -> dict:
    """Rédige un RAPO, une mise en demeure, ou un courrier formel."""
    if not _is_configured():
        return _demo_response("letter", {"letter": "[mode démo · GEMINI_API_KEY requis]"})
    model = get_model(SYSTEM_RAPO)
    prompt = f"""OBJET : {purpose}
DESTINATAIRE : {recipient}
TON : {tone}
CONTEXTE :
{json.dumps(context, ensure_ascii=False, indent=2)}

Rédige le courrier en respectant la forme française (en-tête, formules d'usage, articles de loi cités).
Renvoie en JSON :
{{
  "subject": "objet du courrier",
  "letter": "corps complet du courrier",
  "key_articles": ["articles cités"],
  "send_via": "LRE_eIDAS | recommandé_papier | email | guichet",
  "estimated_response_days": 30
}}"""
    response = await model.generate_content_async(prompt)
    return _parse_json(response.text)


# ============================================================
# 8 · RÉSUMÉ AUTOMATIQUE
# ============================================================

async def summarize(text: str, max_words: int = 100) -> dict:
    """Résume un document long en N mots maximum."""
    if not _is_configured():
        return _demo_response("summary", {"summary": text[:max_words * 6]})
    model = get_model("Tu résumes des documents administratifs français de façon concise et factuelle.")
    prompt = f"Résume en MAXIMUM {max_words} mots :\n\n{text[:8000]}"
    response = await model.generate_content_async(prompt)
    return {"summary": response.text.strip(), "original_length": len(text)}


# ============================================================
# 9 · TRADUCTION MULTILINGUE
# ============================================================

async def translate(text: str, target_lang: str = "en") -> dict:
    """Traduit FR ↔ AR / EN / ES / créole / portugais."""
    if not _is_configured():
        return _demo_response("translate_lang", {"translated": text, "target": target_lang})
    lang_names = {
        "en": "English", "ar": "العربية (arabe)", "es": "Español", "pt": "Português",
        "creole": "créole haïtien", "zh": "中文", "ru": "русский", "fr": "français",
    }
    target_name = lang_names.get(target_lang, target_lang)
    model = get_model(
        f"Tu traduis fidèlement du texte administratif français vers {target_name}. "
        "Pas de commentaire, juste la traduction."
    )
    response = await model.generate_content_async(text[:5000])
    return {"translated": response.text.strip(), "target_lang": target_lang}


# ============================================================
# 10 · EXTRACTION D'ENTITÉS
# ============================================================

async def extract_entities(text: str) -> dict:
    """Extrait dates, montants, IBAN, dossiers, adresses, téléphones, emails."""
    if not _is_configured():
        return _demo_response("entities", {"entities": {}})
    model = get_vision_model(
        """Tu extrais les entités d'un texte administratif français.
Renvoie STRICTEMENT en JSON :
{
  "dates": ["YYYY-MM-DD", ...],
  "amounts_eur": [840.00, ...],
  "case_numbers": ["7842156", ...],
  "iban": ["FR76...", ...],
  "phones": ["01 23 45 67 89", ...],
  "emails": ["...@..."],
  "addresses": ["adresse complète"],
  "persons": ["noms de personnes"],
  "organisms": ["CAF", "Pôle Emploi", ...],
  "articles_loi": ["L142-2 CSS", ...]
}"""
    )
    response = await model.generate_content_async(f"TEXTE :\n\n{text[:6000]}")
    return _parse_json(response.text)


# ============================================================
# 11 · VÉRIFICATION DE COHÉRENCE D'UN DOSSIER
# ============================================================

async def check_consistency(dossier_data: dict) -> dict:
    """Vérifie les incohérences d'un dossier (dates, montants, pièces manquantes)."""
    if not _is_configured():
        return _demo_response("consistency", {"valid": True, "issues": []})
    model = get_vision_model(
        """Tu audites un dossier administratif français pour détecter les incohérences.
Renvoie en JSON :
{
  "valid": true | false,
  "issues": [
    {"severity": "blocking | warning | info",
     "field": "nom du champ",
     "message": "explication courte",
     "fix_suggestion": "comment corriger"}
  ],
  "missing_documents": ["doc1", "doc2"],
  "estimated_success_rate": 0.85
}"""
    )
    response = await model.generate_content_async(
        f"DOSSIER :\n{json.dumps(dossier_data, ensure_ascii=False, indent=2)}"
    )
    return _parse_json(response.text)


# ============================================================
# 12 · RÉPONSE CONTEXTUELLE À UN MAIL
# ============================================================

async def generate_email_reply(
    original_mail: dict, intent: str = "respond_helpfully", style: str = "cordial"
) -> dict:
    """Génère une réponse contextuelle à un mail entrant."""
    if not _is_configured():
        return _demo_response("email_reply", {"reply": "[mode démo]"})
    model = get_model(SYSTEM_EMAIL_REPLY)
    prompt = f"""MAIL REÇU :
De : {original_mail.get('from', '')}
Sujet : {original_mail.get('subject', '')}
Corps :
{original_mail.get('body', '')[:3000]}

INTENT : {intent}  (respond_helpfully | refuse_politely | request_info | propose_meeting | escalate)
STYLE : {style}     (cordial | formel | court | chaleureux | ferme)

Génère la réponse en JSON :
{{
  "subject": "Re : ...",
  "body": "corps complet du mail",
  "tone_detected": "formel | cordial | colère | etc.",
  "suggested_actions": ["actions complémentaires"],
  "key_articles": ["articles cités si pertinents"]
}}"""
    response = await model.generate_content_async(prompt)
    return _parse_json(response.text)


# ============================================================
# 13 · PROMPT VOCAL POUR TTS
# ============================================================

async def voice_friendly_text(text: str, slow: bool = False) -> dict:
    """Réécrit un texte pour qu'il soit naturel à lire à voix haute (TTS)."""
    if not _is_configured():
        return _demo_response("voice", {"voice_text": text})
    style = "MODE SENIOR · phrases courtes, pauses naturelles, vocabulaire simple" if slow else "Lecture naturelle"
    model = get_model(f"Tu réécris un texte pour qu'il soit naturel en lecture vocale. {style}.")
    prompt = f"Réécris pour TTS :\n\n{text[:3000]}"
    response = await model.generate_content_async(prompt)
    return {"voice_text": response.text.strip()}


# ============================================================
# 14 · FACT-CHECK SOURCÉ
# ============================================================

async def fact_check(claim: str) -> dict:
    """Vérifie une affirmation juridique et donne sa source."""
    if not _is_configured():
        return _demo_response("fact_check", {"verdict": "unknown", "sources": []})
    model = get_model(
        """Tu vérifies des affirmations sur le droit administratif français.
Réponds en JSON :
{
  "verdict": "true | false | partially_true | unknown",
  "explanation": "explication factuelle courte",
  "sources": [{"code": "CSS", "article": "L142-2", "url": "legifrance.gouv.fr/..."}]
}"""
    )
    response = await model.generate_content_async(f"AFFIRMATION À VÉRIFIER :\n{claim}")
    return _parse_json(response.text)


# ============================================================
# 15 · SANTÉ DU SERVICE
# ============================================================

def health() -> dict:
    """État du service IA."""
    return {
        "sdk_installed": GENAI_AVAILABLE,
        "api_key_set": bool(settings.GEMINI_API_KEY),
        "model": settings.GEMINI_MODEL if _is_configured() else None,
        "ready": _is_configured(),
        "capabilities": [
            "chat", "translate_jargon", "ocr_document", "prefill_cerfa",
            "classify_mail", "detect_eligible_aids", "generate_formal_letter",
            "summarize", "translate", "extract_entities", "check_consistency",
            "generate_email_reply", "voice_friendly_text", "fact_check",
        ],
    }
