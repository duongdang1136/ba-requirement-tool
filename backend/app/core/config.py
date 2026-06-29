from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "BA Requirement Tool"
    debug: bool = False

    database_url: str = "sqlite:///./ba_tool.db"
    upload_dir: str = "./uploads"
    models_dir: str = "./models"

    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # LLM config (set one)
    llm_provider: str = "openai"  # openai | anthropic | local
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    local_llm_url: str = "http://localhost:11434"

    # sherpa-onnx model
    asr_model_dir: str = "./models/asr/sherpa-onnx-whisper-small"
    asr_language: str = "vi"

    # File limits
    max_upload_size_mb: int = 500
    allowed_extensions: List[str] = [".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg"]

    class Config:
        env_file = ".env"


settings = Settings()
