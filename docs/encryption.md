# Encryption Design

## AES Encryption

- AES-256-CBC
- IV: 랜덤 16 bytes
- 저장 형식: Base64(IV + CipherText)

## Blind Index

전화번호 검색을 위한 해시:

HMAC-SHA256(phone, HASH_KEY)

## 목적

✔ 개인정보 보호  
✔ 검색 가능 구조  
✔ 운영환경 보안 설계
