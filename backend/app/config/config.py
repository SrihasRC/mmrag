from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # API Keys
    COHERE_API_KEY: str
    GOOGLE_API_KEY: str
    GROQ_API_KEY: str
    LANGCHAIN_API_KEY: str = ""
    
    # LangChain Configuration
    LANGCHAIN_TRACING_V2: bool = False
    
    # Application Configuration
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Storage Configuration
    STORAGE_PATH: str = "./storage"
    VECTOR_DB_PATH: str = "./storage/vector_db"
    CONTENT_PATH: str = "./storage/content"
    UPLOADS_PATH: str = "./storage/uploads"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '../../.env')
        env_file_encoding = 'utf-8'

settings = Settings()  # type: ignore