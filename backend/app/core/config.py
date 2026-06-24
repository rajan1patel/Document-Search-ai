from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    APP_NAME:str = "Document Intelligence Search"

    DATABASE_URL:str = "postgresql+asyncpg://document_user:password@localhost:5432/document_db"

    JWT_SECRET:str = "change-me"

    JWT_ALGORITHM:str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES:int = 30


    MILVUS_HOST:str = "localhost"

    MILVUS_PORT:int = 19530

    CORS_ORIGINS:list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # LLM / DSPy Settings
    OPENROUTER_API_KEY:str = ""
    LLM_MODEL:str = "google/gemini-3.1-flash-image"
    LLM_BASE_URL:str = "https://openrouter.ai/api/v1"
    LLM_MAX_TOKENS:int = 2048
    LLM_TEMPERATURE:float = 0.7

    # X-Search API (external patent search)
    XSEARCH_API_KEY:str = ""
    XSEARCH_BASE_URL:str = "http://192.168.0.57:8082/patent_search"

    class Config:
        env_file=".env"
        extra = "ignore"  # ignore unknown env vars



settings = Settings()
