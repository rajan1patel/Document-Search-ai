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


    class Config:
        env_file=".env"



settings = Settings()
