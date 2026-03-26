from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analyze_meeting_mood():
    """
    회의록 텍스트를 `/api/v1/analyze`로 전송했을 때,
    Topic과 Mood, Confidence가 포함된 200 OK 응답을 받아야 한다.
    """
    payload = {
        "meeting_id": "m_12345",
        "text": "오늘 회의에서는 새로운 서버 아키텍처에 대해 논의했습니다. 다들 긍정적인 반응이었어요.",
    }
    response = client.post("/api/v1/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "topic" in data
    assert "mood" in data
    assert "confidence" in data

    # 뼈대를 세우기 위해 우선 고정된 더미 응답(Dummy)을 기대하도록 설정
    assert data["topic"] == "Architecture"
    assert data["mood"] == "Positive"
    assert isinstance(data["confidence"], float)
