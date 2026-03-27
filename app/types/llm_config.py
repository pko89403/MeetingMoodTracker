from pydantic import BaseModel


class LlmConfigResponse(BaseModel):
    LLM_API_KEY: str
    LLM_ENDPOINT: str
    LLM_MODEL: str
