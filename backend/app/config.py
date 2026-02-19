from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "RAG Multi-Tenant System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = "sqlite:///./instance/rag_system.db"

    # File Upload 
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 25 * 1024 * 1024  # 25MB
    ALLOWED_EXTENSIONS: set = {".pdf"}
    
    # Text Processing 
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

     # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    
    class Config:
        env_file = ".env"

settings = Settings()

# Create necessary directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs("./instance", exist_ok=True)