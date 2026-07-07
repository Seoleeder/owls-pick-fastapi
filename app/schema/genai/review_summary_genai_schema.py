from pydantic import BaseModel, Field
from typing import List

# ==========================================
# [OpenAI Structured Outputs] 리뷰 요약 파싱 스키마
# ==========================================

class ReviewSummaryResponseSchema(BaseModel):
    """
    스팀 리뷰 요약 및 키워드 추출 파싱용 응답 스키마
    """
    summary_text: str = Field(
        ..., 
        description="전체 리뷰의 핵심 여론을 반영한 2~3문장 분량의 구어체 한국어 요약 텍스트"
    )
    positive_keywords: List[str] = Field(
        ..., 
        description="리뷰 내 빈출 장점을 나타내는 명사형 단어 5개",
        min_length=5,
        max_length=5
    )
    negative_keywords: List[str] = Field(
        ..., 
        description="리뷰 내 빈출 단점을 나타내는 명사형 단어 5개",
        min_length=5,
        max_length=5
    )