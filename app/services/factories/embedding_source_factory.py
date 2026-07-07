#app\services\factories\embedding_source_factory.py

from app.schema.dto.embedding_dto import EmbeddingData

class EmbeddingSourceFactory:
    """
    게임 메타데이터를 벡터 임베딩 모델의 입력 컨텍스트(문자열)로 변환함.
    """
    @staticmethod
    def create_source_text(game: EmbeddingData, max_length: int) -> str:
        parts = [f"Game Title: {game.title}"]
        
        if game.description:
            parts.append(f"Description: {game.description}")
        
        
        # 배열 형태의 태그 데이터를 쉼표 기준으로 병합하여 단일 텍스트로 구성함
        if game.genres:
            parts.append(f"Genres: {', '.join(game.genres)}")
            
        if game.themes:
            parts.append(f"Themes: {', '.join(game.themes)}")
            
        if game.keywords:
            parts.append(f"Keywords: {', '.join(game.keywords)}")
            
        # 숫자형 데이터에 단위를 명시하여 임베딩 시 의미를 명확히 한정함
        if game.main_story:
            parts.append(f"Playtime: {game.main_story} minutes")
        
        # 설정된 최대 문자열 길이 만큼 추출 후 반환
        return "\n".join(parts)[:max_length].strip()