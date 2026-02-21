# DB Loading Guide

## 적재 순서

1. DROP TABLE
2. CREATE TABLE
3. INSERT MASTER DATA
4. COPY CSV
5. CREATE INDEX

## 실행

더미 전체 실행 (CSV 생성 + DB 적재)
```
python scripts/run_all.py
```

팀원/가족 테스트 데이터 오버레이
```
python scripts/team_seed.py
```

권장 순서
1. `python scripts/run_all.py`
2. `python scripts/team_seed.py`

## 팀 시드 설정

- `scripts/team_fixture.json`을 수정한 뒤 `team_seed.py`를 실행합니다.
- 상세 필드 규칙과 예시는 `docs/team-seed-guide.md`를 참고하세요.

## 성능 팁

- 인덱스는 데이터 적재 후 생성
- COPY 사용으로 속도 향상
