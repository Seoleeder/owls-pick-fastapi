#app\core\config.py

import os
import boto3
from dotenv import load_dotenv
from app.core.logger import setup_logger

logger = setup_logger(__name__)

def _load_prod_config_from_ssm() -> None:
    """
    운영 환경의 동적 설정값 및 자격 증명을 AWS SSM에서 일괄 로드함
    """
    try:
        # EC2 IAM Role을 기반으로 AWS SSM 클라이언트 생성
        ssm = boto3.client('ssm', region_name='ap-northeast-2')
        path_prefix = '/owls-pick/prod/fastapi/'
        
        # 지정된 경로 하위의 모든 파라미터 조회
        paginator = ssm.get_paginator('get_parameters_by_path')
        response_iterator = paginator.paginate(
            Path=path_prefix,
            WithDecryption=True,
            Recursive=True
        )
        
        for page in response_iterator:
            for parameter in page['Parameters']:
                # 경로 접두사를 제거하여 키 이름만 추출 (/.../log-level -> log-level)
                key_kebab = parameter['Name'].replace(path_prefix, '')
                
                # UPPER_SNAKE_CASE 변환
                key_upper_snake = key_kebab.replace('-', '_').upper()
                value = parameter['Value']
                
                os.environ[key_upper_snake] = value
                    
        logger.info("Successfully loaded all dynamic configurations from AWS Parameter Store.")
        
    except Exception as e:
        logger.error(f"Failed to load configurations from Parameter Store: {str(e)}")
        raise RuntimeError("SSM configurations initialization failed.") from e

def init_config():
    """
    앱 구동 환경(APP_ENV)에 따른 설정 파일 로드 및 초기화 진행
    """
    
    # 로컬 개발용 .env 환경 변수 로드
    load_dotenv()
    
    # 실행 환경 판별 (미지정 시 local로 간주)
    env = os.getenv("APP_ENV", "local")
    
    if env == "prod":
        # 운영 환경: SSM에서 동적 파라미터 조회 및 적용
        _load_prod_config_from_ssm()
        
    # OpenAI API 키 로드 여부 최종 검증
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY is not set in the environment variables.")
        raise ValueError("OPENAI_API_KEY is missing. Check your .env or AWS SSM configuration.")
        
    logger.info(f"Application configuration loaded successfully. (Environment: {env})")