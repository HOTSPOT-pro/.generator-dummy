# Encryption Design

## Envelope Encryption

- 회선(`subscription`)별로 DEK를 사용해 `phone_enc`를 암호화합니다.
- DEK는 `subscription_key.encrypted_dek`에 저장하며, KEK로 래핑된 값만 보관합니다.
- `ENCRYPTION_PROVIDER=kms`일 때 AWS KMS `GenerateDataKey/Decrypt`를 실호출합니다.
- 로컬 테스트가 필요하면 `ENCRYPTION_PROVIDER=local`로 폴백할 수 있습니다.

## Subscription Key Model

- `subscription.phone_key_version`: 현재 전화번호 암호문에 사용한 DEK 버전
- `subscription_key.key_version`: 회선별 DEK 버전 이력
- `subscription_key.status`: `active | retired | disabled`
- `subscription_key.kek_key_id`: KEK 식별자(예: KMS key id/arn)

## Blind Index

전화번호 검색용 해시:

`HMAC-SHA256(phone, HASH_KEY)`

## 목적

✔ 개인정보 보호  
✔ 검색 가능 구조  
✔ 키 로테이션 가능한 운영 구조
