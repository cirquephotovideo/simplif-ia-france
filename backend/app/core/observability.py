"""
Observability stack · Sentry + structured logging (Loki/Promtail-ready)

Sentry : erreurs + perf + release tracking + breadcrumbs
Loki   : logs JSON parsables · agrégation Grafana
Alertes: 5+ login fails / min sur la même IP → webhook Slack/Telegram
"""
import json
import sys
import time
from collections import defaultdict, deque
from typing import Any
from loguru import logger

from ..config import settings


# ============================================================================
# 1. Sentry initialization
# ============================================================================
def init_sentry() -> bool:
    """Initialize Sentry SDK if DSN is configured."""
    dsn = getattr(settings, "SENTRY_DSN", "") or ""
    if not dsn:
        logger.info("Sentry DSN non configuré · monitoring désactivé")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.loguru import LoguruIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=settings.APP_ENV,
            release=getattr(settings, "RELEASE_VERSION", "0.1.0"),
            traces_sample_rate=0.2 if settings.APP_ENV == "production" else 1.0,
            profiles_sample_rate=0.1,
            send_default_pii=False,  # RGPD : pas d'IP/cookies par défaut
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoguruIntegration(),
            ],
            before_send=_scrub_pii,
        )
        logger.info(f"Sentry initialisé · env={settings.APP_ENV}")
        return True
    except Exception as e:
        logger.error(f"Sentry init failed: {e}")
        return False


def _scrub_pii(event: dict, hint: dict) -> dict | None:
    """Remove PII from events before sending to Sentry."""
    # Strip query strings/cookies
    if "request" in event:
        req = event["request"]
        # Anonymize cookies
        if "cookies" in req:
            req["cookies"] = {k: "[REDACTED]" for k in req["cookies"]}
        # Anonymize headers sensibles
        for h in ("authorization", "x-csrf-token", "cookie", "x-api-key"):
            if "headers" in req and h in req["headers"]:
                req["headers"][h] = "[REDACTED]"
    # Strip emails/passwords des extras
    if "extra" in event:
        for k in list(event["extra"].keys()):
            if any(s in k.lower() for s in ("password", "token", "secret", "email")):
                event["extra"][k] = "[REDACTED]"
    return event


# ============================================================================
# 2. Structured JSON logging (Loki-ready)
# ============================================================================
def setup_structured_logging():
    """Configure loguru pour émettre du JSON parsable par Loki."""
    logger.remove()
    is_prod = settings.APP_ENV == "production"

    def json_formatter(record):
        log_obj = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "message": record["message"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
        }
        if record["exception"]:
            log_obj["exception"] = str(record["exception"])
        if record["extra"]:
            log_obj.update(record["extra"])
        return json.dumps(log_obj, ensure_ascii=False) + "\n"

    if is_prod:
        logger.add(sys.stdout, format=json_formatter, level=settings.LOG_LEVEL, serialize=False)
    else:
        logger.add(sys.stdout, level=settings.LOG_LEVEL, colorize=True)


# ============================================================================
# 3. Login failure tracker · alerte sur abuse
# ============================================================================
class LoginFailureTracker:
    """
    Track login failures par IP.
    Alerte (Slack/Telegram webhook) si >= 5 fails en 60 secondes.
    """
    def __init__(self, window_seconds: int = 60, threshold: int = 5):
        self.window = window_seconds
        self.threshold = threshold
        self.events: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
        self.alerted: dict[str, float] = {}  # IP -> dernier timestamp d'alerte

    def record_failure(self, ip: str, email: str | None = None) -> bool:
        """Returns True si on a déclenché une alerte."""
        now = time.time()
        events = self.events[ip]
        events.append(now)

        # Nettoyer events trop vieux
        while events and now - events[0] > self.window:
            events.popleft()

        if len(events) >= self.threshold:
            # Éviter de spammer : 1 alerte / 5 min max par IP
            last_alert = self.alerted.get(ip, 0)
            if now - last_alert > 300:
                self.alerted[ip] = now
                self._fire_alert(ip, len(events), email)
                return True
        return False

    def _fire_alert(self, ip: str, count: int, email: str | None):
        msg = f"🚨 BRUTE FORCE DETECTED · IP={ip} · {count} login fails in {self.window}s · email={email}"
        logger.bind(security_event=True, ip=ip, event_type="brute_force_login").warning(msg)

        # Webhook Slack/Telegram si configuré
        webhook = getattr(settings, "SECURITY_WEBHOOK_URL", None)
        if webhook:
            self._async_post_webhook(webhook, msg)

    def _async_post_webhook(self, url: str, message: str):
        """Fire-and-forget webhook (Slack/Telegram)."""
        try:
            import httpx
            httpx.post(url, json={"text": message}, timeout=3.0)
        except Exception as e:
            logger.error(f"Security webhook failed: {e}")


login_failure_tracker = LoginFailureTracker()
