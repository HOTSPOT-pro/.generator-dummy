import json
import os
import random
import time
import uuid
from typing import Optional, Dict, Any, List

from generator.constants import *
from generator.utils import *
from generator.csv_writer import *

# ======================================================
# Bulk Data Generator
# ======================================================

class BulkDataGenerator:
    def __init__(self):
        self.csv = CSVWriterManager()

        self.member_seq = 1
        self.subscription_seq = 1
        self.social_seq = 1
        self.family_seq = 1
        self.family_sub_seq = 1
        self.family_apply_seq = 1
        self.family_apply_target_seq = 1
        # 1~N은 sql/03_insert_master_data.sql의 관리자 템플릿 정책이 사용
        # 더미에서 생성하는 가족별 정책은 그 다음 ID부터 사용
        self.block_policy_seq = len(block_policies) + 1
        self.policy_sub_seq = 1
        self.blocked_service_sub_seq = 1
        self.present_data_seq = 1
        self.notification_seq = 1
        self.notification_allow_seq = 1

        self.phone_seq = 0
        self.used_phones = set()

        self.subscription_member_map: Dict[int, str] = {}
        self.subscription_plan_map: Dict[int, Dict[str, Any]] = {}
        self.subscription_created_map: Dict[int, datetime] = {}
        self.family_subscriptions: List[Dict[str, Any]] = []
        self.non_family_subscriptions: List[int] = []

        self.block_policy_map = {
            idx + 1: p for idx, p in enumerate(block_policies)
        }

        self.app_code_to_id: Dict[str, int] = {code: idx + 1 for idx, (_, code) in enumerate(APP_BLOCKED_SERVICES)}
        self.app_code_to_name: Dict[str, str] = {code: name for name, code in APP_BLOCKED_SERVICES}

    # ======================================================
    #  1️⃣ USER 생성
    # ======================================================

    def generate_unique_phone(self) -> str:
        while True:
            n = random.randint(0, 99_999_999)
            phone = f"010-{n // 10_000:04d}-{n % 10_000:04d}"
            if phone not in self.used_phones:
                self.used_phones.add(phone)
                return phone

    def write_user(self, last_name: Optional[str], role_for_birth: FamilyRole):

        member_id = self.member_seq
        self.member_seq += 1

        sub_id = self.subscription_seq
        self.subscription_seq += 1

        social_id_seq = self.social_seq
        self.social_seq += 1

        if last_name is None:
            last_name = rand_last_name()

        name = rand_name_with_last(last_name)
        birth = birth_by_role(role_for_birth)

        member_created = rand_datetime_between_years(3)

        # MEMBER
        self.csv.writer('member').writerow([
            member_id, 
            name, 
            birth,
            'APPROVED', 
            False,
            member_created, 
            member_created
        ])

        # SOCIAL_ACCOUNT
        provider = random.choice(PROVIDERS)
        social_id = f"{provider}_{pseudo_uuid_hex(member_id)}"
        email = f"user{member_id}@example.com"

        self.csv.writer('social_account').writerow([
            social_id_seq, 
            member_id,
            email, 
            social_id,
            provider, 
            False,
            member_created, 
            member_created
        ])

        # SUBSCRIPTION
        plan_id = random.choice(list(PLANS.keys()))
        phone_raw = self.generate_unique_phone()
        phone_enc = encrypt_aes(phone_raw)
        phone_hash = generate_blind_index(phone_raw)

        sub_created = rand_datetime_between(member_created, now())
        is_locked = random.random() < 0.05

        self.csv.writer('subscription').writerow([
            sub_id, 
            plan_id, 
            member_id,
            phone_enc, 
            phone_hash,
            is_locked,
            False,
            sub_created, 
            sub_created
        ])

        self.subscription_plan_map[sub_id] = PLANS[plan_id]
        self.subscription_member_map[sub_id] = name
        self.subscription_created_map[sub_id] = sub_created

        # NOTIFICATION_ALLOW
        for category in NotificationCategory:
            self.csv.writer('notification_allow').writerow([
                self.notification_allow_seq, 
                sub_id, 
                category.value,
                True, 
                False, 
                sub_created, 
                sub_created
            ])
            self.notification_allow_seq += 1

        if is_locked:
            self.create_notification(
                sub_id,
                noti_type=NotificationType.IMMEDIATE_BLOCK_APPLIED,
                message="데이터 사용 차단이 즉시 적용되었습니다.",
                created_time=sub_created,
            )
        
        return sub_id

    # ======================================================
    #  2️⃣ FAMILY 생성
    # ======================================================

    def generate_family(self):
        log_step("가족 생성")
        total_family_members = 0

        for i in range(TOTAL_FAMILIES):
            size = random.choices(
                FAMILY_SIZES,
                weights=FAMILY_SIZE_WEIGHTS,
                k=1
            )[0]

            # 전체 유저 수 초과 방지
            if total_family_members + size > TOTAL_USERS:
                size = TOTAL_USERS - total_family_members

            if size <= 0:
                break

            family_last = rand_last_name()
            roles = build_roles(size)

            family_data_amount = size * (5 * GB)

            priority_type = (
                PriorityType.PRIORITY
                if random.random() < PRIORITY_FAMILY_RATE
                else PriorityType.FIFO
            )

            family_created = rand_datetime_between_years(2)

            family_id = self.family_seq

            self.csv.writer('family').writerow([
                family_id,
                size,
                family_data_amount,
                priority_type.value,
                False,
                family_created,
                family_created
            ])

            if priority_type == PriorityType.PRIORITY:
                priorities  = list(range(1, size + 1))
                random.shuffle(priorities )
            else:
                priorities  = [-1] * size

            parent_indexes = [i for i, r in enumerate(roles) if r ==  FamilyRole.PARENT]
            other_parent_index = random.choice(parent_indexes) if parent_indexes else None

            for idx, role in enumerate(roles):
                is_other_parent = (idx == other_parent_index)

                last_name = choose_last_name_for_role(
                    role,
                    family_last,
                    is_other_parent=is_other_parent
                )

                sub_id = self.write_user(last_name, role)

                family_sub_id = self.family_sub_seq

                self.csv.writer('family_sub').writerow([
                    family_sub_id,
                    sub_id,
                    family_id,
                    role.value,
                    priorities[idx],
                    family_data_amount
                ])

                self.family_sub_seq += 1
                self.family_subscriptions.append({
                    "family_id": family_id,
                    "sub_id": sub_id,
                    "role": role
                })

                total_family_members += 1

            self.family_seq += 1

            if (i + 1) % 50000 == 0:
                log_progress("FAMILY_GROUP", i + 1, TOTAL_FAMILIES)

        log_done(f"가족 소속 전체 인원: {total_family_members:,}명")
        return total_family_members

    # ======================================================
    #  3️⃣ NON FAMILY 생성
    # ======================================================

    def generate_remaining_users(self, already_created_members):
        log_step("비가족 사용자 생성")

        remaining = TOTAL_USERS - already_created_members

        for i in range(remaining):
            sub_id = self.write_user(None, FamilyRole.PARENT)
            self.non_family_subscriptions.append(sub_id)

            if (i + 1) % 100000 == 0:
                log_progress("NON_FAMILY", i + 1, remaining)

        log_done(f"비가족 사용자 생성 완료 ({remaining:,}명)")

    # ======================================================
    #  4️⃣ FAMILY_APPLY(CREATE) 생성
    # ======================================================
    
    def generate_family_apply_create(self):
        log_step("FAMILY_APPLY(CREATE) 생성")

        candidates = self.non_family_subscriptions[:]
        if len(candidates) < 2:
            log_warn("비가족 사용자 부족으로 FAMILY_APPLY 생성 스킵")
            return

        random.shuffle(candidates)
        max_apply = min(random.randint(5, 10), len(candidates))
        created_apply = 0
        created_target = 0

        idx = 0
        # 가족 생성 신청은 요청자 외 대상자가 최소 2명이어야 한다.
        while created_apply < max_apply and idx < (len(candidates) - 2):
            requester_sub_id = candidates[idx]
            idx += 1

            apply_created = rand_datetime_between(
                self.subscription_created_map[requester_sub_id],
                now()
            )

            status = "PENDING"

            family_apply_id = self.family_apply_seq
            self.csv.writer("family_apply").writerow([
                family_apply_id,
                requester_sub_id,
                "\\N",      # CREATE 신청은 family_id 없음
                "CREATE",
                "\\N",
                status,
                apply_created,
                apply_created
            ])
            self.family_apply_seq += 1
            created_apply += 1

            # 요청자 제외 2~8명 타겟
            target_count = min(
                random.randint(2, 8),
                len(candidates) - idx
            )
            target_pool = []

            while len(target_pool) < target_count and idx < len(candidates):
                target_pool.append(candidates[idx])
                idx += 1

            for target_sub_id in target_pool:
                target_role = random.choice(["PARENT", "CHILD"])
                self.csv.writer("family_apply_target").writerow([
                    self.family_apply_target_seq,
                    family_apply_id,
                    target_sub_id,
                    target_role
                ])
                self.family_apply_target_seq += 1
                created_target += 1

        log_done(f"FAMILY_APPLY(CREATE) 생성 완료 (신청 {created_apply:,}건 / 대상 {created_target:,}건)")

    def generate_family_apply_add(self):
        log_step("FAMILY_APPLY(ADD) 생성")

        family_group_map: Dict[int, List[Dict[str, Any]]] = {}
        for item in self.family_subscriptions:
            family_group_map.setdefault(item["family_id"], []).append(item)

        eligible_families: List[Dict[str, Any]] = []
        for family_id, members in family_group_map.items():
            owner = next((m for m in members if m["role"] == FamilyRole.OWNER), None)
            if owner is None:
                continue
            if len(members) >= 8:
                continue
            eligible_families.append({
                "family_id": family_id,
                "owner_sub_id": owner["sub_id"],
                "size": len(members)
            })

        candidates = self.non_family_subscriptions[:]
        if not eligible_families or not candidates:
            log_warn("ADD 대상 가족/비가족 사용자 부족으로 FAMILY_APPLY(ADD) 생성 스킵")
            return

        random.shuffle(eligible_families)
        random.shuffle(candidates)

        target_apply = min(random.randint(4, 5), len(eligible_families))
        created_apply = 0
        created_target = 0
        idx = 0

        for family in eligible_families:
            if created_apply >= target_apply or idx >= len(candidates):
                break

            family_id = family["family_id"]
            requester_sub_id = family["owner_sub_id"]
            max_addable = min(8 - family["size"], len(candidates) - idx)
            if max_addable < 1:
                continue

            apply_created = rand_datetime_between(
                self.subscription_created_map[requester_sub_id],
                now()
            )

            family_apply_id = self.family_apply_seq
            self.csv.writer("family_apply").writerow([
                family_apply_id,
                requester_sub_id,
                family_id,
                "ADD",
                "\\N",
                "PENDING",
                apply_created,
                apply_created
            ])
            self.family_apply_seq += 1
            created_apply += 1

            target_count = random.randint(1, max_addable)
            for _ in range(target_count):
                target_sub_id = candidates[idx]
                idx += 1

                target_role = random.choice(["PARENT", "CHILD"])
                self.csv.writer("family_apply_target").writerow([
                    self.family_apply_target_seq,
                    family_apply_id,
                    target_sub_id,
                    target_role
                ])
                self.family_apply_target_seq += 1
                created_target += 1

        log_done(f"FAMILY_APPLY(ADD) 생성 완료 (신청 {created_apply:,}건 / 대상 {created_target:,}건)")

    def generate_family_apply_remove(self):
        log_step("FAMILY_APPLY(REMOVE) 생성")

        family_group_map: Dict[int, List[Dict[str, Any]]] = {}
        for item in self.family_subscriptions:
            family_group_map.setdefault(item["family_id"], []).append(item)

        eligible_families: List[Dict[str, Any]] = []
        for family_id, members in family_group_map.items():
            owner = next((m for m in members if m["role"] == FamilyRole.OWNER), None)
            if owner is None:
                continue
            removable_members = [m for m in members if m["role"] != FamilyRole.OWNER]
            max_removable = min(len(removable_members), len(members) - 2)
            if max_removable < 1:
                continue
            eligible_families.append({
                "family_id": family_id,
                "owner_sub_id": owner["sub_id"],
                "removable_members": removable_members,
                "max_removable": max_removable
            })

        if not eligible_families:
            log_warn("REMOVE 대상 가족 부족으로 FAMILY_APPLY(REMOVE) 생성 스킵")
            return

        random.shuffle(eligible_families)
        target_apply = min(random.randint(4, 5), len(eligible_families))
        created_apply = 0
        created_target = 0

        for family in eligible_families:
            if created_apply >= target_apply:
                break

            family_id = family["family_id"]
            requester_sub_id = family["owner_sub_id"]
            max_removable = family["max_removable"]
            removable_members = family["removable_members"]

            apply_created = rand_datetime_between(
                self.subscription_created_map[requester_sub_id],
                now()
            )

            family_apply_id = self.family_apply_seq
            self.csv.writer("family_apply").writerow([
                family_apply_id,
                requester_sub_id,
                family_id,
                "REMOVE",
                "\\N",
                "PENDING",
                apply_created,
                apply_created
            ])
            self.family_apply_seq += 1
            created_apply += 1

            target_count = random.randint(1, max_removable)
            selected_targets = random.sample(removable_members, k=target_count)

            for member in selected_targets:
                target_sub_id = member["sub_id"]
                target_role = member["role"].value
                self.csv.writer("family_apply_target").writerow([
                    self.family_apply_target_seq,
                    family_apply_id,
                    target_sub_id,
                    target_role
                ])
                self.family_apply_target_seq += 1
                created_target += 1

        log_done(f"FAMILY_APPLY(REMOVE) 생성 완료 (신청 {created_apply:,}건 / 대상 {created_target:,}건)")
    
    # ======================================================
    #  5️⃣ POLICY_SUB 생성
    # ======================================================

    def _random_time_window(self):
        duration_minutes = random.randint(1, 8) * 60
        start_minutes = random.randint(0, (24 * 60) - duration_minutes)
        end_minutes = start_minutes + duration_minutes
        start_time = f"{start_minutes // 60:02d}:{start_minutes % 60:02d}"
        end_time = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
        return start_time, end_time

    def _build_new_policy(self):
        all_days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        day_count = random.randint(3, 7)
        start_time, end_time = self._random_time_window()
        snapshot = {
            "days": random.sample(all_days, k=day_count),
            "startTime": start_time,
            "endTime": end_time
        }
        return {
            "name": random.choice(["학습 집중 시간", "야간 사용 제한", "주중 규칙 모드"]),
            "description": "가족 대표가 직접 생성한 가족 전용 시간 정책입니다.",
            "type": PolicyType.SCHEDULED,
            "snapshot": snapshot
        }

    def _build_customized_policy(self, base):
        snapshot = json.loads(json.dumps(base["snapshot"]))
        policy_type = base["type"]

        if policy_type == PolicyType.SCHEDULED:
            all_days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
            day_count = random.randint(3, 7)
            start_time, end_time = self._random_time_window()
            snapshot["days"] = random.sample(all_days, k=day_count)
            snapshot["startTime"] = start_time
            snapshot["endTime"] = end_time
        else:
            start_time, end_time = self._random_time_window()
            snapshot["days"] = snapshot.get("days", ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"])
            snapshot["startTime"] = start_time
            snapshot["endTime"] = end_time

        return {
            "name": f"{base['name']} (커스텀)",
            "description": "관리자 템플릿을 기반으로 가족 대표가 커스텀한 정책입니다.",
            "type": policy_type,
            "snapshot": snapshot
        }

    def _policy_signature(self, family_policy):
        # 같은 가족 내에서 정책 본문 중복 생성을 방지하기 위한 식별자
        return (
            family_policy["type"].value,
            family_policy["name"],
            json.dumps(family_policy["snapshot"], ensure_ascii=False, sort_keys=True)
        )

    def _time_to_minutes(self, hhmm):
        hour, minute = hhmm.split(":")
        return int(hour) * 60 + int(minute)

    def _extract_scheduled_intervals(self, snapshot):
        days = snapshot.get("days", [])
        start_time = snapshot.get("startTime")
        end_time = snapshot.get("endTime")
        if not days or not start_time or not end_time:
            return []

        start_min = self._time_to_minutes(start_time)
        end_min = self._time_to_minutes(end_time)
        if end_min <= start_min:
            return []

        return [(day, start_min, end_min) for day in days]

    def _has_schedule_conflict(self, active_windows_by_day, intervals):
        for day, start_min, end_min in intervals:
            for existing_start, existing_end in active_windows_by_day.get(day, []):
                if max(start_min, existing_start) < min(end_min, existing_end):
                    return True
        return False

    def _append_active_windows(self, active_windows_by_day, intervals):
        for day, start_min, end_min in intervals:
            active_windows_by_day.setdefault(day, []).append((start_min, end_min))
    
    def generate_policy_sub(self):
        log_step("POLICY_SUB 생성")

        template_ids = [
            pid for pid, p in self.block_policy_map.items()
            if p.get("is_active", True) and p["type"] == PolicyType.SCHEDULED
        ]
        if not template_ids:
            log_warn("활성화된 SCHEDULED 관리자 정책 템플릿이 없어 POLICY_SUB 생성 스킵")
            return

        family_group_map: Dict[int, List[Dict[str, Any]]] = {}
        for item in self.family_subscriptions:
            family_group_map.setdefault(item["family_id"], []).append(item)

        created_policy = 0
        created_mapping = 0

        for family_id, members in family_group_map.items():
            owner = next((m for m in members if m["role"] == FamilyRole.OWNER), None)
            if owner is None:
                continue

            owner_sub_id = owner["sub_id"]
            member_active_windows = {m["sub_id"]: {} for m in members}
            policy_count = random.randint(0, 3)
            family_policy_signatures = set()
            generated_count = 0
            max_attempts = max(1, policy_count * 5)

            attempts = 0
            while generated_count < policy_count and attempts < max_attempts:
                attempts += 1
                policy_created = rand_datetime_between(
                    self.subscription_created_map[owner_sub_id],
                    now()
                )

                policy_mode = random.choices(
                    ["COPY", "CUSTOMIZE", "NEW"],
                    weights=[45, 35, 20],
                    k=1
                )[0]

                if policy_mode == "NEW":
                    family_policy = self._build_new_policy()
                else:
                    template_policy_id = random.choice(template_ids)
                    base = self.block_policy_map[template_policy_id]
                    if policy_mode == "COPY":
                        family_policy = {
                            "name": f"{base['name']} (템플릿)",
                            "description": base.get("description", ""),
                            "type": base["type"],
                            "snapshot": json.loads(json.dumps(base["snapshot"]))
                        }
                    else:
                        family_policy = self._build_customized_policy(base)

                signature = self._policy_signature(family_policy)
                if signature in family_policy_signatures:
                    continue
                family_policy_signatures.add(signature)

                family_policy_id = self.block_policy_seq
                self.csv.writer("block_policy").writerow([
                    family_policy_id,
                    family_policy["name"],
                    family_policy["description"],
                    family_id,
                    family_policy["type"].value,
                    json.dumps(family_policy["snapshot"], ensure_ascii=False),
                    True,
                    False,
                    policy_created,
                    policy_created
                ])
                self.block_policy_seq += 1
                created_policy += 1
                generated_count += 1
                policy_intervals = self._extract_scheduled_intervals(family_policy["snapshot"])

                for member in members:
                    sub_id = member["sub_id"]
                    role = member["role"]

                    if role == FamilyRole.CHILD:
                        is_policy_active = random.random() < 0.8
                    elif role == FamilyRole.PARENT:
                        is_policy_active = random.random() < 0.55
                    else:
                        is_policy_active = random.random() < 0.35

                    if is_policy_active and policy_intervals:
                        if self._has_schedule_conflict(member_active_windows[sub_id], policy_intervals):
                            is_policy_active = False
                        else:
                            self._append_active_windows(member_active_windows[sub_id], policy_intervals)

                    self.csv.writer("policy_sub").writerow([
                        self.policy_sub_seq,
                        sub_id,
                        family_policy_id,
                        is_policy_active,
                        policy_created,
                        policy_created
                    ])

                    if is_policy_active:
                        self.create_notification(
                            sub_id=sub_id,
                            noti_type=NotificationType.TIME_WINDOW_POLICY_APPLIED,
                            message=f"“{family_policy['name']}” 시간 차단 정책이 적용되었습니다",
                            created_time=policy_created
                        )

                    self.policy_sub_seq += 1
                    created_mapping += 1

        log_done(
            f"POLICY_SUB 생성 완료 (가족 정책 {created_policy:,}건 / 구성원 매핑 {created_mapping:,}건)"
        )
    

    # ======================================================
    #  6️⃣ BLOCKED_SERVICE_SUB 생성
    # ======================================================

    def generate_blocked_service_sub(self):

        log_step("BLOCKED_SERVICE_SUB 생성")

        created = 0

        for item in self.family_subscriptions:
            sub_id = item["sub_id"]
            role = item["role"]

            if role == FamilyRole.CHILD:
                if random.random() >= 0.7:
                    continue
                block_count = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
            else:
                if random.random() >= 0.2:
                    continue
                block_count = random.choices([1, 2], weights=[80, 20])[0]

            selected_codes = random.sample(PREFERRED_CODES, k=min(block_count, len(PREFERRED_CODES)))

            sub_created = self.subscription_created_map[sub_id]

            for code in selected_codes:
                blocked_service_id = self.app_code_to_id.get(code)
                if not blocked_service_id:
                    continue

                blocked_created = rand_datetime_between(sub_created, now())

                self.csv.writer("blocked_service_sub").writerow([
                    self.blocked_service_sub_seq,
                    sub_id,
                    blocked_service_id,
                    True,
                    False,
                    blocked_created,
                    blocked_created
                ])

                service_name = self.app_code_to_name.get(code, code)

                self.create_notification(
                    sub_id=sub_id,
                    noti_type=NotificationType.SERVICE_ACCESS_BLOCKED,
                    message=f"“{service_name}” 서비스 이용이 차단되었습니다.",
                    created_time=blocked_created
                )

                self.blocked_service_sub_seq += 1
                created += 1

        log_done(f"BLOCKED_SERVICE_SUB 생성 완료 ({created:,}건)")

    # ======================================================
    # 7️⃣ PRESENT_DATA 생성
    # ======================================================

    def generate_present_data(self):

        log_step("PRESENT_DATA 생성")

        family_group_map: Dict[int, List[Dict[str, Any]]] = {}
        for item in self.family_subscriptions:
            family_group_map.setdefault(item["family_id"], []).append(item)

        start = datetime(2026, 2, 1, 0, 0, 0)
        end = datetime(2026, 2, 20, 23, 59, 59)

        created = 0

        for family_id, members in family_group_map.items():
            # 50% 가족만 선물 이벤트 발생
            if random.random() > 0.5:
                continue

            parents = [
                m for m in members 
                if m["role"] in (FamilyRole.OWNER, FamilyRole.PARENT)
            ]

            children = [
                m for m in members 
                if m["role"] == FamilyRole.CHILD
            ]

            if not parents or not children:
                continue

            sender = random.choice(parents)
            receiver = random.choice(children)

            sender_sub_id = sender["sub_id"]
            receiver_sub_id = receiver["sub_id"]

            plan = self.subscription_plan_map.get(sender_sub_id)
            if not plan:
                continue

            if plan["amount"] == -1:
                max_gift_gb = 5
            elif plan["amount"] == int(1.5 * GB):
                max_gift_gb = 0
            elif plan["period"] == "DAY":
                max_gift_gb = 0
            else:
                total_gb = plan["amount"] // GB
                max_gift_gb = min(total_gb, 5) if total_gb >= 1 else 0

            if max_gift_gb <= 0:
                continue

            gift_gb = random.randint(1, max_gift_gb)
            gift_amount = gift_gb * GB

            present_created = rand_datetime_between(start, end)

            self.csv.writer("present_data").writerow([
                self.present_data_seq,
                receiver_sub_id,
                sender_sub_id,
                gift_amount,
                present_created
            ])

            sender_name = self.subscription_member_map.get(sender_sub_id, "가족")
            self.create_notification(
                sub_id=receiver_sub_id,
                noti_type=NotificationType.PRESENT_DATA,
                message=f"“{sender_name}”님이 데이터 {gift_gb}GB를 선물하셨습니다.",
                created_time=present_created
            )

            self.present_data_seq += 1
            created += 1

        log_done(f"PRESENT_DATA 생성 완료 ({created:,}건)")

   # ======================================================
    # 8️⃣ NOTIFIACTION 생성
    # ======================================================

    def create_notification(
        self,
        sub_id: int,
        noti_type: NotificationType,
        message: str,
        created_time: datetime
    ):
        # 랜덤 event_id 생성
        event_id = f"evt_{uuid.uuid4().hex}"

        # 알림 제목을 생성 (noti_type이나 기획에 맞게 수정하셔도 됩니다)
        title = "알림이 도착했습니다." 

        self.csv.writer("notification").writerow([
            self.notification_seq,   # 1. notification_id
            sub_id,                  # 2. sub_id
            noti_type.value,         # 3. notification_type
            title,                   # 4. notification_title (💡 새로 추가됨!)
            message,                 # 5. notification_content
            created_time,            # 6. created_time
            False,                   # 7. is_read
            event_id                 # 8. event_id
        ])

        self.notification_seq += 1

    # ======================================================
    # 9️⃣ MAIN 실행
    # ======================================================

    def print_summary(self):
        log_step("📊 생성된 파일 요약")

        for name in self.csv.files.keys():
            path = os.path.join(OUTPUT_DIR, f"{name}.csv")

            if not os.path.exists(path):
                log_warn(f"{name}.csv → 파일 없음")
                continue

            with open(path, encoding="utf-8") as f:
                row_count = sum(1 for _ in f)

            log_info(f"{name}.csv → {row_count:,} rows")

    def generate(self):

        start_time = time.time()

        log_step("▶️  더미 데이터 생성 시작")

        total_family_members = self.generate_family()
        self.generate_remaining_users(total_family_members)
        self.generate_family_apply_create()
        self.generate_family_apply_add()
        self.generate_family_apply_remove()

        self.generate_policy_sub()
        self.generate_blocked_service_sub()
        self.generate_present_data()

        self.csv.close()
        self.print_summary()

        log_done(f"✅ 전체 더미 데이터 생성 완료 (실행 시간: {elapsed_hms(start_time)})")


if __name__ == "__main__":
    BulkDataGenerator().generate()
