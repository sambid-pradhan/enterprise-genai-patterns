from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    app_env: str = Field(default="local", alias="APP_ENV")
    workspace_root: Path = Field(default=Path("/workspace"), alias="WORKSPACE_ROOT")
    repos_dir: Path = Field(default=Path("/workspace/repos"), alias="REPOS_DIR")
    prompts_dir: Path = Field(default=Path("/workspace/prompts"), alias="PROMPTS_DIR")
    sample_repo_dir: Path = Field(default=Path("/workspace/sample_target_repo"), alias="SAMPLE_REPO_DIR")
    codex_command: str = Field(default="codex", alias="CODEX_COMMAND")
    pytest_command: str = Field(default="pytest", alias="PYTEST_COMMAND")
    git_command: str = Field(default="git", alias="GIT_COMMAND")
    gh_command: str = Field(default="gh", alias="GH_COMMAND")
    agent_timeout_seconds: int = Field(default=1800, alias="AGENT_TIMEOUT_SECONDS")
    pytest_timeout_seconds: int = Field(default=600, alias="PYTEST_TIMEOUT_SECONDS")
    git_timeout_seconds: int = Field(default=300, alias="GIT_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
