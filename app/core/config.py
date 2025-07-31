from pydantic_settings import BaseSettings
from pydantic import SecretStr
from pydantic import Field
import os

class Settings(BaseSettings):
    GEMINI_API_KEY: SecretStr = Field(
        default=SecretStr(os.getenv("GEMINI_API_KEY")),
        description="API key for Gemini",
    )

    MISTRAL_API_KEY: SecretStr = Field(
        default=SecretStr(os.getenv("MISTRAL_API_KEY")),
        description="API key for Mistral",
    )

    UPLOAD_DIRECTORY: str = Field(
        default=os.getenv("UPLOAD_DIRECTORY", "vector_store"),
        description="Directory for file uploads",
    )

    DATABASE_URL : str = Field(
        default=os.getenv("DATABASE_URL", ""),
        description="Database URL for the application",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        aliases = {
            "GEMINI_API_KEY": "GEMINI_API_KEY",
            "MISTRAL_API_KEY": "MISTRAL_API_KEY",
            "UPLOAD_DIRECTORY": "UPLOAD_DIRECTORY",
        }

settings = Settings()
