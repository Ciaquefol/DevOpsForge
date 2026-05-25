from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./tasks.db"
    secret_key: str = "dev-secret-key"
    environment: str = "development"
    deploy_workspace: str = "./deploy_workspace"
    git_cache_dir: str = "./deploy_workspace/git-cache"
    default_repo_url: str = "https://github.com/octocat/Hello-World.git"
    metrics_interval_seconds: int = 5
    seed_on_startup: bool = True
    cors_origins: str = (
        "http://localhost,http://127.0.0.1,"
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://localhost:8000"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
