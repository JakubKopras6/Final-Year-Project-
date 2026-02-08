from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "RAG Multi-Tenant System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this"
    
    # Database
    DATABASE_URL: str = "sqlite:///./instance/rag_system.db"
    
    class Config:
        env_file = ".env"