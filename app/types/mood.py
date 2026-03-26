from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    meeting_id: str
    text: str


class AnalyzeResponse(BaseModel):
    topic: str
    mood: str
    confidence: float
