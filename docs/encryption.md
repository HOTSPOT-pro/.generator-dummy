# Encryption Design

## Envelope Encryption

- `sub_id % 1000` 버킷 단위 DEK를 사용해 `phone_enc`를 암호화합니다.
- DEK는 `subscription_key.encrypted_dek`에 저장하며, KEK로 래핑된 값만 보관합니다.
- `ENCRYPTION_PROVIDER=kms`일 때 AWS KMS `GenerateDataKey/Decrypt`를 실호출합니다.
- 로컬 테스트가 필요하면 `ENCRYPTION_PROVIDER=local`로 폴백할 수 있습니다.

## Subscription Key Model

- `subscription.phone_key_bucket_id`: 전화번호 암호문에 사용한 키 버킷 ID (`sub_id % 1000`)
- `subscription.phone_key_version`: 현재 전화번호 암호문에 사용한 DEK 버전
- `subscription_key.bucket_id`: 버킷별 DEK 키 공간
- `subscription_key.key_version`: 버킷별 DEK 버전 이력
- `subscription_key.status`: `active | retired | disabled`
- `subscription_key.kek_key_id`: KEK 식별자(예: KMS key id/arn)

## Blind Index

전화번호 검색용 해시:

`HMAC-SHA256(phone, HASH_KEY)`

## Local vs KMS

| 항목 | `ENCRYPTION_PROVIDER=local` | `ENCRYPTION_PROVIDER=kms` |
|---|---|---|
| DEK 생성 | 앱에서 랜덤 생성 | KMS `GenerateDataKey` 호출 |
| DEK 래핑(`encrypted_dek`) | 로컬 `SECRET_KEY`로 래핑(시뮬레이션) | KMS KEK로 래핑 |
| DEK 복원 | 로컬 `SECRET_KEY`로 언래핑 | KMS `Decrypt` 호출 |
| 필요 환경변수 | `SECRET_KEY`, `HASH_KEY` | `AWS_REGION`, `KEK_KEY_ID`, AWS 자격증명, `HASH_KEY` |
| 외부 의존성 | 없음 | AWS KMS 네트워크/권한 필요 |
| 보안 수준 | 개발/테스트 용도 | 운영 권장 |
| 비용 | 추가 비용 없음 | KMS API 호출 비용 발생 |

운영 환경 권장: `kms`  
개발/로컬 검증 권장: `local`

## 목적

✔ 개인정보 보호  
✔ 검색 가능 구조  
✔ 키 로테이션 가능한 운영 구조
