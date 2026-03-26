#app\api\localization.py

from fastapi import APIRouter
from app.schema.localization_dto import BulkLocalizationRequest, BulkLocalizationResponse, BulkKeywordLocalizationResponse, KeywordLocalizationRequest
from app.services.localization_service import LocalizationService
from app.services.keyword_localization_service import KeywordLocalizationService
from app.core.logger import setup_logger
from fastapi import HTTPException

logger = setup_logger(__name__)
router = APIRouter()

# 서비스 인스턴스 싱글톤(Singleton) 생성
localization_service = LocalizationService()
keyword_service = KeywordLocalizationService()

@router.post("/bulk", response_model=BulkLocalizationResponse)
async def localize_bulk_games(req: BulkLocalizationRequest):
    """
    대량 게임 데이터 현지화(Localization) API
    Gemini AI 기반의 비동기 병렬 처리를 통해 대량의 게임 데이터를 번역하여 반환
    """
    game_count = len(req.games)
    logger.info(f"Received Request: Bulk Localization for {game_count} games.")
    
    # 비동기 병렬 번역 처리 위임
    results = await localization_service.process_bulk_localizations(req.games)
    
    logger.info(f"Localization Completed: Returning {len(results)} results.")
    
    return BulkLocalizationResponse(success=True, results=results)


@router.post("/keywords", response_model=BulkKeywordLocalizationResponse)
async def localize_bulk_keywords(req: KeywordLocalizationRequest):
    """
    대량 게임 키워드 현지화(Localization) API
    청크 단위의 키워드 리스트를 받아 일괄 번역하여 반환
    """
    kw_count = len(req.keywords)
    logger.info(f"Received Request: Keyword Localization for {kw_count} keywords.")
    
    # 키워드 번역 서비스 호출
    try:
        results = await keyword_service.process_keyword_localization(req.keywords)
        logger.info(f"Keyword Localization Completed: Returning {len(results)} results.")
        
        return BulkKeywordLocalizationResponse(localizationResults=results)
        
    except Exception as e:
        # 실패 시 500 에러를 반환하여 Spring Boot에서 캐치하도록 유도
        raise HTTPException(status_code=500, detail=str(e))

