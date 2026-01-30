## backend_py/app/config.py
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from redis import Redis
# FIX: Import ClientOptions
from supabase import Client, create_client, ClientOptions


# Always load .env from the backend_py directory
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        # Core
        self.port: int = int(os.getenv("PORT", "3001"))
        self.node_env: str = os.getenv("NODE_ENV", "development")

        # Supabase
        self.supabase_url: str = os.getenv("SUPABASE_URL", "")
        self.supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
        self.supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

        if not self.supabase_url:
            raise RuntimeError("SUPABASE_URL environment variable is required")
        if not self.supabase_anon_key:
            raise RuntimeError("SUPABASE_ANON_KEY environment variable is required")

        # Email (Mailgun)
        self.mailgun_api_key: str = os.getenv("MAILGUN_API_KEY", "")
        self.mailgun_domain: str = os.getenv("MAILGUN_DOMAIN", "")
        self.mail_from_address: str = os.getenv(
            "MAIL_FROM_ADDRESS", f"noreply@{self.mailgun_domain}" if self.mailgun_domain else "noreply@example.com"
        )
        self.mail_from_name: str = os.getenv("MAIL_FROM_NAME", "admin")

        self.app_url: str = os.getenv("APP_URL", os.getenv("RENDER_EXTERNAL_URL", "http://localhost:3001"))
        
        # For CORS, we need the Frontend URL
        self.cors_origin: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

        # Redis / Queue
        self.redis_host: str = os.getenv("REDIS_HOST", "127.0.0.1")
        self.redis_port: int = int(os.getenv("REDIS_PORT", "6379"))

        # OpenAI
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")

        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


@lru_cache()
def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache()
def get_supabase_admin_client() -> Client | None:
    settings = get_settings()
    if not settings.supabase_service_role_key:
        return None
    
    # FIX: Use ClientOptions Object instead of a Dictionary
    options = ClientOptions(
        auto_refresh_token=False,
        persist_session=False
    )
    
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=options,
    )


@lru_cache()
def get_redis_connection() -> Redis:
    settings = get_settings()
    return Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=False)