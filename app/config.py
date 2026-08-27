"""Central configuration. Single source of truth for every service toggle."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_embed_model: str = "text-embedding-004"

    mongo_uri: str = ""
    mongo_db: str = "opsmind"

    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_docs_table: str = "policy_chunks"

    redis_url: str = "redis://localhost:6379/0"

    firebase_credentials_json: str = ""
    auth_dev_bypass: bool = True

    n8n_webhook_url: str = ""

    rag_chunk_size: int = 900
    rag_chunk_overlap: int = 150
    rag_top_k: int = 5
    rag_min_score: float = 0.25

    # --- capability flags: every subsystem checks these instead of keys ---
    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_mongo(self) -> bool:
        return bool(self.mongo_uri)

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key)

    @property
    def has_firebase(self) -> bool:
        return bool(self.firebase_credentials_json)

    def capability_report(self) -> dict:
        return {
            "gemini": self.has_gemini,
            "mongo": self.has_mongo,
            "supabase_vectors": self.has_supabase,
            "firebase_auth": self.has_firebase,
            "n8n": bool(self.n8n_webhook_url),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
