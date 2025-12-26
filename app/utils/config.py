"""
Configuration management using Pydantic Settings.
Loads settings from environment variables with validation.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str  # Required: set in environment

    # Security
    SECRET_KEY: str  # Required: set in environment
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI Integration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Azure Cognitive Services
    AZURE_SPEECH_KEY: Optional[str] = None
    AZURE_SPEECH_REGION: Optional[str] = None
    AZURE_KEYVAULT_URL: Optional[str] = None
    AZURE_STORAGE_ACCOUNT: Optional[str] = None
    AZURE_STORAGE_KEY: Optional[str] = None
    AZURE_STORAGE_CONTAINER: Optional[str] = "mew-backups"

    # Email Integration
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Twilio (SMS/WhatsApp)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None

    # OAuth Providers
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_TEAM_ID: Optional[str] = None
    APPLE_KEY_ID: Optional[str] = None
    APPLE_PRIVATE_KEY: Optional[str] = None
    FACEBOOK_CLIENT_ID: Optional[str] = None
    FACEBOOK_CLIENT_SECRET: Optional[str] = None
    OAUTH_REDIRECT_URL: Optional[str] = None
    BASE_URL: str = "http://localhost:8888"

    # Application
    APP_NAME: str = "Mew Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS
    CORS_ORIGINS: str = "*"

    # Session Management
    SESSION_COOLDOWN_MINUTES: int = 30
    MAX_SESSIONS_PER_USER: int = 10

    # Cooldown Settings (hours)
    DEFAULT_COOLDOWN_HOURS: int = 24
    TUTORING_COOLDOWN_HOURS: int = 24
    SCHEDULING_COOLDOWN_HOURS: int = 12
    SUMMARY_COOLDOWN_HOURS: int = 48

    # Priority Period Settings (24-hour format)
    MORNING_PREP_START: str = "07:00"
    MORNING_PREP_END: str = "09:00"
    AFTER_SCHOOL_START: str = "15:00"
    AFTER_SCHOOL_END: str = "18:00"
    EVENING_ROUTINE_START: str = "19:00"
    EVENING_ROUTINE_END: str = "21:00"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields in .env
    )


settings = Settings()
