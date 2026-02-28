from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트(.env 위치) 로드
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

"""
통합 실행 스크립트
1. 더미 데이터 생성 (CSV)
2. PostgreSQL DB에 업로드
"""
import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from generator.generator_master import BulkDataGenerator
from db_loader import main as load_db

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_generator():
    print("\n=== STEP 1: 더미 데이터 생성 ===\n")
    BulkDataGenerator().generate()


def run_loader():
    print("\n=== STEP 2: DB 로딩 ===\n")
    load_db()


if __name__ == "__main__":
    start = time.time()

    run_generator()
    run_loader()

    print(f"\n✅ 전체 완료 (소요시간: {int(time.time()-start)}초)")