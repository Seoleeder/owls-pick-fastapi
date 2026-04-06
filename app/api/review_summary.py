#app\api\review_summary.py

import traceback
from fastapi import APIRouter, HTTPException
from app.schema.review_summary_dto import ReviewSummaryRequest, ReviewSummaryResponse
from app.services.review_summary_service import ReviewSummaryService
from app.core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# 싱글톤 서비스 인스턴스
summary_service = ReviewSummaryService()

@router.post("/reviews", response_model=ReviewSummaryResponse)
async def summarize_game_reviews(req: ReviewSummaryRequest):
    """
    게임 리뷰 요약 및 긍정/부정 키워드 추출 API
    Spring Boot 서버에서 단일 게임 단위로 호출
    """
    logger.info(f"Received Request: Review Summary for Game ID {req.gameId} ({len(req.reviewTexts)} reviews)")
    
    try:
        # 서비스 계층 호출
        result = await summary_service.summarize_reviews(req)
        logger.info(f"Review Summary Completed for Game ID {req.gameId}.")
        
        return result
        
    except Exception as e:
        # 내부 로직 실패 시 HTTP 500 에러를 반환하여 Spring Boot의 CustomException 유발
        logger.error(f"Python Internal Error:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))