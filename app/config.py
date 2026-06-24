from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    cors_origins: str = "http://localhost:3000"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    imagekit_public_key: str = ""
    imagekit_private_key: str = ""
    imagekit_url_endpoint: str = "https://ik.imagekit.io/abm2tsfhg"
    imagekit_upload_folder: str = "/mags/profiles"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def imagekit_configured(self) -> bool:
        return bool(self.imagekit_private_key and self.imagekit_public_key)


settings = Settings()
