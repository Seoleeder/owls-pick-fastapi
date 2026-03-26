import os
import json
import asyncio
from google import genai
from google.genai import types

from app.schema.localization_dto import KeywordResult
from app.core.logger import setup_logger
from app.core.gemini_config import SAFETY_SETTINGS_BLOCK_NONE
from app.utils.file_util import load_prompt_text, load_json_schema

logger = setup_logger(__name__)

class KeywordLocalizationService:
    def __init__(self):
        # 환경 변수 로드 (키워드 매핑은 특히 일관성이 중요하므로 온도를 낮게 유지)
        self.model_name = os.getenv("KEYWORD_MODEL_NAME", "gemini-3.1-flash-lite-preview")
        self.temperature = float(os.getenv("KEYWORD_TEMPERATURE", "0.1"))

        # 리소스 파일 로드 (시스템 지침, JSON 스키마)
        system_instruction = load_prompt_text("keyword_instruction.md")
        response_schema = load_json_schema("keyword_schema.json")

        # Gemini 클라이언트 초기화
        self.client = genai.Client()
        
        # 모델 생성 옵션 설정 (JSON 응답 강제 및 안전 필터 해제)
        self.config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=self.temperature,
            response_mime_type="application/json",
            response_schema=response_schema, 
            safety_settings=SAFETY_SETTINGS_BLOCK_NONE
        )

        # 폴백 모드 발동 시 API Rate Limit(초당 요청 수) 초과를 방지하기 위한 동시성 제어
        self.semaphore = asyncio.Semaphore(50)

        logger.info(f"[Keyword Localization Engine] Initialized (Model: {self.model_name})")


    async def process_keyword_localization(self, keywords: list[str], retries: int = 2) -> list[KeywordResult]:
        """
        [메인 비즈니스 로직] 영문 키워드 배열의 한글화 파이프라인
        - 1차: 벌크(대량) 처리 시도
        - 2차: Safety Filter로 인한 실패 시, 개별 비동기 처리로 우회(Fallback)하여 가용성 극대화
        """
        
        # 처리할 데이터가 없으면 조기 반환(Early Return)
        if not keywords:
            return []

        # 벌크 처리를 위한 사용자 프롬프트 생성
        prompt = f"다음 키워드들을 번역해 주세요:\n{json.dumps(keywords)}"

        # --- [벌크 처리 루프] ---
        # 네트워크 지연이나 일시적 API 오류에 대비한 재시도(Retry) 루프
        for attempt in range(retries):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=self.config
                )

                # API 차단 또는 빈 응답 발생 검증
                if not response.candidates or not response.text:
                    raise ValueError("Blocked by Google")

                # 글자 수 제한 또는 안전 필터에 의한 비정상 종료 검증
                finish_reason = response.candidates[0].finish_reason
                if finish_reason and finish_reason.name != "STOP":
                    raise ValueError(f"Aborted (Reason: {finish_reason.name})")

                # JSON 파싱 
                result_json = json.loads(response.text)
                parsed_list = result_json.get("localizationResults", [])

                # Pydantic 객체로 변환하여 반환
                return [KeywordResult(**item) for item in parsed_list]

            except Exception as e:
                # 일시적인 네트워크 지연이나 500 계열 에러일 경우 지수 백오프(Exponential Backoff) 후 재시도
                if attempt < retries - 1:
                    sleep_time = (attempt + 1) * 2
                    logger.warning(f"Bulk Keyword API Hiccup, retrying in {sleep_time}s... ({str(e)})")
                    await asyncio.sleep(sleep_time)
                    continue
                
                # 재시도를 모두 소진했다면, 특정 태그로 인한 차단일 확률이 높음
                logger.error(f"[Bulk Translation Failed] Exhausted retries. Triggering Individual Async Fallback. Error: {str(e)}")
            
        # --- [단건 비동기 폴백 (Fallback)] ---
        # 벌크 처리가 최종 실패하여 루프를 빠져나왔을 때 실행
            
        logger.info(f"Starting individual fallback for {len(keywords)} keywords...")
        
        # 각 키워드별로 독립적인 코루틴 생성
        tasks = [self._localize_single_keyword(kw) for kw in keywords]
        
        # asyncio.gather를 통해 병렬로 동시 실행 후 결과 취합
        results = await asyncio.gather(*tasks)
        
        return list(results)
           
            
    async def _localize_single_keyword(self, keyword: str) -> KeywordResult:
        """
        [내부 헬퍼 로직] 폴백 시 단일 키워드를 한글화하는 로직. 예외 발생 시 원본 영문 키워드 반환
        """
        prompt = f"다음 키워드를 번역해 주세요:\n[\"{keyword}\"]"
        
        try:
            # Semaphore를 통해 한 번에 실행되는 API 요청 수를 50개로 제한
            async with self.semaphore:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=self.config
                )

                if not response.candidates or not response.text:
                    raise ValueError("Blocked by Google")

                finish_reason = response.candidates[0].finish_reason
                if finish_reason and finish_reason.name != "STOP":
                    raise ValueError(f"Aborted ({finish_reason.name})")

                result_json = json.loads(response.text)
                parsed_list = result_json.get("localizationResults", [])
                
                # 정상 파싱되었다면 번역된 결과 반환
                if parsed_list:
                    return KeywordResult(**parsed_list[0])
                
                # 구조가 맞지 않는 이상 응답 방어
                return KeywordResult(engName=keyword, korName=keyword)

        except Exception as e:
            
            # 필터링에 걸린 키워드이거나 개별 통신에 실패한 경우 영문 원본을 반환
            logger.warning(f"[Isolated Safety Block] Keyword '{keyword}' failed to translate. Returning original. Reason: {str(e)}")
            return KeywordResult(engName=keyword, korName=keyword)