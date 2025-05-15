from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_type: str = "dummy"
    debug: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
