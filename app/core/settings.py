from pydantic_settings import BaseSettings, SettingsConfigDict

# ==========================================
# 정적 인프라 설정 (TOML 파일 매핑)
# ==========================================
class ReviewSettings(BaseSettings):
    semaphore_limit: int

class HltbSettings(BaseSettings):
    semaphore_limit: int

class EmbeddingSettings(BaseSettings):
    output_dimension: int
    max_concurrent_tasks: int
    max_text_length: int
    micro_batch_size: int
    sleep_seconds: float

class Settings(BaseSettings):
    """
    서버 리소스 및 API 동작 관련 정적 임계치 정의
    - 외부 config.toml 파일의 값을 읽어와 객체로 구조화
    """
    review: ReviewSettings
    hltb: HltbSettings
    embedding: EmbeddingSettings
    
    # TOML 파일 자동 매핑 지정
    model_config = SettingsConfigDict(toml_file='config.toml')

# 전역 참조용 설정 객체 생성
settings = Settings()