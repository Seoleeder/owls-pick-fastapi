#app\services\hltb_sync_service.py

import os
import asyncio
from howlongtobeatpy import HowLongToBeat, HowLongToBeatEntry

from app.schema.dto.hltb_dto import HltbSyncResponse, SyncStatus
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class HltbSyncService:
    def __init__(self):
        # IP 차단(Rate Limit) 방지를 위한 동시성 제어 설정
        self.semaphore_limit = int(os.getenv("HLTB_SEMAPHORE_LIMIT", "10"))
        self.semaphore = asyncio.Semaphore(self.semaphore_limit)
        
        logger.info(f"[HLTB-Sync] Initialized with Semaphore limit: {self.semaphore_limit}")
        
    @staticmethod
    def _normalize_hours(hours: float) -> float | None:
        """
        유효하지 않은 플레이타임 값(0 이하, 누락 등)을 None으로 정규화
        """
        if hours is None or hours <= 0:
            return None
        return float(hours)

    async def scrape_playtime(self, game_name: str) -> HltbSyncResponse:
        """
        HowLongToBeat 플레이타임 스크래핑 파이프라인
        """
        
        # 설정된 세마포어 내에서만 스크래핑 동시 실행 허용
        async with self.semaphore:
            try:
                logger.debug(f"[HLTB-Sync] Searching playtime for: {game_name}")
                
                # 대량 병렬 요청 시 대상 서버 부하 및 봇 탐지 우회를 위한 최소 지연 시간
                await asyncio.sleep(0.5)

                # HLTB 비동기 검색 요청
                results : list[HowLongToBeatEntry] = await HowLongToBeat().async_search(game_name)

                # 검색된 게임 데이터가 없을 경우 예외 처리 (NOT_FOUND)
                if not results:
                    logger.debug(f"[HLTB-Sync] No results found for: {game_name}")
                    return HltbSyncResponse(status=SyncStatus.NOT_FOUND)

                # 다수의 결과 중 원본 검색어와 유사도(Similarity)가 가장 높은 단일 데이터 추출
                best_match: HowLongToBeatEntry = max(results, key=lambda element: element.similarity)
                logger.debug(f"[HLTB-Sync] Best match found: {best_match.game_name} (Similarity: {best_match.similarity})")
                
                # 정규화 진행
                normalized_story = self._normalize_hours(best_match.main_story)
                normalized_extra = self._normalize_hours(best_match.main_extra)
                normalized_completionist = self._normalize_hours(best_match.completionist)

                # 유효한 플레이타임 데이터가 없는 경우 (NO_DATA)
                if normalized_story is None and normalized_extra is None and normalized_completionist is None:
                    logger.debug(f"[HLTB-Sync] Game found, but no playtime data: '{best_match.game_name}'")
                    return HltbSyncResponse(status=SyncStatus.NO_DATA)

                # 추출된 데이터를 응답 DTO 규격에 맞춰 매핑 후 반환 (SUCCESS)
                return HltbSyncResponse(
                    main_story=normalized_story,
                    main_extra=normalized_extra,
                    completionist=normalized_completionist,
                    status=SyncStatus.SUCCESS
                )
            except Exception as e:
                # 스크래핑 중 발생하는 예외(네트워크 타임아웃, 접속 차단 등) 방어 및 상태 반환
                logger.error(f"[HLTB-Sync] Failed to scrape - Game: {game_name} | Error: {str(e)}")
                return HltbSyncResponse(status=SyncStatus.FAILED)