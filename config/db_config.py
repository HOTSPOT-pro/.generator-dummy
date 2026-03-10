from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

import os
import base64
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트 경로
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CSV 출력 디렉토리
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')

# --- DB 연결 설정 ---
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'app_db'),
    'user': os.getenv('DB_USER', 'app_user'),
    'password': os.getenv('DB_PASSWORD', 'app_password')
}

# --- 공통 키 로더 ---
def load_key_from_base64(value: str, env_name: str, expected_len: int = 32) -> bytes:
    if not value:
        raise ValueError(f"{env_name} not set")
    key = base64.b64decode(value)
    if len(key) != expected_len:
        raise ValueError(f"{env_name} must be {expected_len} bytes")
    return key

def load_key(env_name: str, expected_len: int = 32) -> bytes:
    value = os.getenv(env_name)
    return load_key_from_base64(value, env_name, expected_len)


ENCRYPTION_PROVIDER = os.getenv("ENCRYPTION_PROVIDER", "kms").lower()
AWS_REGION = os.getenv("AWS_REGION")
KEK_KEY_ID = os.getenv("KEK_KEY_ID")

_HASH_KEY_CACHE = None


def get_hash_key() -> bytes:
    global _HASH_KEY_CACHE
    if _HASH_KEY_CACHE is not None:
        return _HASH_KEY_CACHE

    _HASH_KEY_CACHE = load_key("HASH_KEY", 32)
    return _HASH_KEY_CACHE


def validate_encryption_config():
    if ENCRYPTION_PROVIDER == "kms":
        if not AWS_REGION:
            raise ValueError("AWS_REGION must be set when ENCRYPTION_PROVIDER=kms")
        if not KEK_KEY_ID:
            raise ValueError("KEK_KEY_ID must be set when ENCRYPTION_PROVIDER=kms")
    elif ENCRYPTION_PROVIDER == "local":
        load_key("SECRET_KEY", 32)
    else:
        raise ValueError("ENCRYPTION_PROVIDER must be 'kms' or 'local'")
