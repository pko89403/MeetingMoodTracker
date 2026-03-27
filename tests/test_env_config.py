from pathlib import Path

from fastapi.testclient import TestClient

import app.service.llm_config_service as llm_config_service
from app.main import app

client = TestClient(app)


def _write_env_file(
    base_dir: Path,
    file_name: str,
    values: dict[str, str],
) -> None:
    lines = [f"{key}={value}" for key, value in values.items()]
    (base_dir / file_name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_get_llm_config_uses_dev_file_when_app_env_is_unset(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_env_file(
        base_dir=tmp_path,
        file_name="dev.env",
        values={
            "LLM_API_KEY": "dev-key-001",
            "LLM_ENDPOINT": "https://dev.endpoint",
            "LLM_MODEL_NAME": "gpt-5-mini",
            "LLM_DEPLOYMENT_NAME": "gpt-5-mini",
            "LLM_MODEL_VERSION": "2025-08-07",
        },
    )
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setattr(llm_config_service, "get_project_root", lambda: tmp_path)

    response = client.get("/api/env/v1")

    assert response.status_code == 200
    assert response.json() == {
        "LLM_API_KEY": "dev-key-001",
        "LLM_ENDPOINT": "https://dev.endpoint",
        "LLM_MODEL_NAME": "gpt-5-mini",
        "LLM_DEPLOYMENT_NAME": "gpt-5-mini",
        "LLM_MODEL_VERSION": "2025-08-07",
    }


def test_get_llm_config_uses_prod_file_when_app_env_is_prod(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_env_file(
        base_dir=tmp_path,
        file_name="prod.env",
        values={
            "LLM_API_KEY": "prod-key-999",
            "LLM_ENDPOINT": "https://prod.endpoint",
            "LLM_MODEL_NAME": "gpt-5.4",
            "LLM_DEPLOYMENT_NAME": "gpt-5.4-prod",
        },
    )
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setattr(llm_config_service, "get_project_root", lambda: tmp_path)

    response = client.get("/api/env/v1")

    assert response.status_code == 200
    assert response.json() == {
        "LLM_API_KEY": "prod-key-999",
        "LLM_ENDPOINT": "https://prod.endpoint",
        "LLM_MODEL_NAME": "gpt-5.4",
        "LLM_DEPLOYMENT_NAME": "gpt-5.4-prod",
        "LLM_MODEL_VERSION": None,
    }


def test_get_llm_config_returns_422_when_required_keys_are_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_env_file(
        base_dir=tmp_path,
        file_name="dev.env",
        values={
            "LLM_API_KEY": "dev-key-001",
            "LLM_ENDPOINT": "https://dev.endpoint",
            "LLM_MODEL_NAME": "gpt-5-mini",
        },
    )
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setattr(llm_config_service, "get_project_root", lambda: tmp_path)

    response = client.get("/api/env/v1")

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "LLM_CONFIG_MISSING_KEY"
    assert response.json()["detail"]["missing_keys"] == ["LLM_DEPLOYMENT_NAME"]


def test_get_llm_config_returns_422_when_only_legacy_llm_model_key_exists(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_env_file(
        base_dir=tmp_path,
        file_name="dev.env",
        values={
            "LLM_API_KEY": "dev-key-001",
            "LLM_ENDPOINT": "https://dev.endpoint",
            "LLM_MODEL": "legacy-model-name",
        },
    )
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setattr(llm_config_service, "get_project_root", lambda: tmp_path)

    response = client.get("/api/env/v1")

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "LLM_CONFIG_MISSING_KEY"
    assert response.json()["detail"]["missing_keys"] == [
        "LLM_MODEL_NAME",
        "LLM_DEPLOYMENT_NAME",
    ]


def test_get_llm_config_returns_500_when_target_env_file_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setattr(llm_config_service, "get_project_root", lambda: tmp_path)

    response = client.get("/api/env/v1")

    assert response.status_code == 500
    assert response.json()["detail"]["error_code"] == "LLM_CONFIG_LOAD_FAILED"
    assert "Environment file not found" in response.json()["detail"]["reason"]


def test_get_llm_config_returns_500_when_app_env_is_invalid(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("APP_ENV", "stage")
    monkeypatch.setattr(llm_config_service, "get_project_root", lambda: tmp_path)

    response = client.get("/api/env/v1")

    assert response.status_code == 500
    assert response.json()["detail"]["error_code"] == "LLM_CONFIG_LOAD_FAILED"
    assert "APP_ENV must be one of [dev, prod]" in response.json()["detail"]["reason"]
