from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    
    PROJECT_NAME: str = "PDF Analyzer API"
    DEBUG: bool = False

    # Database Settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str = "db" # Defaults to Docker service name 'db'
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    @property
    def database_url(self) -> str:
        """Assembles database connection string dynamically."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # # Read .env file automatically if present locally
    # model_config = SettingsConfigDict(env_file=ENV_FILE_PATH,
    #                                   extra="ignore",
    #                                   env_file_encoding="utf-8")



# Global instance for direct imports
settings = Settings()