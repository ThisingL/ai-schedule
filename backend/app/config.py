from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

_default_db_url = f"sqlite+aiosqlite:///{DATA_DIR / 'schedule.db'}"


class Settings(BaseSettings):
    database_url: str = _default_db_url

    class Config:
        env_file = BASE_DIR / ".env"


settings = Settings()
