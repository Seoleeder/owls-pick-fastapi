#app\schema\review_summary_dto.py

from app.schema.base_dto import CamelModel
from typing import List


# ==========================================
# [Review Summary Request/Response] 리뷰 요약 DTO
# ==========================================

class ReviewSummaryRequest(CamelModel):
    """
    Spring Boot -> FastAPI 단일 게임 리뷰 요약 요청 모델
    """
    game_id: int
    review_score: int
    review_texts: List[str]

class ReviewSummaryResponse(CamelModel):
    """
    FastAPI -> Spring Boot 요약 결과 응답 모델
    """
    summary_text: str | None = None
    positive_keywords: List[str] = []
    negative_keywords: List[str] = []