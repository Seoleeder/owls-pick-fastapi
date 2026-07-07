from pydantic import BaseModel, Field
from typing import List

# ==========================================
# [OpenAI Structured Outputs] 키워드 한글화 파싱 스키마
# ==========================================

class KeywordItemSchema(BaseModel):
    eng_name: str = Field(
        ...,
        description="원본 영문 키워드"
    )
    kor_name: str | None = Field(
        default=None,
        description="한글화된 키워드"
    )

class BulkKeywordResponseSchema(BaseModel):
    """
    대량의 키워드 데이터를 파싱하기 위한 응답 스키마
    """
    localization_results: List[KeywordItemSchema]