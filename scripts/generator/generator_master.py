import json
import os
import copy
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
        self.block_policy_seq = 1
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
            self.write_user(None, FamilyRole.PARENT)

            if (i + 1) % 100000 == 0:
                log_progress("NON_FAMILY", i + 1, remaining)

        log_done(f"비가족 사용자 생성 완료 ({remaining:,}명)")
    
    # ======================================================
    #  4️⃣ POLICY_SUB 생성
    # ======================================================
    
    def generate_policy_sub(self):
        log_step("POLICY_SUB 생성")

        scheduled_ids = [
            pid for pid, p in self.block_policy_map.items()
            if p["type"] == PolicyType.SCHEDULED
        ]
        if not scheduled_ids:
            log_warn("SCHEDULED 정책이 없어 POLICY_SUB 생성 스킵")
            return

        created = 0

        for item in self.family_subscriptions:
            sub_id = item["sub_id"]
            role = item["role"]

            if role == FamilyRole.CHILD:
                policy_type = random.choices([None, PolicyType.SCHEDULED], weights=[70, 30])[0]
            else:
                policy_type = random.choices([None, PolicyType.SCHEDULED], weights=[85, 15])[0]

            if policy_type is None:
                continue

            block_policy_id = random.choice(scheduled_ids)
            base = self.block_policy_map[block_policy_id]

            sub_created = self.subscription_created_map[sub_id]
            policy_created = rand_datetime_between(sub_created, now())

            snapshot = {
                "policyName": base["name"],
                "policyType": base["type"].value,
                "data": copy.deepcopy(base["snapshot"])
            }

            self.csv.writer("policy_sub").writerow([
                self.policy_sub_seq,
                sub_id,
                block_policy_id,
                json.dumps(snapshot, ensure_ascii=False),
                False,
                policy_created,
                policy_created
            ])

            self.create_notification(
                sub_id=sub_id,
                noti_type=NotificationType.TIME_WINDOW_POLICY_APPLIED,
                message=f"“{base['name']}” 시간 차단 정책이 적용되었습니다",
                created_time=policy_created
            )

            self.policy_sub_seq += 1
            created += 1

        log_done(f"POLICY_SUB 생성 완료 ({created:,}건)")
    

    # ======================================================
    #  5️⃣ BLOCKED_SERVICE_SUB 생성
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
    # 6️⃣ PRESENT_DATA 생성
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
    # 7️⃣ NOTIFIACTION 생성
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

        self.csv.writer("notification").writerow([
            self.notification_seq,   # notification_id
            sub_id,
            noti_type.value,
            message,
            created_time,
            False,                   # is_read
            event_id                 # 추가
        ])

        self.notification_seq += 1

    # ======================================================
    # 8️⃣ MAIN 실행
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

        self.generate_policy_sub()
        self.generate_blocked_service_sub()
        self.generate_present_data()

        self.csv.close()
        self.print_summary()

        log_done(f"✅ 전체 더미 데이터 생성 완료 (실행 시간: {elapsed_hms(start_time)})")


if __name__ == "__main__":
    BulkDataGenerator().generate()
