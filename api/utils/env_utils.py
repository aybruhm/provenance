import os

from pydantic import BaseModel


class EnvSettings(BaseModel):
    # Infrastructure Settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://abc:qwerty@db:5432/provenance_db"
    )

    # Application Settings
    JWT_KEY: str = os.getenv("JWT_KEY", "")
    JWT_EXP: int = int(os.getenv("JWT_EXP", "900"))
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")


env = EnvSettings()
