"""
Environment-driven configuration.

Never branch on `if production:` in application logic. Instead read
typed settings from here, which itself resolves entirely from
environment variables (with sane local-dev defaults).
"""
from functools import lru_cache
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core ---
    app_env: Literal["development", "production", "test"] = Field("development", alias="APP_ENV")
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # --- Database ---
    database_url: str = Field(..., alias="DATABASE_URL")

    # --- Vector store ---
    vector_store: Literal["faiss", "chroma", "pgvector"] = Field("faiss", alias="VECTOR_STORE")
    faiss_index_dir: str = Field("./data/faiss", alias="FAISS_INDEX_DIR")

    # --- LLM ---
    llm_provider: Literal["ollama", "openai", "groq", "gemini"] = Field("ollama", alias="LLM_PROVIDER")
    llm_model: str = Field("llama3", alias="LLM_MODEL")
    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    groq_api_key: str = Field("", alias="GROQ_API_KEY")
    gemini_api_key: str = Field("", alias="GEMINI_API_KEY")
    ollama_base_url: str = Field("http://localhost:11434", alias="OLLAMA_BASE_URL")

    # --- Embeddings / RAG ---
    embedding_model: str = Field("sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    chunk_size: int = Field(800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(120, alias="CHUNK_OVERLAP")
    top_k: int = Field(5, alias="TOP_K")
    similarity_threshold: float = Field(0.2, alias="SIMILARITY_THRESHOLD")
    reranker_model: str = Field("", alias="RERANKER_MODEL")

    # --- CORS ---
    cors_origins: str = Field("http://localhost:3000", alias="CORS_ORIGINS")

    # --- Storage ---
    storage_provider: Literal["local", "s3"] = Field("local", alias="STORAGE_PROVIDER")
    storage_bucket: str = Field("", alias="STORAGE_BUCKET")
    storage_endpoint: str = Field("", alias="STORAGE_ENDPOINT")
    storage_access_key: str = Field("", alias="STORAGE_ACCESS_KEY")
    storage_secret_key: str = Field("", alias="STORAGE_SECRET_KEY")
    local_storage_dir: str = Field("./data/uploads", alias="LOCAL_STORAGE_DIR")

    # --- Cache ---
    redis_url: str = Field("", alias="REDIS_URL")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — settings are read once per process."""
    return Settings()
