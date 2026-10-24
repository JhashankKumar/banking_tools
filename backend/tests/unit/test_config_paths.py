from app.core.config import ENV_FILE


def test_env_file_is_at_repo_root() -> None:
    # The repo root is where docker-compose.yml and .env.example live.
    assert (ENV_FILE.parent / "docker-compose.yml").is_file()
    assert ENV_FILE.name == ".env"
