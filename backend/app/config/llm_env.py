"""`APP_ENV`에 맞는 env 파일을 선택하고 값을 로드하는 유틸리티."""

from pathlib import Path

from dotenv import dotenv_values

ENV_FILE_BY_APP_ENV: dict[str, str] = {
    "dev": "dev.env",
    "prod": "prod.env",
}


def get_project_root() -> Path:
    """프로젝트 루트 경로를 반환한다."""
    return Path(__file__).resolve().parents[2]


def resolve_app_env(app_env_raw: str | None) -> str:
    """입력된 `APP_ENV` 값을 검증하고 기본값(`dev`)을 적용한다."""
    if app_env_raw is None or app_env_raw == "":
        return "dev"

    if app_env_raw not in ENV_FILE_BY_APP_ENV:
        allowed = ", ".join(sorted(ENV_FILE_BY_APP_ENV.keys()))
        raise ValueError(
            f"APP_ENV must be one of [{allowed}], but got '{app_env_raw}'."
        )

    return app_env_raw


def resolve_env_file_path(project_root: Path, app_env: str) -> Path:
    """환경 이름(`dev`/`prod`)에 해당하는 env 파일 절대경로를 만든다."""
    env_file_name = ENV_FILE_BY_APP_ENV[app_env]
    return project_root / env_file_name


def load_env_file_values(
    project_root: Path, app_env_raw: str | None
) -> dict[str, str | None]:
    """선택된 env 파일을 읽어 키-값 매핑으로 반환한다."""
    app_env = resolve_app_env(app_env_raw=app_env_raw)
    env_file_path = resolve_env_file_path(project_root=project_root, app_env=app_env)

    if not env_file_path.exists():
        raise FileNotFoundError(f"Environment file not found: {env_file_path}")

    loaded = dotenv_values(env_file_path)
    return {str(key): value for key, value in loaded.items()}
