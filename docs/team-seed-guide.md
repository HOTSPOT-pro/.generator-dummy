# Team Seed Guide

`team_seed.py`는 대량 더미(`run_all.py`) 이후 팀 계정/가족 데이터를 오버레이하는 스크립트입니다.

## 실행 순서

1. `python scripts/run_all.py`
2. `python scripts/team_seed.py`

## team_fixture.json 형태

```json
{
  "members": [
    {
      "member_key": "owner_1",
      "name": "홍길동",
      "birth": "900101",
      "plan_id": 2,
      "phone": "010-1234-5678",
      "email": "owner@example.com"
    }
  ],
  "families": [
    {
      "family_key": "1",
      "priority_type": "FIFO",
      "family_data_amount": 20971520,
      "members": [
        { "member_key": "owner_1", "family_role": "OWNER", "priority": -1 }
      ]
    }
  ]
}
```

## members 필드

- 필수: `member_key`, `plan_id`, `phone`
- 선택: `name`, `birth`, `email`
- `member_key`는 fixture 내부 식별자이며 중복되면 안 됩니다.
- `phone`은 팀 번호 우선 적용 대상입니다.
- `team_seed`는 USER-BE 온보딩 플로우에 맞춰 `member/social_account`를 생성하지 않습니다.
- `name`, `birth`는 온보딩 요청/화면 테스트용 보조 데이터로만 사용합니다.

## families 필드

- 필수: `members` (`member_key`, `family_role`)
- 선택: `family_key`, `priority_type`, `family_data_amount`, `priority`
- `family_role`은 `OWNER | PARENT | CHILD`
- `priority_type` 기본값: `FIFO`
- `family_data_amount` 단위: `KB`
- `family_data_amount` 미입력 시 기본값: `가족 인원수 * 5GB(KB 기준)`
  - 예: 4명 => `4 * 5 * 1024 * 1024 = 20971520`

## team_seed가 반영하는 테이블

- `subscription`
- `notification_allow`
- `family`
- `family_sub`

`member`, `social_account`, `policy_sub`, `blocked_service_sub`, `present_data`는 `team_seed`에서 생성/수정하지 않습니다.
`subscription.member_id`는 `NULL`로 맞춰 온보딩 전 상태를 유지합니다.

## 전화번호 처리 규칙

- `members[].phone` 값이 우선 적용됩니다.
- 같은 번호가 기존 더미에 이미 있으면 기존 회선을 다른 번호로 이동시켜 팀 번호를 확보합니다.
- `subscription.phone_hash`는 인덱스로 조회 성능을 보조하며, 팀 번호 충돌은 `team_seed.py` 로직에서 조정합니다.
