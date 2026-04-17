import os
import asyncio
import logging
from typing import List
from google import genai
from google.genai import types
from app.services.factories.embedding_source_factory import EmbeddingSourceFactory

from app.schema.embedding_dto import RawGameData, EmbeddingResult, EmbeddingStatus

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Owls 챗봇 검색용 게임 메타데이터 임베딩 서비스
    """
    
    def __init__(self):
        # 모델 사양 및 동시성 제어 환경 변수 로드
        self.model_name = os.getenv("EMBEDDING_MODEL_NAME", "gemini-embedding-001")
        self.semaphore_limit = int(os.getenv("EMBEDDING_MAX_CONCURRENT_TASKS", "10"))
        
        # Vertex AI 프로젝트 및 리전 설정
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_LOCATION", "asia-northeast3")
        
        # 출력 차원 축소 및 토큰 제한 설정
        self.output_dimension = 768
        self.max_text_length = int(os.getenv("EMBEDDING_MAX_TEXT_LENGTH", "4000"))
        
        # 마이크로 배치 및 지연(Sleep) 설정
        self.micro_batch_size = int(os.getenv("EMBEDDING_MICRO_BATCH_SIZE", "10"))
        self.sleep_seconds = float(os.getenv("EMBEDDING_SLEEP_SECONDS", "2.0"))

        # Vertex AI 클라이언트 초기화
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )

        # API Rate Limit 방어용 세마포어 설정
        self.semaphore = asyncio.Semaphore(self.semaphore_limit)

        logger.info(f"[Embedding Engine] Initialized (Model: {self.model_name}, Dimension: {self.output_dimension})")

    async def generate_embedding(self, game: RawGameData, retries: int = 2) -> EmbeddingResult:
        """
        단일 게임 데이터 벡터 임베딩 변환
        """
        # 팩토리를 이용한 임베딩용 소스 텍스트 추출
        source_text = EmbeddingSourceFactory.create_source_text(game, self.max_text_length)
        
        # 유효 텍스트 부족 시 임베딩 생략 및 실패 상태 반환
        if not source_text or len(source_text) < 5:
            logger.warning(f"[Game ID: {game.game_id}] Skip: Insufficient text.")
            return EmbeddingResult(game_id=game.game_id, vector=None, status=EmbeddingStatus.FAILED)

        # 지수 백오프 기반 API 호출
        for attempt in range(retries + 1):
            try:
                async with self.semaphore:
                    response = await self.client.aio.models.embed_content(
                        model=self.model_name,
                        contents=source_text,
                        config=types.EmbedContentConfig(
                            task_type="RETRIEVAL_DOCUMENT",
                            title=game.title,
                            output_dimensionality=self.output_dimension
                        )
                    )

                # 정상 응답 시 결과 객체 매핑 및 반환
                return EmbeddingResult(
                    game_id=game.game_id,
                    vector=response.embeddings[0].values,
                    source_text=source_text,
                    status=EmbeddingStatus.SUCCESS
                )

            except Exception as e:
                # API 호출 실패 시 대기 후 바로 재시도
                if attempt < retries:
                    sleep_time = (attempt + 1) * 2
                    logger.warning(f"[Game ID: {game.game_id}] Retry {attempt+1}/{retries} after {sleep_time}s")
                    await asyncio.sleep(sleep_time)
                    continue
                
                # 최대 재시도 횟수 초과 시 최종 실패 로깅 및 실패 상태 고립
                logger.error(f"[Embedding Failed] Game ID {game.game_id}: {str(e)}")
                return EmbeddingResult(game_id=game.game_id, vector=None, status=EmbeddingStatus.FAILED)

    async def process_batch(self, batch: List[RawGameData]) -> List[EmbeddingResult]:
        """
        배치 단위 게임 데이터 비동기 병렬 임베딩 처리
        """
        results: List[EmbeddingResult] = []
        total_games = len(batch)
        
        logger.info(f"[Embedding Batch] Processing {total_games} games in micro-batches of {self.micro_batch_size}.")

        for i in range(0, total_games, self.micro_batch_size):
            # 배치 데이터를 설정된 마이크로 배치 단위로 분할
            micro_batch = batch[i : i + self.micro_batch_size]
            
            # 비동기 태스크 병렬 실행
            tasks = [self.generate_embedding(game) for game in micro_batch]
            micro_batch_results = await asyncio.gather(*tasks)
            
            # 결과 리스트에 병합
            results.extend(micro_batch_results)
            
            # 마지막 배치가 아닐 경우, 지연 시간 부여
            if i + self.micro_batch_size < total_games:
                logger.info(f"[Embedding Batch] Processed {i + len(micro_batch)}/{total_games}. Sleeping for {self.sleep_seconds}s...")
                await asyncio.sleep(self.sleep_seconds)
                
        logger.info("[Embedding Batch] All micro-batches processed successfully.")
        return results