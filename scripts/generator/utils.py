import base64
import random
import time
import hmac
import hashlib
from datetime import datetime, date, timedelta
from typing import List
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

from config.db_config import HASH_KEY, SECRET_KEY
from generator.constants import *

# ======================================================
# Time
# ======================================================

def now() -> datetime:
    return datetime.now().replace(microsecond=0)

def elapsed_hms(start_time: float) -> str:
    total_seconds = int(time.time() - start_time)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# ======================================================
# Crypto
# ======================================================

def encrypt_aes(plain_text: str) -> str:
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))
    return base64.b64encode(iv + encrypted).decode('utf-8')

# ======================================================
# Crypto
# ======================================================

def generate_blind_index(plain_text: str) -> str:
    signature = hmac.new(
        HASH_KEY,
        plain_text.encode('utf-8'),
        hashlib.sha256
    ).digest()

    return base64.b64encode(signature).decode('utf-8')

# ======================================================
# Random data generators
# ======================================================

def generate_seq_phone(seq: int) -> str:
    mid = seq // 10000
    last = seq % 10000
    return f"010-{mid:04d}-{last:04d}"

def rand_last_name() -> str:
    return random.choices(LAST_NAMES, weights=LAST_NAME_WEIGHTS, k=1)[0]

def rand_name_with_last(last: str) -> str:
    first = random.choice(FIRST_SYLLABLES)
    second = random.choice(SECOND_SYLLABLES)

    while second == first:
        second = random.choice(SECOND_SYLLABLES)

    return last + first + second

def rand_datetime_between_years(years_back: int) -> datetime:
    cur = now()
    start = cur - timedelta(days=years_back * 365)
    delta = cur - start
    return (start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))).replace(microsecond=0)

def rand_datetime_between(start_dt, end_dt):
    delta = end_dt - start_dt
    seconds = random.randint(0, int(delta.total_seconds()))
    return (start_dt + timedelta(seconds=seconds)).replace(microsecond=0)

def birth_by_age_range(min_age: int, max_age: int) -> str:
    """YYMMDD"""
    today = date.today()
    start = today - timedelta(days=max_age * 365)
    end = today - timedelta(days=min_age * 365)
    days = (end - start).days
    d = start + timedelta(days=random.randint(0, days))
    return d.strftime("%y%m%d")

def birth_by_role(role: FamilyRole) -> str:
    if role in (FamilyRole.OWNER, FamilyRole.PARENT):
        return birth_by_age_range(30, 55)
    return birth_by_age_range(5, 25)

def pseudo_uuid_hex(member_id: int) -> str:
    r = random.getrandbits(64)
    return f"{member_id:08x}{r:016x}"

# ======================================================
# Family role builders
# ======================================================

def decide_parent_count(family_size: int) -> int:
    if family_size == 2:
        return 1 if random.random() < 0.75 else 2
    return 1 if random.random() < 0.35 else 2 

def build_roles(family_size: int) -> List[FamilyRole]:
    parent_cnt = min(decide_parent_count(family_size), family_size)

    roles = [FamilyRole.PARENT] * parent_cnt + \
            [FamilyRole.CHILD] * (family_size - parent_cnt)

    random.shuffle(roles)

    parent_idxs = [i for i, r in enumerate(roles) if r == FamilyRole.PARENT]
    owner_idx = random.choice(parent_idxs)
    roles[owner_idx] = FamilyRole.OWNER

    return roles

def choose_last_name_for_role(role: FamilyRole, family_last: str, is_other_parent: bool) -> str:
    """
    - OWNER/CHILD: 무조건 family_last
    - PARENT(다른 부모로 선택된 1명): 확률적으로 성씨 다르게
    """
    if role in (FamilyRole.CHILD, FamilyRole.OWNER):
        return family_last

    if is_other_parent:
        if random.random() < MOTHER_SAME_LASTNAME_RATE:
            return family_last
        return random.choice(LAST_NAMES)

    return family_last

# ======================================================
# Logging
# ======================================================

def log_step(title: str):
    print("\n" + "=" * 60)
    print(f"[STEP] {title}")
    print("=" * 60)

def log_info(message: str):
    print(f"[INFO] {message}")

def log_done(message: str):
    print(f"[DONE] {message}")

def log_warn(message: str):
    print(f"[WARN] {message}")

def log_progress(label: str, current: int, total: int):
    percent = (current / total) * 100
    print(f"[{label}] {current:,}/{total:,} ({percent:.2f}%)")

