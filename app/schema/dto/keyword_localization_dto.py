from typing import List
from pydantic import Field
from app.schema.dto.base_dto import CamelModel
from app.schema.enums.genai_fail_reason import GenaiFailReason

# ==========================================
# [Keyword Request/Response] 키워드 한글화 DTO
# ==========================================

class KeywordLocalizationRequest(CamelModel):
    """
    키워드 대량 한글화 요청 DTO
    """
    keywords: List[str] = Field(
        ..., 
        description="원본 영문 키워드 목록",
        min_length=1,
        json_schema_extra={"example": ["masterpiece", "boring", "great soundtrack"]}
    )

class KeywordResult(CamelModel):
    """
    단일 키워드 한글화 응답 DTO
    """
    eng_name: str = Field(
        ..., 
        description="원본 영문 키워드"
    )
    kor_name: str | None = Field(
        default=None, 
        description="한글화된 키워드"
    )
    error_reason: GenaiFailReason | None = Field(
        default=None,
        description="키워드 한글화 실패 사유"
    )

class BulkKeywordLocalizationResponse(CamelModel):
    """
    키워드 대량 한글화 응답 DTO
    """
    localization_results: List[KeywordResult] = Field(
        ..., 
        description="한글화 완료 키워드 목록"
    )