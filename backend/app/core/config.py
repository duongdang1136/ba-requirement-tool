from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "BA Requirement Tool"
    debug: bool = False

    database_url: str = "sqlite:///./ba_tool.db"
    upload_dir: str = "./uploads"
    models_dir: str = str(REPO_ROOT / "models")

    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # LLM config (set one)
    llm_provider: str = "ollama"  # ollama | openai | anthropic | local
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    local_llm_url: str = "http://localhost:11434"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_fallback_model: str = "qwen2.5:3b"
    ollama_timeout_seconds: int = 300
    ollama_context_tokens: int = 8192
    llm_temperature: float = 0.2

    # sherpa-onnx model
    asr_model_dir: str = str(REPO_ROOT / "models" / "asr" / "sherpa-onnx-whisper-small")
    asr_language: str = "vi"
    asr_provider: str = "cpu"
    vad_model_path: str = str(REPO_ROOT / "models" / "vad" / "silero_vad.onnx")
    diarization_segmentation_model: str = str(REPO_ROOT / "models" / "diarization" / "sherpa-onnx-pyannote-segmentation-3-0" / "model.onnx")
    diarization_embedding_model: str = str(REPO_ROOT / "models" / "diarization" / "3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx")
    diarization_cluster_threshold: float = 0.5
    diarization_chunk_minutes: int = 25
    diarization_speaker_match_threshold: float = 0.62
    upload_chunk_size_mb: int = 8

    # File limits
    max_upload_size_mb: int = 1024
    allowed_extensions: List[str] = [".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg"]
    asr_num_threads: int = 8

    worker_poll_interval_seconds: float = 2.0
    job_timeout_minutes: int = 240

    class Config:
        env_file = ".env"


settings = Settings()
