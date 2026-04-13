import traceback
from fastapi import APIRouter, HTTPException, Query

from app.schema.hltb_dto import HltbSyncResponse
from app.services.hltb_sync_service import HltbSyncService
from app.core.logger import setup_logger

router = APIRouter()

logger = setup_logger(__name__)

# 서비스 인스턴스 싱글톤(Singleton) 생성
hltb_service = HltbSyncService()

@router.get("/scrape", response_model=HltbSyncResponse)
async def scrape_hltb_playtime(
    game_name: str = Query(..., description="검색할 게임의 영문 원본 타이틀")
):
    """
    HowLongToBeat 스크래핑 및 플레이타임 반환 API
    """
    logger.info(f"Received Request: HLTB Scrape for game '{game_name}'")
    
    try:
        # 플레이타임 스크래핑 서비스 호출
        result = await hltb_service.scrape_playtime(game_name)
        
        logger.info(f"HLTB Scrape Completed for '{game_name}'. Status: {result.status}")
        return result
        
    except Exception as e:
        # 파이썬 내부 로직 실패 시 HTTP 500 에러를 반환
        logger.error(f"Python Internal Error during HLTB scraping:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))