#app\utils\file_util.py

import json
from pathlib import Path
from app.core.logger import setup_logger

logger = setup_logger(__name__)

# app 폴더 경로를 절대 경로로 추적
BASE_DIR = Path(__file__).resolve().parent.parent 


def load_prompt_text(filename: str) -> str:
    """
    resources/prompts 폴더에서 마크다운(.md) 또는 텍스트 파일 로드
    System Instruction 로드할 때 사용
    """
    file_path = BASE_DIR / "resources" / "prompts" / "system_instruction" / filename
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError as e:
        logger.error(f"Text prompt file not found: {e}")
        raise