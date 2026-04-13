#app\services\review_summary_service.py

import os
import json
import asyncio
from google import genai
from google.genai import types

from app.schema.review_summary_dto import ReviewSummaryRequest, ReviewSummaryResponse
from app.services.factories.review_config_factory import ReviewConfigFactory
from app.core.logger import setup_logger
from app.utils.file_util import load_prompt_text, load_json_schema

logger = setup_logger(__name__)

# 리뷰 요약 실패시 마킹
SUMMARY_FAILED_FLAG = "SUMMARY_GENERATION_FAILED"

class ReviewSummaryService:
    def __init__(self):
        
        # 리뷰 요약 전용 환경 변수 로드
        self.model_name = os.getenv("REVIEW_MODEL_NAME", "gemini-2.5-flash")
        self.temperature = float(os.getenv("REVIEW_TEMPERATURE", "0.35")) 

        # 리뷰 세마포어 수 로드 (Rate Limit 방어)
        self.semaphore_limit = int(os.getenv("REVIEW_SEMAPHORE_LIMIT", "5"))

        # Vertex AI 인프라 정보 로드
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_LOCATION", "asia-northeast3")

        # 2. 시스템 프롬프트 및 응답 스키마(JSON) 로드
        self.base_instruction = load_prompt_text("review_summary_instruction.md")
        self.response_schema = load_json_schema("review_summary_schema.json")

        # Vertex AI 클라이언트 초기화
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )

        # API 과부하 방지를 위한 동시성 제어
        self.semaphore = asyncio.Semaphore(self.semaphore_limit)

        logger.info(f"[Review Summary Engine] Initialized (Model: {self.model_name})")

    async def summarize_reviews(self, request: ReviewSummaryRequest, retries: int = 2) -> ReviewSummaryResponse:
        """
        리뷰 요약 파이프라인 실행 (핵심 요약 및 긍/부정 키워드 추출)
        """
        if not request.review_texts:
            return ReviewSummaryResponse()

        # LLM 컨텍스트 주입을 위한 리뷰 텍스트 병합 
        joined_reviews = "\n---\n".join(request.review_texts)
        prompt = f"다음은 게임 ID {request.game_id}의 유저 리뷰들입니다. 이를 바탕으로 요약과 키워드를 추출해주세요.\n\n<Reviews>\n{joined_reviews}\n</Reviews>"
        
        # 실제 데이터 분포(긍/부정 비율)에 따른 동적 설정 빌드
        dynamic_config = ReviewConfigFactory.create_config(
            review_score=request.review_score,
            base_instruction=self.base_instruction,
            response_schema=self.response_schema,
            temperature=self.temperature
        )

        # 일시적 네트워크 오류 대비 재시도 루프
        for attempt in range(retries):
            try:
                # Semaphore를 활용한 커넥션 풀 제어
                async with self.semaphore:
                    response = await self.client.aio.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=dynamic_config
                    )

                # 응답 데이터 누락 검증 (구글 측 차단 또는 빈 응답)
                if not response.candidates or not response.text:
                    logger.warning(f"[Game ID: {request.game_id}] Blocked by Google Safety Filter. Returning {SUMMARY_FAILED_FLAG} flag.")
                    return ReviewSummaryResponse(summary_text=SUMMARY_FAILED_FLAG)

                # 글자 수 제한 또는 안전 필터에 의한 비정상 종료 검증
                finish_reason = response.candidates[0].finish_reason
                if finish_reason and finish_reason.name != "STOP":
                    logger.warning(f"[Game ID: {request.game_id}] Aborted by filter (Reason: {finish_reason.name}). Returning {SUMMARY_FAILED_FLAG} flag.")
                    return ReviewSummaryResponse(summary_text=SUMMARY_FAILED_FLAG)
                # 정상 응답 시 JSON 파싱 및 DTO 매핑
                result_json = json.loads(response.text)
                return ReviewSummaryResponse(**result_json)

            except Exception as e:
                # 네트워크 오류 등 발생 시 지수 백오프(Exponential Backoff) 적용
                if attempt < retries - 1:
                    sleep_time = (attempt + 1) * 2
                    logger.warning(f"[Game ID: {request.game_id}] API Hiccup, retrying in {sleep_time}s... ({str(e)})")
                    await asyncio.sleep(sleep_time)
                    continue
                
                # 최대 재시도 횟수 초과 시 최종 실패 로깅
                logger.error(f"[Review Summary Failed] Exhausted retries for Game ID {request.game_id}. Error: {str(e)}")
                
                raise e