from pathlib import Path

from harness.validators.fastapi_contract_checker import FastAPIContractValidator


def _write_runtime_file(tmp_path: Path, code: str) -> Path:
    runtime_dir = tmp_path / "app" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    file_path = runtime_dir / "analyze.py"
    file_path.write_text(code, encoding="utf-8")
    return file_path


def test_fastapi_contract_validator_valid_route(tmp_path: Path) -> None:
    _write_runtime_file(
        tmp_path=tmp_path,
        code=(
            "from fastapi import APIRouter\n"
            "from app.types.mood import AnalyzeRequest, AnalyzeResponse\n\n"
            "router = APIRouter()\n\n"
            "@router.post('/analyze', response_model=AnalyzeResponse)\n"
            "def analyze_meeting(request: AnalyzeRequest) -> AnalyzeResponse:\n"
            "    return AnalyzeResponse(topic='Architecture', mood='Positive', confidence=0.9)\n"
        ),
    )
    validator = FastAPIContractValidator(base_dir=str(tmp_path))
    assert validator.validate() == []


def test_fastapi_contract_validator_missing_return_type(tmp_path: Path) -> None:
    _write_runtime_file(
        tmp_path=tmp_path,
        code=(
            "from fastapi import APIRouter\n"
            "from app.types.mood import AnalyzeRequest, AnalyzeResponse\n\n"
            "router = APIRouter()\n\n"
            "@router.post('/analyze', response_model=AnalyzeResponse)\n"
            "def analyze_meeting(request: AnalyzeRequest):\n"
            "    return AnalyzeResponse(topic='Architecture', mood='Positive', confidence=0.9)\n"
        ),
    )
    validator = FastAPIContractValidator(base_dir=str(tmp_path))
    violations = validator.validate()
    assert any("반환 타입 힌트" in v for v in violations)


def test_fastapi_contract_validator_missing_response_model(tmp_path: Path) -> None:
    _write_runtime_file(
        tmp_path=tmp_path,
        code=(
            "from fastapi import APIRouter\n"
            "from app.types.mood import AnalyzeRequest, AnalyzeResponse\n\n"
            "router = APIRouter()\n\n"
            "@router.post('/analyze')\n"
            "def analyze_meeting(request: AnalyzeRequest) -> AnalyzeResponse:\n"
            "    return AnalyzeResponse(topic='Architecture', mood='Positive', confidence=0.9)\n"
        ),
    )
    validator = FastAPIContractValidator(base_dir=str(tmp_path))
    violations = validator.validate()
    assert any("response_model" in v for v in violations)


def test_fastapi_contract_validator_forbids_dict_or_list_return(tmp_path: Path) -> None:
    _write_runtime_file(
        tmp_path=tmp_path,
        code=(
            "from fastapi import APIRouter\n"
            "from app.types.mood import AnalyzeRequest, AnalyzeResponse\n\n"
            "router = APIRouter()\n\n"
            "@router.post('/analyze', response_model=AnalyzeResponse)\n"
            "def analyze_meeting(request: AnalyzeRequest) -> AnalyzeResponse:\n"
            "    return {'topic': 'Architecture', 'mood': 'Positive', 'confidence': 0.9}\n"
        ),
    )
    validator = FastAPIContractValidator(base_dir=str(tmp_path))
    violations = validator.validate()
    assert any("dict/list 리터럴" in v for v in violations)


def test_fastapi_contract_validator_forbids_non_types_io_models(tmp_path: Path) -> None:
    _write_runtime_file(
        tmp_path=tmp_path,
        code=(
            "from fastapi import APIRouter\n"
            "from app.types.mood import AnalyzeRequest\n"
            "from app.service.schemas import ServiceResponse\n\n"
            "router = APIRouter()\n\n"
            "@router.post('/analyze', response_model=ServiceResponse)\n"
            "def analyze_meeting(request: AnalyzeRequest) -> ServiceResponse:\n"
            "    return ServiceResponse()\n"
        ),
    )
    validator = FastAPIContractValidator(base_dir=str(tmp_path))
    violations = validator.validate()
    assert any("app/types 외 경로" in v for v in violations)


def test_fastapi_contract_validator_allows_whitelisted_sse_route(
    tmp_path: Path,
) -> None:
    _write_runtime_file(
        tmp_path=tmp_path,
        code=(
            "from fastapi import APIRouter\n"
            "from fastapi.responses import StreamingResponse\n"
            "from app.types.mood import AnalyzeRequest\n\n"
            "router = APIRouter()\n\n"
            "@router.post('/analyze/inspect/stream', response_class=StreamingResponse)\n"
            "def inspect_stream(request: AnalyzeRequest) -> StreamingResponse:\n"
            "    return StreamingResponse(iter(['event: done\\\\ndata: {}\\\\n\\\\n']), media_type='text/event-stream')\n"
        ),
    )
    validator = FastAPIContractValidator(base_dir=str(tmp_path))
    assert validator.validate() == []


def test_fastapi_contract_validator_rejects_sse_route_without_streaming_response_class(
    tmp_path: Path,
) -> None:
    _write_runtime_file(
        tmp_path=tmp_path,
        code=(
            "from fastapi import APIRouter\n"
            "from fastapi.responses import StreamingResponse\n"
            "from app.types.mood import AnalyzeRequest\n\n"
            "router = APIRouter()\n\n"
            "@router.post('/analyze/inspect/stream')\n"
            "def inspect_stream(request: AnalyzeRequest) -> StreamingResponse:\n"
            "    return StreamingResponse(iter(['event: done\\\\ndata: {}\\\\n\\\\n']), media_type='text/event-stream')\n"
        ),
    )
    validator = FastAPIContractValidator(base_dir=str(tmp_path))
    violations = validator.validate()
    assert any("response_class=StreamingResponse" in v for v in violations)
