"""
팀원 테스트 데이터 시드 스크립트

실행 순서:
1) python scripts/run_all.py
2) python scripts/team_seed.py
"""
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import psycopg2

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.db_config import DB_CONFIG
from generator.constants import NotificationCategory
from generator.utils import encrypt_aes, generate_blind_index

# 데이터 단위는 KB 기준
KB_PER_GB = 1024 * 1024
FIXTURE_PATH = os.path.join(PROJECT_ROOT, "scripts", "team_fixture.json")


def get_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )


def load_fixture(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def now():
    return datetime.now().replace(microsecond=0)


def generate_team_phone(
    cur,
    offset: int,
    exclude_sub_id: Optional[int] = None,
    avoid_phone_hash: Optional[str] = None,
) -> str:
    # 테스트용 임시 대역(9xxx) 대신 일반 번호 대역(1xxx~)을 순차 사용한다.
    seq = 10_000_000 + max(0, int(offset))
    while True:
        middle = (seq // 10000) % 10000
        tail = seq % 10000
        phone = f"010-{middle:04d}-{tail:04d}"
        phone_hash = generate_blind_index(phone)
        if avoid_phone_hash and phone_hash == avoid_phone_hash:
            seq += 1
            continue

        cur.execute(
            """
            SELECT 1
            FROM subscription
            WHERE phone_hash = %s
              AND (%s IS NULL OR sub_id <> %s)
            LIMIT 1
            """,
            (phone_hash, exclude_sub_id, exclude_sub_id),
        )
        exists = cur.fetchone() is not None
        if not exists:
            return phone
        seq += 1


def ensure_team_phone_priority(
    cur,
    desired_phone: str,
    team_member_key: str,
    phone_offset: int,
    current_sub_id: Optional[int],
):
    desired_hash = generate_blind_index(desired_phone)
    cur.execute(
        """
        SELECT sub_id
        FROM subscription
        WHERE phone_hash = %s
          AND (%s IS NULL OR sub_id <> %s)
        ORDER BY sub_id ASC
        LIMIT 1
        """,
        (desired_hash, current_sub_id, current_sub_id),
    )
    conflict = cur.fetchone()
    if not conflict:
        return

    conflict_sub_id = conflict[0]
    fallback_phone = generate_team_phone(
        cur,
        phone_offset + 1,
        exclude_sub_id=conflict_sub_id,
        avoid_phone_hash=desired_hash,
    )
    fallback_enc = encrypt_aes(fallback_phone)
    fallback_hash = generate_blind_index(fallback_phone)
    ts = now()
    cur.execute(
        """
        UPDATE subscription
        SET phone_enc = %s, phone_hash = %s, modified_time = %s
        WHERE sub_id = %s
        """,
        (fallback_enc, fallback_hash, ts, conflict_sub_id),
    )
    print(
        f"  [MOVE] subscription phone reassigned: sub_id={conflict_sub_id} "
        f"(team {team_member_key} phone reserved)"
    )


def find_member_by_phone(cur, phone: str) -> Optional[int]:
    phone_hash = generate_blind_index(phone)
    cur.execute(
        """
        SELECT member_id
        FROM subscription
        WHERE phone_hash = %s
        ORDER BY sub_id ASC
        LIMIT 1
        """,
        (phone_hash,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def upsert_member(cur, payload: Dict[str, Any]) -> int:
    phone = payload.get("phone")
    member_id = find_member_by_phone(cur, phone) if phone else None

    ts = now()
    if member_id is None:
        cur.execute(
            """
            INSERT INTO member (name, birth, status, is_deleted, created_time, modified_time)
            VALUES (%s, %s, 'APPROVED', FALSE, %s, %s)
            RETURNING member_id
            """,
            (payload["name"], payload["birth"], ts, ts),
        )
        member_id = cur.fetchone()[0]
        print(f"  [INSERT] member: {payload['member_key']} -> {member_id}")
    else:
        cur.execute(
            """
            UPDATE member
            SET name = %s, birth = %s, modified_time = %s
            WHERE member_id = %s
            """,
            (payload["name"], payload["birth"], ts, member_id),
        )
        print(f"  [UPDATE] member: {payload['member_key']} -> {member_id}")

    return member_id


def upsert_subscription(cur, member_id: int, payload: Dict[str, Any], phone_offset: int) -> int:
    cur.execute(
        """
        SELECT sub_id
        FROM subscription
        WHERE member_id = %s
        ORDER BY sub_id ASC
        LIMIT 1
        """,
        (member_id,),
    )
    row = cur.fetchone()
    plan_id = int(payload.get("plan_id", 3))
    ts = now()

    sub_id = row[0] if row else None
    phone_raw = payload.get("phone")
    if phone_raw:
        ensure_team_phone_priority(cur, phone_raw, payload["member_key"], phone_offset, sub_id)
    else:
        phone_raw = generate_team_phone(cur, phone_offset, exclude_sub_id=sub_id)
    phone_enc = encrypt_aes(phone_raw)
    phone_hash = generate_blind_index(phone_raw)

    if sub_id:
        cur.execute(
            """
            UPDATE subscription
            SET plan_id = %s, phone_enc = %s, phone_hash = %s, modified_time = %s, is_deleted = FALSE
            WHERE sub_id = %s
            """,
            (plan_id, phone_enc, phone_hash, ts, sub_id),
        )
        print(f"  [UPDATE] subscription: {payload['member_key']} -> {sub_id}")
        return sub_id

    cur.execute(
        """
        INSERT INTO subscription (
            plan_id, member_id, phone_enc, phone_hash, is_locked, is_deleted, created_time, modified_time
        )
        VALUES (%s, %s, %s, %s, FALSE, FALSE, %s, %s)
        RETURNING sub_id
        """,
        (plan_id, member_id, phone_enc, phone_hash, ts, ts),
    )
    sub_id = cur.fetchone()[0]
    print(f"  [INSERT] subscription: {payload['member_key']} -> {sub_id}")
    return sub_id


def ensure_notification_allow(cur, sub_id: int):
    ts = now()
    for category in NotificationCategory:
        cur.execute(
            """
            SELECT notification_allow_id
            FROM notification_allow
            WHERE sub_id = %s AND notification_category = %s
            LIMIT 1
            """,
            (sub_id, category.value),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                """
                UPDATE notification_allow
                SET notification_allow = TRUE, is_deleted = FALSE, modified_time = %s
                WHERE notification_allow_id = %s
                """,
                (ts, row[0]),
            )
        else:
            cur.execute(
                """
                INSERT INTO notification_allow (
                    sub_id, notification_category, notification_allow, is_deleted, created_time, modified_time
                )
                VALUES (%s, %s, TRUE, FALSE, %s, %s)
                """,
                (sub_id, category.value, ts, ts),
            )


def upsert_family(cur, family_payload: Dict[str, Any], sub_map: Dict[str, int]) -> int:
    members = family_payload["members"]
    if not members:
        raise ValueError(f"family members 비어있음: {family_payload.get('family_key')}")

    first_member_key = members[0]["member_key"]
    first_sub_id = sub_map[first_member_key]
    ts = now()

    cur.execute(
        """
        SELECT family_id
        FROM family_sub
        WHERE sub_id = %s
        ORDER BY family_sub_id ASC
        LIMIT 1
        """,
        (first_sub_id,),
    )
    existing = cur.fetchone()

    family_num = len(members)
    family_data_amount = int(family_payload.get("family_data_amount", family_num * 5 * KB_PER_GB))
    priority_type = family_payload.get("priority_type", "FIFO")

    if existing:
        family_id = existing[0]
        cur.execute(
            """
            UPDATE family
            SET family_num = %s, family_data_amount = %s, priority_type = %s, modified_time = %s, is_deleted = FALSE
            WHERE family_id = %s
            """,
            (family_num, family_data_amount, priority_type, ts, family_id),
        )
        print(f"  [UPDATE] family: {family_payload.get('family_key')} -> {family_id}")
    else:
        cur.execute(
            """
            INSERT INTO family (family_num, family_data_amount, priority_type, is_deleted, created_time, modified_time)
            VALUES (%s, %s, %s, FALSE, %s, %s)
            RETURNING family_id
            """,
            (family_num, family_data_amount, priority_type, ts, ts),
        )
        family_id = cur.fetchone()[0]
        print(f"  [INSERT] family: {family_payload.get('family_key')} -> {family_id}")

    for member in members:
        member_key = member["member_key"]
        sub_id = sub_map[member_key]
        role = member["family_role"]
        priority = member.get("priority")

        cur.execute(
            """
            SELECT family_sub_id
            FROM family_sub
            WHERE sub_id = %s
            ORDER BY family_sub_id ASC
            LIMIT 1
            """,
            (sub_id,),
        )
        fs = cur.fetchone()

        if fs:
            cur.execute(
                """
                UPDATE family_sub
                SET family_id = %s, family_role = %s, priority = %s, data_limit = %s
                WHERE family_sub_id = %s
                """,
                (family_id, role, priority, family_data_amount, fs[0]),
            )
        else:
            cur.execute(
                """
                INSERT INTO family_sub (sub_id, family_id, family_role, priority, data_limit)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (sub_id, family_id, role, priority, family_data_amount),
            )

    return family_id


def validate_fixture(fixture: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    members = fixture.get("members", [])
    families = fixture.get("families", [])

    if not members:
        raise ValueError("members가 비어있습니다.")

    key_set = set()
    for m in members:
        key = m.get("member_key")
        if not key:
            raise ValueError("member_key 누락")
        if key in key_set:
            raise ValueError(f"중복 member_key: {key}")
        key_set.add(key)

    for fam in families:
        for fm in fam.get("members", []):
            mk = fm.get("member_key")
            if mk not in key_set:
                raise ValueError(f"families에서 알 수 없는 member_key 사용: {mk}")

    return members, families


def main():
    print("=" * 60)
    print("TEAM FIXTURE SEED")
    print("=" * 60)
    print(f"fixture: {FIXTURE_PATH}")

    fixture = load_fixture(FIXTURE_PATH)
    members, families = validate_fixture(fixture)

    conn = get_connection()
    try:
        conn.autocommit = False

        member_map: Dict[str, int] = {}
        sub_map: Dict[str, int] = {}

        with conn.cursor() as cur:
            for idx, member in enumerate(members):
                member_id = upsert_member(cur, member)
                sub_id = upsert_subscription(cur, member_id, member, idx)
                ensure_notification_allow(cur, sub_id)

                member_map[member["member_key"]] = member_id
                sub_map[member["member_key"]] = sub_id

            for fam in families:
                upsert_family(cur, fam, sub_map)

        conn.commit()
        print("\n✅ 팀원/가족 테스트 데이터 반영 완료")
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] team seed 실패: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
