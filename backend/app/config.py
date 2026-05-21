"""Configuration centralisée chargée depuis les variables d'environnement."""
from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    APP_NAME: str = "Simplif-IA-France"
    APP_ENV: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    CORS_ORIGINS: str = "http://localhost:8080"

    # Database
    DATABASE_URL: str
    POSTGRES_USER: str = "simplifia"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "simplifia"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT
    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # Encryption
    MASTER_ENCRYPTION_KEY: str = Field(..., min_length=44)

    # Admin initial
    ADMIN_EMAIL: str = "admin@simplif-ia.fr"
    ADMIN_PASSWORD: str = ""
    ADMIN_FIRST_NAME: str = "Admin"
    ADMIN_LAST_NAME: str = "Simplifia"

    # IA
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro-latest"

    # TTS
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "XB0fDUnXU5powFXDhCwa"
    ELEVENLABS_MODEL: str = "eleven_multilingual_v2"

    # APIs Gouv
    API_BAN_URL: str = "https://api-adresse.data.gouv.fr"
    API_SIRENE_URL: str = "https://recherche-entreprises.api.gouv.fr"
    API_ANNUAIRE_URL: str = "https://api-lannuaire.service-public.gouv.fr"
    API_GEO_URL: str = "https://geo.api.gouv.fr"

    # Légifrance
    LEGIFRANCE_CLIENT_ID: str = ""
    LEGIFRANCE_CLIENT_SECRET: str = ""

    # AR24
    AR24_API_KEY: str = ""
    AR24_API_URL: str = "https://app.ar24.fr/api"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@simplif-ia.fr"

    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_PATH: str = "/app/storage"
    S3_BUCKET: str = ""
    S3_REGION: str = "fr-par"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_ENDPOINT: str = ""

    # === Security v2 ===
    # Cookies sécurité (Secure=True force HTTPS, à laisser True en prod)
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: str = "lax"        # "strict" si pas de redirections OAuth
    COOKIE_DOMAIN: str = ""              # Vide = host courant (recommandé)

    # CSRF
    CSRF_ENABLED: bool = True

    # hCaptcha (https://dashboard.hcaptcha.com)
    HCAPTCHA_SITEKEY: str = ""
    HCAPTCHA_SECRET: str = ""
    HCAPTCHA_REQUIRED_ROUTES: str = "register,password-reset,lre-send,contact"

    # Sentry monitoring
    SENTRY_DSN: str = ""
    RELEASE_VERSION: str = "0.1.0"

    # Webhooks d'alerte sécurité (Slack/Telegram)
    SECURITY_WEBHOOK_URL: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
