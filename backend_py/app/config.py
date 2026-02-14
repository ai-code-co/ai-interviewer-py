## backend_py/app/config.py
import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from redis import Redis


# Always load .env from the backend_py directory
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        # Core
        self.port: int = int(os.getenv("PORT", "3001"))
        self.node_env: str = os.getenv("NODE_ENV", "development")

        # TiDB / MySQL
        self.db_name: str = os.getenv("DB_NAME", "")
        self.db_user: str = os.getenv("DB_USER", "")
        self.db_password: str = os.getenv("DB_PASSWORD", "")
        self.db_host: str = os.getenv("DB_HOST", "127.0.0.1")
        self.db_port: int = int(os.getenv("DB_PORT", "3306"))
        self.database_url: str = os.getenv("DATABASE_URL", "")
        self.sqlalchemy_database_url: str = self._build_database_url()
        if not self.sqlalchemy_database_url:
            raise RuntimeError(
                "DATABASE_URL or DB_NAME/DB_USER/DB_HOST/DB_PORT environment variables are required"
            )
        db_url_lower = self.sqlalchemy_database_url.lower()
        self.db_ssl_enabled: bool = self._to_bool(
            os.getenv("DB_SSL_ENABLED"),
            default=("tidbcloud.com" in db_url_lower),
        )
        self.db_ssl_verify_cert: bool = self._to_bool(
            os.getenv("DB_SSL_VERIFY_CERT"),
            default=True,
        )
        self.db_ssl_verify_identity: bool = self._to_bool(
            os.getenv("DB_SSL_VERIFY_IDENTITY"),
            default=True,
        )
        self.db_ssl_ca: str = os.getenv("DB_SSL_CA", "")

        # Cloudinary
        self.cloudinary_cloud_name: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
        self.cloudinary_api_key: str = os.getenv("CLOUDINARY_API_KEY", "")
        self.cloudinary_api_secret: str = os.getenv("CLOUDINARY_API_SECRET", "")
        self.cloudinary_url: str = os.getenv("CLOUDINARY_URL", "")
        if not self.cloudinary_url and (
            not self.cloudinary_cloud_name or not self.cloudinary_api_key or not self.cloudinary_api_secret
        ):
            raise RuntimeError(
                "Cloudinary is not fully configured. Set CLOUDINARY_URL or CLOUDINARY_CLOUD_NAME/CLOUDINARY_API_KEY/CLOUDINARY_API_SECRET."
            )

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

    def _build_database_url(self) -> str:
        if self.database_url and self.database_url.strip():
            url = self.database_url.strip()
            if url.startswith("mysql://"):
                return "mysql+pymysql://" + url[len("mysql://") :]
            if url.startswith("mysql+mysqldb://"):
                return "mysql+pymysql://" + url[len("mysql+mysqldb://") :]
            return url
        if not self.db_name or not self.db_user:
            return ""
        encoded_user = quote_plus(self.db_user)
        encoded_password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{encoded_user}:{encoded_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @staticmethod
    def _to_bool(value: str | None, default: bool = False) -> bool:
        if value is None:
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "on"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


@lru_cache()
def get_redis_connection() -> Redis:
    settings = get_settings()
    return Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=False)
