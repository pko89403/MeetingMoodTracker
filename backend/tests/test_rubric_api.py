from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_calculate_rubric_endpoint_success():
    # Given
    payload = {
        "topics": ["Architecture", "Performance"],
        "sentiment": {
            "positive": {"confidence": 60},
            "negative": {"confidence": 10},
            "neutral": {"confidence": 30},
        },
        "meeting_signals": {
            "tension": {"confidence": 10},
            "alignment": {"confidence": 80},
            "urgency": {"confidence": 20},
            "clarity": {"confidence": 90},
            "engagement": {"confidence": 70},
        },
    }

    # When
    response = client.post("/api/v1/rubric/calculate", json=payload)

    # Then
    assert response.status_code == 200
    data = response.json()
    assert "rubric" in data
    assert "dominance" in data["rubric"]
    assert "efficiency" in data["rubric"]
    assert "cohesion" in data["rubric"]

    # 구체적인 값 검증 (calculate_final_rubrics 로직 기준)
    # Dominance: (70*0.35 + 10*0.25 + 90*0.20 + 80*0.10 + 20*0.10) + (100-30)*0.1 = 55 + 7 = 62
    assert data["rubric"]["dominance"] == 62

    # Efficiency: (90*0.5 + 20*0.3 + 70*0.2) + min(2*5, 15) = 65 + 10 = 75
    assert data["rubric"]["efficiency"] == 75

    # Cohesion: (80*0.4 + 70*0.3 + 90*0.1) + 60*0.2 = (32 + 21 + 9) + 12 = 62 + 12 = 74
    assert data["rubric"]["cohesion"] == 74


def test_calculate_rubric_endpoint_invalid_payload():
    # Given: 필수 필드 누락
    payload = {"topics": []}

    # When
    response = client.post("/api/v1/rubric/calculate", json=payload)

    # Then
    assert response.status_code == 422
