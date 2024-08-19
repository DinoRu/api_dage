from typing import Optional

from pydantic_settings import BaseSettings


class Setting(BaseSettings):
    SECRET_KEY: Optional[str] = None

    class Config:
        env_file = ".env"

