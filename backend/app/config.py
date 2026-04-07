from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    max_file_size_mb: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
