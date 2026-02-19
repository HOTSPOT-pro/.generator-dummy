# HOTSPOT Dummy Data Generator

통신사 가족 데이터 공유/차단 정책 서비스를 위한
**대규모 더미 데이터 생성 및 PostgreSQL 적재 도구**

✔ 100만 사용자 생성  
✔ 가족 데이터 공유 구조 생성  
✔ 정책/차단/선물 데이터 시뮬레이션  
✔ AES 암호화 + Blind Index 적용  
✔ PostgreSQL COPY 기반 고속 적재  

---
## 📦 프로젝트 구조
```
.generator-dummy/
├── scripts/
│   ├── run_all.py            # 통합 실행
│   ├── db_loader.py          # DB 로딩
│   ├── team_seed.py          # 팀원/가족 테스트 데이터 오버레이
│   ├── team_fixture.json     # 팀원/가족 테스트 fixture
│   └── generator/
│       ├── generator_master.py
│       ├── utils.py
│       ├── constants.py
│       └── csv_writer.py
├── config/
│   └── db_config.py
├── sql/
│   ├── 01_drop_tables.sql
│   ├── 02_create_tables.sql
│   ├── 03_insert_master_data.sql
│   └── 04_create_indexes.sql
├── output/                   # 생성된 CSV
├── docs/
│   ├── data-rules.md
│   ├── encryption.md
│   └── loader-guide.md
├── .env
├── .env.example
└── requirements.txt
```

---
## 🚀 주요 기능
✔ 사용자 & 회선 생성
- 1,000,000 회원
- 1,000,000 회선 생성

✔ 가족 그룹 구성
- 2~8명 가족 구성
- 역할:
  - OWNER
  - PARENT
  - CHILD
- 데이터 공유 정책:
  - FIFO
  - PRIORITY

✔ 정책 & 차단 시스템 시뮬레이션
- 시간 차단 정책 적용
- 앱 서비스 차단
- 정책 적용 알림 자동 생성

✔ 데이터 선물 이벤트
- 부모 → 자녀 데이터 선물
- 요금제 기준 선물 용량 제한
- 일 단위 요금제 / 1.5GB 요금제는 선물 데이터 생성 제외

✔ 개인정보 보호 설계
- 전화번호 AES 암호화 저장
- Blind Index 해시 검색 지원

---
## ⚙️ 설치
```
pip install -r requirements.txt
```

---
## 🔐 환경변수 설정
.env.example 복사:
```
cp .env.example .env
```

환경에 맞게 수정:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hotspot
DB_USER=postgres
DB_PASSWORD=postgres

# AES 256 key (32 bytes)
SECRET_KEY=your_32byte_secret_key_here

# HMAC key for blind index
HASH_KEY=your_base64_hmac_key_here
```

> .env가 없으면 config/db_config.py 기본값 사용

---
## ▶ 실행 방법
더미 전체 실행 (CSV 생성 + DB 적재)
```
python scripts/run_all.py
```

팀원/가족 테스트 데이터 오버레이
```
python scripts/team_seed.py
```

> `scripts/team_fixture.json` 수정 후 실행  
> 권장 순서: `python scripts/run_all.py` -> `python scripts/team_seed.py`

### team_fixture.json 가이드
- `members`: 팀원 사용자 정의
- `create_social_account=false`: 소셜 계정 미생성(신규 소셜 가입 플로우 테스트용)
- `families`: `member_key` 기준 가족 구성 정의

---
## 📊 생성 데이터 규모
| 테이블                 | 예상 건수      |
| ------------------- | ---------- |
| member              | 1,000,000  |
| subscription        | 1,000,000  |
| family              | 250,000    |
| family_sub          | ~860,000   |
| notification_allow  | 4,000,000  |
| blocked_service_sub | ~650,000   |
| policy_sub          | ~200,000   |
| notification        | ~1,000,000 |

---
## 🔐 암호화 설계
**AES 암호화**

전화번호는 AES-256-CBC 방식으로 저장됩니다.
```
Base64( IV + CipherText )
```

✔ 동일 값도 매번 다른 암호문 생성  
✔ Java/Spring에서 동일 키로 복호화 가능

**Blind Index**

전화번호 검색을 위한 해시:
```
HMAC-SHA256(phone, HASH_KEY)
```

✔ 평문 검색 가능  
✔ 개인정보 노출 방지  

---
## ⚡ 성능 최적화 전략
✔ PostgreSQL COPY 사용  
✔ 인덱스 후 생성 전략   
✔ 버퍼링 CSV 쓰기  
✔ 대량 데이터 처리 최적화  

---
## 🧠 활용 목적
✔ API 성능 테스트  
✔ 정책 엔진 검증  
✔ 데이터 공유 로직 테스트  
✔ 대용량 트래픽 시뮬레이션  
✔ 보안 설계 검증  

---
## 📚 문서
| 문서              | 설명        |
| --------------- | --------- |
| data-rules.md   | 데이터 생성 규칙 |
| encryption.md   | 암호화 설계    |
| loader-guide.md | DB 적재 가이드 |

---
## 🛠 기술 스택
- Python
- PostgreSQL
- psycopg2 COPY
- AES Encryption
- HMAC SHA256
- Bulk Data Simulation
