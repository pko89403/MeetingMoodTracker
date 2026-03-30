#!/usr/bin/env python3
"""LLM-as-Judge 배치 평가 스크립트.

입력 JSONL 예시:
{"meeting_id":"m1","turn_id":"t1","utterance_text":"좋습니다","predicted_label":"POS"}
"""

import argparse
import json
from pathlib import Path
from typing import Any

from openai import AzureOpenAI

from app.service.llm_config_service import get_llm_config
from app.types.llm_config import LlmConfigResponse

DEFAULT_AZURE_OPENAI_API_VERSION = "2025-04-01-preview"
SUPPORTED_SENTIMENT_LABELS: tuple[str, str, str] = ("POS", "NEG", "NEUTRAL")

JUDGE_RESPONSE_SCHEMA: dict[str, Any] = {
    "name": "turn_sentiment_judge",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "judged_label": {
                "type": "string",
                "enum": list(SUPPORTED_SENTIMENT_LABELS),
            },
            "agree_with_prediction": {"type": "boolean"},
            "rationale": {"type": "string"},
        },
        "required": ["judged_label", "agree_with_prediction", "rationale"],
    },
}


def _resolve_api_version(cfg: LlmConfigResponse) -> str:
    """모델 설정에서 API 버전을 우선순위에 따라 선택한다."""
    if cfg.LLM_API_VERSION is not None and cfg.LLM_API_VERSION.strip() != "":
        return cfg.LLM_API_VERSION
    if cfg.LLM_MODEL_VERSION is not None and cfg.LLM_MODEL_VERSION.strip() != "":
        return cfg.LLM_MODEL_VERSION
    return DEFAULT_AZURE_OPENAI_API_VERSION


def _build_client(cfg: LlmConfigResponse) -> AzureOpenAI:
    """평가 스크립트용 Azure OpenAI 클라이언트를 생성한다."""
    return AzureOpenAI(
        api_key=cfg.LLM_API_KEY,
        azure_endpoint=cfg.LLM_ENDPOINT,
        api_version=_resolve_api_version(cfg=cfg),
    )


def _judge_one_turn(
    client: AzureOpenAI,
    deployment_name: str,
    utterance_text: str,
    predicted_label: str,
) -> dict[str, Any]:
    """한 턴의 예측 라벨을 판정하고 판정 결과를 구조화해 반환한다."""
    completion = client.chat.completions.create(
        model=deployment_name,
        response_format={"type": "json_schema", "json_schema": JUDGE_RESPONSE_SCHEMA},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict sentiment judge for meeting turns. "
                    "Classify sentiment as POS/NEG/NEUTRAL for Korean and mixed English input. "
                    "Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"utterance:\n{utterance_text}\n\n"
                    f"predicted_label={predicted_label}\n"
                    "Judge if prediction is correct."
                ),
            },
        ],
    )
    content = completion.choices[0].message.content
    if not isinstance(content, str):
        raise ValueError("Judge response content is not a string.")
    parsed = json.loads(content)
    return {
        "judged_label": parsed["judged_label"],
        "agree_with_prediction": parsed["agree_with_prediction"],
        "rationale": parsed["rationale"],
    }


def run(input_path: Path, output_path: Path) -> None:
    """입력 JSONL 전체를 평가하고 단일 리포트 JSON으로 저장한다."""
    llm_cfg = get_llm_config()
    client = _build_client(cfg=llm_cfg)

    rows: list[dict[str, Any]] = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "":
            continue
        rows.append(json.loads(line))

    results: list[dict[str, Any]] = []
    agree_count = 0
    for row in rows:
        judged = _judge_one_turn(
            client=client,
            deployment_name=llm_cfg.LLM_DEPLOYMENT_NAME,
            utterance_text=str(row["utterance_text"]),
            predicted_label=str(row["predicted_label"]),
        )
        agree = bool(judged["agree_with_prediction"])
        if agree:
            agree_count += 1
        results.append(
            {
                "meeting_id": row.get("meeting_id"),
                "turn_id": row.get("turn_id"),
                "predicted_label": row.get("predicted_label"),
                "judged_label": judged["judged_label"],
                "agree_with_prediction": agree,
                "rationale": judged["rationale"],
            }
        )

    total = len(results)
    report = {
        "total_turns": total,
        "agree_count": agree_count,
        "agreement_rate": (agree_count / total) if total > 0 else 0.0,
        "model_name": llm_cfg.LLM_MODEL_NAME,
        "deployment_name": llm_cfg.LLM_DEPLOYMENT_NAME,
        "model_version": llm_cfg.LLM_MODEL_VERSION,
        "results": results,
    }
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """CLI 인자를 파싱해 LLM-as-Judge 배치 평가를 실행한다."""
    parser = argparse.ArgumentParser(
        description="Evaluate sentiment predictions with LLM-as-Judge"
    )
    parser.add_argument("--input", required=True, help="Input JSONL path")
    parser.add_argument("--output", required=True, help="Output JSON report path")
    args = parser.parse_args()

    run(
        input_path=Path(args.input),
        output_path=Path(args.output),
    )


if __name__ == "__main__":
    main()
