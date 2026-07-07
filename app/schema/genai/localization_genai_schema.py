#app\schema\genai\localization_genai_schema.py

from pydantic import BaseModel, Field

# ==========================================
# [OpenAI Structured Outputs] 게임 데이터 한글화 파싱 스키마
# ==========================================

class LocalizationResponseSchema(BaseModel):
    """
    게임 설명 및 스토리라인 한글화 시 JSON 응답 규격을 정의하는 스키마
    """
    description_ko: str | None = Field(
        default=None, 
        description="한글화된 게임 설명"
    )
    storyline_ko: str | None = Field(
        default=None, 
        description="한글화된 게임 스토리"
    )