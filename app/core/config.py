from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    GEMINI_API_KEY: str = Field(
        description="API key for Gemini",
    )

    MISTRAL_API_KEY: str = Field(
        description="API key for Mistral",
    )

    UPLOAD_DIRECTORY: str = Field(

        description="Directory for file uploads",
    )

    HF_TOKEN: str = Field(
        description="Hugging Face token for model access",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        aliases = {
            "GEMINI_API_KEY": "GEMINI_API_KEY",
            "MISTRAL_API_KEY": "MISTRAL_API_KEY",
            "UPLOAD_DIRECTORY": "UPLOAD_DIRECTORY",
            "HF_TOKEN": "HF_TOKEN",
        }