import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    SECRET_KEY: str

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
