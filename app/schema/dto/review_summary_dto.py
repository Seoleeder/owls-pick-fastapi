#app\schema\review_summary_dto.py

from typing import List
from pydantic import Field
from app.schema.dto.base_dto import CamelModel
from app.schema.enums.genai_fail_reason import GenaiFailReason


# ==========================================
# [Review Summary Request/Response] 리뷰 요약 DTO
# ==========================================

class ReviewSummaryRequest(CamelModel):
    """
    단일 게임 리뷰 요약 요청 모델
    """
    game_id: int = Field(..., description="게임 ID")
    review_score: int = Field(..., description="스팀 리뷰 스코어")
    review_texts: List[str] = Field(..., description="분석 대상 유저 리뷰 배열")

class ReviewSummaryResponse(CamelModel):
    """
    단일 게임 리뷰 요약 응답 모델
    """
    summary_text: str | None = Field(default=None, description="리뷰 핵심 요약 텍스트")
    positive_keywords: List[str] = Field(default_factory=list, description="긍정 리뷰 추출 키워드")
    negative_keywords: List[str] = Field(default_factory=list, description="부정 리뷰 추출 키워드")
    error_reason: GenaiFailReason | None = Field(default=None, description="요약 실패 사유")