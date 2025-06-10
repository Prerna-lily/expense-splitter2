from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Expense Splitter"
    
    # Error handling
    MAX_ERROR_MESSAGE_LENGTH: int = 500
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
