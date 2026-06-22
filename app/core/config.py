#app\core\config.py

import os
import base64
import tempfile
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
        
        # 지정된 경로 하위의 모든 파라미터를 Paginator로 순회하며 조회
        paginator = ssm.get_paginator('get_parameters_by_path')
        response_iterator = paginator.paginate(
            Path=path_prefix,
            WithDecryption=True,
            Recursive=True
        )
        
        for page in response_iterator:
            for parameter in page['Parameters']:
                # 경로 접두사를 제거하여 순수 키 이름만 추출 (/.../log-level -> log-level)
                key_kebab = parameter['Name'].replace(path_prefix, '')
                
                # 환경 변수 주입을 위해 kebab-case를 UPPER_SNAKE_CASE로 변환
                key_upper_snake = key_kebab.replace('-', '_').upper()
                value = parameter['Value']
                
                # Vertex AI 인증 키는 Base64 디코딩 후 임시 파일로 생성하여 환경 변수에 경로 매핑
                if key_kebab == 'vertex-api-key-base64':
                    decoded_key = base64.b64decode(value)
                    
                    fd, path = tempfile.mkstemp(suffix='.json')
                    with os.fdopen(fd, 'wb') as f:
                        f.write(decoded_key)
                    
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path
                    logger.info("Successfully loaded Vertex AI credentials from AWS Parameter Store.")
                else:
                    # 나머지 일반 파라미터는 OS 환경 변수에 직접 주입
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
    else:
        # 로컬 환경: GCP 인증 키(.env) 셋팅 여부 검증
        gcp_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # 키 누락 시 즉시 서버 구동 중단
        if not gcp_credentials:
            logger.error("GOOGLE_APPLICATION_CREDENTIALS is not set in the local .env file.")
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is missing. Check your .env configuration.")
            
    logger.info(f"Application configuration loaded successfully. (Environment: {env})")