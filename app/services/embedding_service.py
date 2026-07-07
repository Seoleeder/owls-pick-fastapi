#app\services\embedding_service.py

import os
import asyncio
from typing import List
from openai import AsyncOpenAI

from app.core.logger import setup_logger
from app.schema.enums.genai_fail_reason import GenaiFailReason
from app.services.factories.embedding_source_factory import EmbeddingSourceFactory

from app.schema.dto.embedding_dto import EmbeddingData, EmbeddingResult, EmbeddingStatus

logger = setup_logger(__name__)

class EmbeddingService:
    """
    Owls 챗봇 검색용 게임 메타데이터 임베딩 서비스
    """
    
    def __init__(self):
        # 임베딩 전용 환경 변수 로드
        self.model_name = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
        self.output_dimension = int(os.getenv("EMBEDDING_OUTPUT_DIMENSION", "768"))
        self.semaphore_limit = int(os.getenv("EMBEDDING_MAX_CONCURRENT_TASKS", "10"))
        self.max_text_length = int(os.getenv("EMBEDDING_MAX_TEXT_LENGTH", "4000"))
        
        # API Rate Limit 방어를 위한 배치 크기 및 지연 시간 설정
        self.micro_batch_size = int(os.getenv("EMBEDDING_MICRO_BATCH_SIZE", "10"))
        self.sleep_seconds = float(os.getenv("EMBEDDING_SLEEP_SECONDS", "1.0"))

        # 비동기 OpenAI 클라이언트 초기화
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # API Rate Limit 방어 및 서버 과부하 방지를 위한 동시성 제어
        self.semaphore = asyncio.Semaphore(self.semaphore_limit)

        logger.info(f"[GenAI-Embedding] Initialized with AsyncOpenAI SDK (Model: {self.model_name}, Dimension: {self.output_dimension})")

    async def generate_embeddings(self, batch: List[EmbeddingData], retries: int = 2) -> List[EmbeddingResult]:
        """
        대량의 게임 데이터 비동기 병렬 임베딩 파이프라인.
        """
        results: List[EmbeddingResult] = []
        total_games = len(batch)
        
        logger.debug(f"[GenAI-Embedding] Processing {total_games} games in micro-batches of {self.micro_batch_size}.")

        # 마이크로 배치 단위로 분할하여 순차 처리함
        for i in range(0, total_games, self.micro_batch_size):
            micro_batch = batch[i : i + self.micro_batch_size]
            
            valid_games = []
            source_texts = []
            
            # 팩토리를 통해 게임 데이터를 단일 텍스트로 병합함
            for game in micro_batch:
                text = EmbeddingSourceFactory.create_source_text(game, self.max_text_length)
                
                # 기준 길이 미만의 텍스트는 API 호출에서 제외하고 에러 상태를 결과에 적재함
                if not text or len(text) < 5:
                    logger.debug(f"[GenAI-Embedding] Skip: Insufficient text - GameId: {game.game_id}")
                    results.append(self._build_fallback_result(game.game_id, GenaiFailReason.INSUFFICIENT_DATA))
                else:
                    valid_games.append(game)
                    source_texts.append(text)
                    
            
            # 유효 데이터가 없을 경우 API 요청 생략
            if not valid_games:
                continue

            # 네트워크 지연 및 API 일시 오류 대응을 위한 재시도 루프
            for attempt in range(retries + 1):
                try:
                    # 동시성 한도 내에서만 API 요청 실행
                    async with self.semaphore:
                        # 텍스트 배열을 단일 API 요청으로 일괄 전송함
                        response = await self.client.embeddings.create(
                            model=self.model_name,
                            input=source_texts,
                            dimensions=self.output_dimension
                        )

                    # API 응답을 원본 데이터와 1:1 매핑하여 성공 상태 할당
                    for idx, game in enumerate(valid_games):
                        results.append(EmbeddingResult(
                            game_id=game.game_id,
                            vector=response.data[idx].embedding,
                            status=EmbeddingStatus.SUCCESS,
                            error_reason=None
                        ))
                    
                    # 정상 처리 시 재시도 루프 탈출
                    break

                except Exception as e:
                    # 일시적 오류 발생 시 점진적 대기 후 재시도
                    if attempt < retries:
                        sleep_time = (attempt + 1) * 2
                        logger.warning(f"[GenAI-Embedding] Batch API Error, retrying {attempt+1}/{retries}... ({str(e)})")
                        await asyncio.sleep(sleep_time)
                        continue
                    
                    # 재시도 횟수 초과 시 개별 재시도를 생략하고 마이크로 배치 전체를 실패 처리함
                    # 상태 복구는 메인 서버로 위임함
                    logger.error(f"[GenAI-Embedding] Batch Final Failure | Error: {str(e)}")
                    for game in valid_games:
                        results.append(self._build_fallback_result(game.game_id, GenaiFailReason.NETWORK_ERROR))
            
            # 다음 마이크로 배치 실행 전 API 한도 보호를 위한 지연 대기
            if i + self.micro_batch_size < total_games:
                logger.debug(f"[GenAI-Embedding] Processed {i + len(micro_batch)}/{total_games}. Sleeping for {self.sleep_seconds}s...")
                await asyncio.sleep(self.sleep_seconds)
                
        logger.debug("[GenAI-Embedding] All micro-batches processed successfully.")
        return results
    
    def _build_fallback_result(self, game_id: int, reason: GenaiFailReason) -> EmbeddingResult:
        """
        실패 건에 대한 에러 응답 객체 생성
        """
        return EmbeddingResult(
            game_id=game_id, 
            vector=None, 
            status=EmbeddingStatus.FAILED,
            error_reason=reason
        )