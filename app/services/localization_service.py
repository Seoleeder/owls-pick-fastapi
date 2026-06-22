#app\services\localization_service.py

import os
import json
import asyncio
from google import genai
from google.genai import types

from app.schema.localization_dto import GameItem, LocalizationResult
from app.core.logger import setup_logger
from app.core.gemini_config import SAFETY_SETTINGS_BLOCK_NONE

from app.utils.file_util import load_prompt_text, load_json_schema

logger = setup_logger(__name__)

FAILED_MARK = "LOCALIZATION_FAILED"

class LocalizationService:
    def __init__(self):
        # 번역 전용 환경 변수 로드
        self.model_name = os.getenv("Localization_MODEL_NAME", "gemini-2.5-flash")
        self.temperature = float(os.getenv("Localization_TEMPERATURE", "0.2"))

        # 리소스 파일 (프롬프트, 스키마) 로드 
        system_instruction = load_prompt_text("localization_instruction.md")
        response_schema = load_json_schema("localization_schema.json")

        # Gemini 클라이언트 초기화
        self.project_id = os.getenv("GCP_PROJECT_ID", "owls-pick-2026")
        self.location = os.getenv("GCP_LOCATION", "asia-northeast3")
        
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )
        
        # 모델 생성 옵션(지침, 포맷, 안전 필터) 설정
        self.config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=self.temperature,
            response_mime_type="application/json",
            response_schema=response_schema,
            safety_settings = SAFETY_SETTINGS_BLOCK_NONE
        )

        # 동시성 제어 (Rate Limit 방어를 위해 최대 50개의 코루틴만 API 동시 호출 허용)
        self.semaphore = asyncio.Semaphore(50)
        
        logger.info(f"[Localization] Initialized with modern google-genai SDK (Model: {self.model_name})")

    async def localize_task (self, game: GameItem, retries: int = 2) -> LocalizationResult:
        """
        단일 게임 데이터의 한글화(Localization) 프로세스
        """
        # 원본 데이터(설명, 스토리라인) 부재 시 조기 반환
        if not game.description and not game.storyline:
            return LocalizationResult(game_id=game.game_id, description_ko=None, storyline_ko=None)
        
        # 필드별 유효 데이터 존재 여부 검증
        has_desc = bool(game.description and game.description.strip())
        has_story = bool(game.storyline and game.storyline.strip())
            
        # 유효한 데이터만 추출하여 프롬프트 컨텍스트 구성
        prompt_parts = []
        if game.description and game.description.strip():
            prompt_parts.append(f"<Description>\n{game.description}\n</Description>")
        if game.storyline and game.storyline.strip():
            prompt_parts.append(f"<Storyline>\n{game.storyline}\n</Storyline>")
        
        prompt = "\n\n".join(prompt_parts)    
        
        # 일시적인 네트워크 오류 등을 대비한 API 호출 및 재시도 루프
        for attempt in range(retries):
            try:
                # Semaphore를 획득하여 동시 API 호출 수 통제
                async with self.semaphore:  
                    response = await self.client.aio.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=self.config
                    )
                
                # API 차단 또는 빈 응답 발생 시 즉시 실패 처리
                if not response.candidates or not response.text:
                    logger.warning(f"[Localization] Blocked by Google Safety Filter (No content returned). Skipping - GameId: {game.game_id}")
                    return self._build_fallback_result(game.game_id, has_desc, has_story)

                # 정상 종료 외 모든 케이스는 불완전 응답으로 간주하여 즉시 실패 처리
                finish_reason = response.candidates[0].finish_reason
                if finish_reason and finish_reason.name != "STOP":
                    logger.warning(f"[Localization] Aborted by Gemini (Reason: {finish_reason.name}). Skipping - GameId: {game.game_id}")
                    return self._build_fallback_result(game.game_id, has_desc, has_story)
                
                # 응답 JSON 파싱 및 결과 매핑
                result_json = json.loads(response.text)
            
                # 원본을 주지 않았다면(has_desc/has_story == False), 무조건 None 처리
                final_desc_ko = result_json.get("description_ko") if has_desc else None
                final_story_ko = result_json.get("storyline_ko") if has_story else None
    
                return LocalizationResult(
                    game_id=game.game_id,
                    description_ko=final_desc_ko,
                    storyline_ko=final_story_ko
                )
            except Exception as e:
                
                # 일시적 오류 시 대기 시간 점진적 증가 후 재시도
                if attempt < retries - 1:
                    sleep_time = (attempt + 1) * 2
                    logger.warning(f"[Localization] API Hiccup, retrying... GameId: {game.game_id} ({str(e)})")
                    await asyncio.sleep(sleep_time)
                    continue
                
                # 최대 재시도 횟수 초과 시 최종 실패 처리
                logger.error(f"[Localization] Final Failure - GameId: {game.game_id} | Error: {str(e)}")
                
                return self._build_fallback_result(game.game_id, has_desc, has_story)


    async def process_bulk_localizations(self, games: list[GameItem]) -> list[LocalizationResult]:
        """
        대량의 게임 데이터 비동기 병렬 한글화 파이프라인
        """
        total_count = len(games)
        logger.debug(f"[Localization] Starting async concurrent localization for {len(games)} items.")
        
        # 개별 게임 데이터를 비동기 작업 단위(Coroutine) 리스트로 변환
        # 실행 대기 상태의 코루틴 객체들을 생성하여 배치(Batch) 준비
        tasks = [self.localize_task(game) for game in games]
        
        # 모든 코루틴을 이벤트 루프에 등록하여 병렬 실행 및 결과 집계
        # await: 모든 비동기 작업이 완료될 때까지 대기하는 동기화 포인트(Barrier) 역할
        results = await asyncio.gather(*tasks)
        
        logger.debug(f"[Localization] Localization completed for {total_count} items.")
        
        return list(results)
    
    
    def _build_fallback_result(self, game_id: int, has_desc: bool, has_story: bool) -> LocalizationResult:
        """
        실패 상태(FAILED_MARK) DTO 생성 팩토리 메서드
        """
        return LocalizationResult(
            game_id=game_id, 
            description_ko=FAILED_MARK if has_desc else None, 
            storyline_ko=FAILED_MARK if has_story else None
        )