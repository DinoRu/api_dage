"""Application configuration."""

import secrets
from typing import Literal, Optional
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

from pydantic import (
    Field,
    PostgresDsn,
    field_validator,
    computed_field,
    AnyHttpUrl,
    model_validator
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # ===== APPLICATION =====
    APP_NAME: str = Field(
        default="Meter Reading API",
        description="Nom de l'application"
    )
    APP_VERSION: str = Field(
        default="1.0.0",
        description="Version de l'application"
    )
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environnement d'exécution"
    )
    DEBUG: bool = Field(
        default=False,
        description="Mode debug"
    )
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="Préfixe de l'API"
    )
    API_V2_PREFIX: str = Field(
        default="/api/v2",
        description="Préfixe de l'API"
    )
    # ===== SECURITY =====
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Clé secrète pour JWT et encryption"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="Algorithme de hachage JWT"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        description="Durée de validité du token d'accès (minutes)"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        description="Durée de validité du token de rafraîchissement (jours)"
    )
    
    # ===== PASSWORD HASHING =====
    PWD_SCHEME: str = Field(
        default="bcrypt",
        description="Schéma de hachage des mots de passe"
    )
    PWD_DEPRECATED: str = Field(
        default="auto",
        description="Schémas dépréciés"
    )
    
    # ===== CORS =====
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",

        ],
        description="Liste des origines autorisées pour CORS"
    )
    
    # ===== GEOLOCATION =====
    GEOLOCATION_REQUIRED: bool = Field(
        default=True,
        description="Rendre la géolocalisation obligatoire pour les lectures"
    )
    GEOLOCATION_STRICT_VALIDATION: bool = Field(
        default=False,
        description="Validation stricte de la distance lecture-compteur"
    )
    GEOLOCATION_MAX_DISTANCE: int = Field(
        default=500,
        ge=10,
        le=5000,
        description="Distance maximale autorisée entre lecture et compteur (mètres)"
    )
    GEOLOCATION_IP_FALLBACK: bool = Field(
        default=True,
        description="Utiliser l'IP comme fallback si GPS non disponible"
    )
        
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)
    
    # ===== DATABASE =====
    DB_HOST: str = Field(
        default="localhost",
        description="Hôte de la base de données"
    )
    DB_PORT: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="Port de la base de données"
    )
    DB_USER: str = Field(
        ...,
        description="Utilisateur de la base de données"
    )
    DB_PASS: str = Field(
        ...,
        description="Mot de passe de la base de données"
    )
    DB_NAME: str = Field(
        ...,
        description="Nom de la base de données"
    )
    
    # Options de connexion DB
    DB_POOL_SIZE: int = Field(
        default=5,
        ge=1,
        description="Taille du pool de connexions"
    )
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        description="Nombre maximum de connexions supplémentaires"
    )
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
        description="Timeout du pool (secondes)"
    )
    DB_POOL_RECYCLE: int = Field(
        default=3600,
        ge=1,
        description="Durée de recyclage des connexions (secondes)"
    )
    DB_ECHO: bool = Field(
        default=False,
        description="Afficher les requêtes SQL"
    )
    
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL."""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Construct synchronous database URL for Alembic."""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    # ===== TEST DATABASE =====
    TEST_DB_NAME: Optional[str] = Field(
        default=None,
        description="Nom de la base de données de test"
    )
    
    @computed_field
    @property
    def TEST_DATABASE_URL(self) -> Optional[str]:
        """Construct test database URL."""
        if self.TEST_DB_NAME:
            return (
                f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.TEST_DB_NAME}"
            )
        return None
    
    # ===== AWS S3 =====
    S3_ENABLED: bool = Field(
        default=True,
        description="Activer le stockage S3"
    )
    S3_ENDPOINT_URL: Optional[str] = Field(
        default=None,
        description="URL de l'endpoint S3 (pour MinIO local)"
    )
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default=None,
        description="ID de clé d'accès AWS"
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None,
        description="Clé d'accès secrète AWS"
    )
    S3_BUCKET_NAME: Optional[str] = Field(
        default=None,
        description="Nom du bucket S3"
    )
    AWS_REGION: str = Field(
        default="ru-1",
        description="Région AWS"
    )
    S3_PUBLIC_URL: Optional[str] = Field(
        default=None,
        description="URL publique du CDN S3"
    )
    
    # Dossiers S3
    S3_FOLDER_READINGS: str = Field(
        default="readings",
        description="Dossier pour les photos de lectures"
    )
    S3_FOLDER_AVATARS: str = Field(
        default="avatars",
        description="Dossier pour les avatars"
    )
    
    # Limites de fichiers
    MAX_UPLOAD_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1,
        description="Taille maximale d'upload (bytes)"
    )
    ALLOWED_IMAGE_TYPES: list[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        description="Types MIME d'images autorisés"
    )
    
    @model_validator(mode="after")
    def validate_s3_config(self):
        if self.S3_ENABLED:
            missing = []
            if not self.AWS_ACCESS_KEY_ID:
                missing.append("AWS_ACCESS_KEY_ID")
            if not self.AWS_SECRET_ACCESS_KEY:
                missing.append("AWS_SECRET_ACCESS_KEY")
            if not self.S3_BUCKET_NAME:
                missing.append("S3_BUCKET_NAME")
            if missing:
                raise ValueError(
                    f"S3 est activé mais les champs suivants sont manquants: "
                    f"{', '.join(missing)}"
                )
        return self
    
    @computed_field
    @property
    def S3_BASE_URL(self) -> str:
        """Construct S3 base URL."""
        if self.S3_PUBLIC_URL:
            return self.S3_PUBLIC_URL
        if self.S3_ENDPOINT_URL:
            return f"{self.S3_ENDPOINT_URL}/{self.S3_BUCKET_NAME}"
        return f"https://{self.S3_BUCKET_NAME}.s3.{self.AWS_REGION}.amazonaws.com"
    
    # ===== EMAIL (optionnel) =====
    SMTP_ENABLED: bool = Field(
        default=False,
        description="Activer l'envoi d'emails"
    )
    SMTP_HOST: Optional[str] = Field(
        default=None,
        description="Hôte SMTP"
    )
    SMTP_PORT: int = Field(
        default=587,
        ge=1,
        le=65535,
        description="Port SMTP"
    )
    SMTP_USER: Optional[str] = Field(
        default=None,
        description="Utilisateur SMTP"
    )
    SMTP_PASSWORD: Optional[str] = Field(
        default=None,
        description="Mot de passe SMTP"
    )
    SMTP_TLS: bool = Field(
        default=True,
        description="Utiliser TLS"
    )
    EMAILS_FROM_EMAIL: Optional[str] = Field(
        default=None,
        description="Email expéditeur"
    )
    EMAILS_FROM_NAME: Optional[str] = Field(
        default=None,
        description="Nom de l'expéditeur"
    )
    
    # ===== REDIS (optionnel pour cache) =====
    REDIS_ENABLED: bool = Field(
        default=False,
        description="Activer Redis pour le cache"
    )
    REDIS_HOST: str = Field(
        default="localhost",
        description="Hôte Redis"
    )
    REDIS_PORT: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Port Redis"
    )
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="Mot de passe Redis"
    )
    REDIS_DB: int = Field(
        default=0,
        ge=0,
        description="Numéro de base de données Redis"
    )
    
    @computed_field
    @property
    def REDIS_URL(self) -> Optional[str]:
        """Construct Redis URL."""
        if not self.REDIS_ENABLED:
            return None
        if self.REDIS_PASSWORD:
            return (
                f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:"
                f"{self.REDIS_PORT}/{self.REDIS_DB}"
            )
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ===== LOGGING =====
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Niveau de logging"
    )
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Format des logs"
    )
    
    # ===== RATE LIMITING =====
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Activer le rate limiting"
    )
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        ge=1,
        description="Nombre de requêtes autorisées par minute"
    )
    
    # ===== PAGINATION =====
    DEFAULT_PAGE_SIZE: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Taille de page par défaut"
    )
    MAX_PAGE_SIZE: int = Field(
        default=1000,
        ge=1,
        description="Taille de page maximale"
    )
    
    # ===== SUPER ADMIN =====
    FIRST_SUPERUSER_USERNAME: str = Field(
        default="admin",
        description="Username du premier super admin"
    )
    FIRST_SUPERUSER_PASSWORD: str = Field(
        default="changeme",
        description="Mot de passe du premier super admin"
    )
    FIRST_SUPERUSER_FULL_NAME: str = Field(
        default="Super Admin",
        description="Nom complet du premier super admin"
    )
    
    # ===== PYDANTIC CONFIG =====
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        validate_assignment=True
    )
    
    # ===== COMPUTED PROPERTIES =====
    @computed_field
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"
    
    @computed_field
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"
    
    @computed_field
    @property
    def is_staging(self) -> bool:
        """Check if running in staging mode."""
        return self.ENVIRONMENT == "staging"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Instance globale
settings = get_settings()