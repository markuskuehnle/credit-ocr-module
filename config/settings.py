from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_type: str = "dummy"   # override with MODEL_TYPE
    debug: bool = True          # override with DEBUG

    model_config = SettingsConfigDict(        # modern replacement for inner Config
        env_file=".env",                      # optional .env file
        case_sensitive=False,                 # MODEL_TYPE, model_type, etc. all work
    )

settings = Settings()
