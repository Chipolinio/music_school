from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=str(BASE_DIR / ".env"))

class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    JWT_PRIVATE_KEY: Path = BASE_DIR / "jwt_tokens" / "jwt-private.pem"
    JWT_PUBLIC_KEY: Path = BASE_DIR / "jwt_tokens" / "jwt-public.pem"
    ALGORITHM: str = "RS256"

    @property
    def DATABASE_URL(self) -> str:
        return (f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}")

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return (f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}")

    model_config = SettingsConfigDict(from_attributes=True)

settings = Settings()