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

# --- AES-256 암호화 키 (32 bytes) ---
def load_key(env_name: str, expected_len: int = 32) -> bytes:
    value = os.getenv(env_name)
    if not value:
        raise ValueError(f"{env_name} not set")

    key = base64.b64decode(value)

    if len(key) != expected_len:
        raise ValueError(f"{env_name} must be {expected_len} bytes")

    return key


SECRET_KEY = load_key("SECRET_KEY", 32)
HASH_KEY = load_key("HASH_KEY", 32)