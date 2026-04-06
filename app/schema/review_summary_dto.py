#app\schema\review_summary_dto.py

from pydantic import BaseModel
from typing import List

# ==========================================
# [Review Summary Request/Response] 리뷰 요약 DTO
# ==========================================

class ReviewSummaryRequest(BaseModel):
    """
    Spring Boot -> FastAPI 단일 게임 리뷰 요약 요청 모델
    """
    gameId: int
    reviewScore: int
    reviewTexts: List[str]

class ReviewSummaryResponse(BaseModel):
    """
    FastAPI -> Spring Boot 요약 결과 응답 모델
    """
    summaryText: str | None = None
    positiveKeywords: List[str] = []
    negativeKeywords: List[str] = []