from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    demo_mode: bool = True
    huggingface_api_key: str | None = Field(default=None, validation_alias=AliasChoices("HUGGINGFACE_API_KEY", "HF_TOKEN"))
    hf_chat_model: str = "Qwen/Qwen2.5-7B-Instruct"
    mongodb_uri: str | None = None
    mongodb_database: str = "bnb_interview"
    proctor_warning_limit: int = 3
    proctor_face_absence_seconds: int = 10
    proctor_min_brightness: int = 55
    proctor_max_brightness: int = 235


settings = Settings()
