#app\api\keyword_localization.py

import traceback
from fastapi import APIRouter, HTTPException, Depends
from app.schema.dto.keyword_localization_dto import KeywordLocalizationRequest, BulkKeywordLocalizationResponse
from app.services.keyword_localization_service import KeywordLocalizationService
from app.core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

def get_keyword_localization_service() -> KeywordLocalizationService:
    """
    LocalizationService 의존성 주입(DI)용 팩토리 함수
    """
    return KeywordLocalizationService()

@router.post("/keywords/bulk", response_model=BulkKeywordLocalizationResponse)
async def localize_bulk_keywords(
    req: KeywordLocalizationRequest,
    service: KeywordLocalizationService = Depends(get_keyword_localization_service)
    ):
    """
    대량 게임 키워드 한글화 API
    """
    kw_count = len(req.keywords)
    logger.info(f"Received Request: Keyword Localization for {kw_count} keywords.")
    
    # 키워드 한글화 서비스 호출
    try:
        results = await service.process_keyword_localization(req.keywords)
        logger.info(f"Keyword Localization Completed: Returning {len(results)} results.")
        return BulkKeywordLocalizationResponse(localization_results=results)
        
    except Exception as e:
        # 실패 시 500 에러를 반환하여 Spring Boot에서 캐치하도록 유도
        logger.error(f"Python Internal Error (Keyword Localization):\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))