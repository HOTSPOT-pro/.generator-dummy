# DB Loading Guide

## 적재 순서

1. DROP TABLE
2. CREATE TABLE
3. INSERT MASTER DATA
4. COPY CSV
5. CREATE INDEX

## 실행

python scripts/run_all.py

## 성능 팁

- 인덱스는 데이터 적재 후 생성
- COPY 사용으로 속도 향상
