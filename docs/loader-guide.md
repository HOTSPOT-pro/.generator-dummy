# DB Loading Guide

## 적재 순서

1. DROP TABLE
2. CREATE TABLE
3. INSERT MASTER DATA
4. COPY CSV
5. CREATE INDEX

## 최근 스키마 변경 반영

- 가족 신청은 `family_apply` + `family_apply_target` 구조로 분리되었습니다.
- 가족 구성원 삭제 예약 반영을 위한 `family_remove_schedule` 테이블이 추가되었습니다.
- 정책 매핑은 `policy_sub.block_policy_id` 기준으로 관리됩니다.
- 로더는 테이블 단위 커밋을 수행하며, deadlock 감지 시 최대 3회 자동 재시도합니다.

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
