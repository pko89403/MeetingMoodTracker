"""Streamlit 기반 Analyze Inspect 테스트 콘솔."""

import json
import os
from datetime import datetime
from typing import Any

import httpx
import streamlit as st

DEFAULT_API_BASE_URL = "http://localhost:8000"
MAX_HISTORY_ITEMS = 30


def _resolve_api_base_url() -> str:
    """환경변수/입력값 기준으로 FastAPI 베이스 URL을 정규화한다."""
    configured = os.getenv("ANALYZE_API_BASE_URL", DEFAULT_API_BASE_URL).strip()
    if configured == "":
        configured = DEFAULT_API_BASE_URL
    return configured.rstrip("/")


def _call_inspect_rest(base_url: str, payload: dict[str, str]) -> dict[str, Any]:
    """inspect REST API를 호출해 trace 포함 결과를 가져온다."""
    with httpx.Client(timeout=30.0) as client:
        response = client.post(f"{base_url}/api/v1/analyze/inspect", json=payload)
        response.raise_for_status()
        return response.json()


def _read_sse_events(base_url: str, payload: dict[str, str]) -> list[dict[str, Any]]:
    """inspect SSE 스트림을 읽어 이벤트 목록으로 파싱한다."""
    events: list[dict[str, Any]] = []
    current_event = "message"
    data_lines: list[str] = []

    with httpx.Client(timeout=60.0) as client:
        with client.stream(
            "POST",
            f"{base_url}/api/v1/analyze/inspect/stream",
            json=payload,
            headers={"Accept": "text/event-stream"},
        ) as response:
            response.raise_for_status()
            for raw_line in response.iter_lines():
                line = raw_line.strip() if raw_line is not None else ""
                if line == "":
                    if data_lines:
                        data_raw = "\n".join(data_lines)
                        try:
                            parsed_data = json.loads(data_raw)
                        except json.JSONDecodeError:
                            parsed_data = {"raw": data_raw}
                        events.append({"event": current_event, "data": parsed_data})
                    current_event = "message"
                    data_lines = []
                    continue

                if line.startswith("event:"):
                    current_event = line.split(":", 1)[1].strip()
                    continue
                if line.startswith("data:"):
                    data_lines.append(line.split(":", 1)[1].strip())

    return events


def _merge_events_to_inspect_payload(events: list[dict[str, Any]]) -> dict[str, Any]:
    """SSE 이벤트 목록을 inspect REST와 동일한 표시 구조로 변환한다."""
    request_id = ""
    logic_steps: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []
    result: dict[str, Any] = {}

    for event in events:
        event_name = event.get("event")
        data = event.get("data", {})
        if isinstance(data, dict) and "request_id" in data:
            request_id = str(data["request_id"])

        if event_name == "start" and isinstance(data, dict):
            maybe_logic_steps = data.get("logic_steps")
            if isinstance(maybe_logic_steps, list):
                logic_steps = maybe_logic_steps
        elif event_name == "log" and isinstance(data, dict):
            logs.append(
                {
                    "request_id": data.get("request_id"),
                    "step_id": data.get("step_id"),
                    "message_ko": data.get("message_ko"),
                    "created_at": data.get("created_at"),
                }
            )
        elif event_name == "result" and isinstance(data, dict):
            maybe_result = data.get("result")
            if isinstance(maybe_result, dict):
                result = maybe_result
        elif event_name == "error" and isinstance(data, dict):
            message = str(data.get("message_ko", "알 수 없는 SSE 오류"))
            raise RuntimeError(message)

    return {
        "request_id": request_id,
        "result": result,
        "logic_steps": logic_steps,
        "logs": logs,
    }


def _render_logic_steps(logic_steps: list[dict[str, Any]]) -> None:
    """로직 단계 목록을 UI에 렌더링한다."""
    st.subheader("내부 로직 단계")
    if not logic_steps:
        st.info("표시할 로직 단계가 없습니다.")
        return
    for index, step in enumerate(logic_steps, start=1):
        step_id = step.get("step_id", "-")
        title = step.get("title_ko", "-")
        description = step.get("description_ko", "-")
        st.markdown(f"{index}. `{step_id}` - **{title}**")
        st.caption(str(description))


def _render_logs(logs: list[dict[str, Any]]) -> None:
    """로그 항목을 테이블 형태로 표시한다."""
    st.subheader("실행 로그")
    if not logs:
        st.info("표시할 로그가 없습니다.")
        return
    st.table(logs)


def _init_session_state() -> None:
    """화면 상태/히스토리 관련 세션 키를 초기화한다."""
    if "last_response" not in st.session_state:
        st.session_state["last_response"] = None
    if "last_error" not in st.session_state:
        st.session_state["last_error"] = None
    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "selected_history_index" not in st.session_state:
        st.session_state["selected_history_index"] = -1


def _build_history_entry(
    payload: dict[str, str],
    response_payload: dict[str, Any],
    mode_label: str,
) -> dict[str, Any]:
    """요청/응답 페어를 히스토리 저장 구조로 변환한다."""
    text_value = payload.get("text", "")
    text_preview = text_value[:60] + ("..." if len(text_value) > 60 else "")
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "mode": mode_label,
        "meeting_id": payload.get("meeting_id", "-"),
        "text_preview": text_preview,
        "request_id": response_payload.get("request_id", "-"),
        "response": response_payload,
    }


def _append_history_entry(entry: dict[str, Any]) -> None:
    """세션 히스토리에 항목을 추가하고 최대 보관 개수를 유지한다."""
    history: list[dict[str, Any]] = st.session_state["history"]
    history.append(entry)
    if len(history) > MAX_HISTORY_ITEMS:
        del history[: len(history) - MAX_HISTORY_ITEMS]


def _format_history_option(history_index: int) -> str:
    """히스토리 선택 UI에 표시할 라벨 문자열을 만든다."""
    if history_index == -1:
        return "최신 결과 보기"

    history: list[dict[str, Any]] = st.session_state["history"]
    if history_index < 0 or history_index >= len(history):
        return "유효하지 않은 항목"

    entry = history[history_index]
    created_at = entry.get("created_at", "-")
    mode = entry.get("mode", "-")
    meeting_id = entry.get("meeting_id", "-")
    request_id = entry.get("request_id", "-")
    return (
        f"{created_at} | {mode} | meeting_id={meeting_id} | "
        f"request_id={request_id}"
    )


def _resolve_selected_response() -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """현재 선택 상태(최신/히스토리)에 맞는 표시 응답과 메타를 반환한다."""
    selected_history_index = st.session_state.get("selected_history_index", -1)
    if selected_history_index == -1:
        return st.session_state.get("last_response"), None

    history: list[dict[str, Any]] = st.session_state.get("history", [])
    if 0 <= selected_history_index < len(history):
        entry = history[selected_history_index]
        return entry.get("response"), entry

    return st.session_state.get("last_response"), None


def _render_history_selector_in_sidebar() -> None:
    """사이드바에 히스토리 선택 UI를 렌더링한다."""
    with st.sidebar:
        history: list[dict[str, Any]] = st.session_state["history"]
        st.subheader("요청 히스토리")
        if history:
            selectable_indexes = [-1] + list(range(len(history) - 1, -1, -1))
            current_selection = st.session_state.get("selected_history_index", -1)
            if current_selection not in selectable_indexes:
                current_selection = -1
            selected_position = selectable_indexes.index(current_selection)
            selected_history_index = st.selectbox(
                "표시할 결과 선택",
                options=selectable_indexes,
                index=selected_position,
                format_func=_format_history_option,
            )
            st.session_state["selected_history_index"] = selected_history_index
        else:
            st.caption("저장된 히스토리가 없습니다.")
            st.session_state["selected_history_index"] = -1


def main() -> None:
    """Streamlit 앱을 구성하고 API 호출 결과를 화면에 표시한다."""
    st.set_page_config(page_title="Analyze Inspect Console", layout="wide")
    st.title("Analyze Inspect 테스트 콘솔")
    st.caption("기본 모드로 SSE를 사용하고, 실패 시 inspect REST로 자동 폴백합니다.")

    _init_session_state()

    default_base_url = _resolve_api_base_url()
    with st.sidebar:
        st.subheader("연결 설정")
        base_url = st.text_input("FastAPI Base URL", value=default_base_url)
        use_sse = st.toggle("SSE 우선 사용", value=True)
        col_clear, col_history_clear = st.columns(2)
        with col_clear:
            if st.button("화면 Clear"):
                st.session_state["last_response"] = None
                st.session_state["last_error"] = None
                st.session_state["selected_history_index"] = -1
                st.rerun()
        with col_history_clear:
            if st.button("히스토리 삭제"):
                st.session_state["history"] = []
                st.session_state["selected_history_index"] = -1
                st.rerun()

    with st.form("analyze_inspect_form"):
        meeting_id = st.text_input("meeting_id", value="m_12345")
        text = st.text_area(
            "text",
            value="오늘 회의에서는 새로운 서버 아키텍처에 대해 논의했습니다. 다들 긍정적인 반응이었어요.",
            height=140,
        )
        submitted = st.form_submit_button("요청 실행")

    if submitted:
        payload = {"meeting_id": meeting_id, "text": text}
        st.session_state["last_error"] = None
        try:
            mode_label = "REST"
            if use_sse:
                try:
                    sse_events = _read_sse_events(base_url=base_url, payload=payload)
                    response_payload = _merge_events_to_inspect_payload(events=sse_events)
                    mode_label = "SSE"
                except Exception as sse_exc:
                    st.warning(
                        "SSE 호출에 실패해 inspect REST로 전환합니다: "
                        f"{sse_exc}",
                    )
                    response_payload = _call_inspect_rest(
                        base_url=base_url,
                        payload=payload,
                    )
                    mode_label = "SSE->REST(Fallback)"
            else:
                response_payload = _call_inspect_rest(
                    base_url=base_url,
                    payload=payload,
                )
            st.session_state["last_response"] = response_payload
            _append_history_entry(
                _build_history_entry(
                    payload=payload,
                    response_payload=response_payload,
                    mode_label=mode_label,
                )
            )
            st.session_state["selected_history_index"] = -1
        except Exception as exc:
            st.session_state["last_error"] = str(exc)

    _render_history_selector_in_sidebar()

    if st.session_state["last_error"]:
        st.error(f"요청 실행 실패: {st.session_state['last_error']}")

    response_payload, selected_history_entry = _resolve_selected_response()
    if not response_payload:
        st.info("좌측 입력을 수정한 뒤 `요청 실행`을 눌러 결과를 확인하세요.")
        return

    if selected_history_entry is not None:
        st.caption(
            "히스토리 조회 중: "
            f"{selected_history_entry.get('created_at')} | "
            f"mode={selected_history_entry.get('mode')} | "
            f"text={selected_history_entry.get('text_preview')}"
        )

    st.subheader("요청 ID")
    st.code(str(response_payload.get("request_id", "-")))

    col_result, col_logs = st.columns([1, 1])
    with col_result:
        st.subheader("Analyze 결과")
        st.json(response_payload.get("result", {}))
    with col_logs:
        _render_logs(response_payload.get("logs", []))

    _render_logic_steps(response_payload.get("logic_steps", []))


if __name__ == "__main__":
    main()
