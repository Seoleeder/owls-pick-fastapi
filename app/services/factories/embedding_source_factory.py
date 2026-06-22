#app\services\factories\embedding_source_factory.py

from app.schema.embedding_dto import EmbeddingData

class EmbeddingSourceFactory:
    """
    게임 데이터를 임베딩용 텍스트 템플릿으로 변환하는 팩토리
    """
    @staticmethod
    def create_source_text(game: EmbeddingData, max_length: int) -> str:
        parts = [f"Game Title: {game.title}"]
        
        if game.description: parts.append(f"Description: {game.description}")
        
        if game.genres: parts.append(f"Genres: {game.genres}")
        if game.themes: parts.append(f"Themes: {game.themes}")
        
        if game.keywords: parts.append(f"Keywords: {', '.join(game.keywords)}")
        
        if game.main_story: parts.append(f"Playtime: {game.main_story}")
        
        return "\n".join(parts)[:max_length].strip()