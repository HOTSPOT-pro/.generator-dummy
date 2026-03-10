import base64
import random
import time
import hmac
import hashlib
from typing import Optional, Tuple
from datetime import datetime, date, timedelta
from typing import List
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

from config.db_config import (
    AWS_REGION,
    ENCRYPTION_PROVIDER,
    KEK_KEY_ID,
    get_hash_key,
    load_key,
    validate_encryption_config,
)
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

_kms_client = None
GCM_PREFIX = "gcm:"
GCM_NONCE_SIZE = 12
GCM_TAG_SIZE = 16

def _get_kms_client():
    global _kms_client
    if _kms_client is not None:
        return _kms_client
    import boto3
    _kms_client = boto3.client("kms", region_name=AWS_REGION)
    return _kms_client

def _encrypt_with_key_cbc(raw_bytes: bytes, key: bytes) -> str:
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(raw_bytes, AES.block_size))
    return base64.b64encode(iv + encrypted).decode('utf-8')

def _decrypt_with_key_cbc(cipher_text: str, key: bytes) -> bytes:
    decoded = base64.b64decode(cipher_text)
    iv = decoded[:AES.block_size]
    encrypted = decoded[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(encrypted), AES.block_size)

def _encrypt_with_key(raw_bytes: bytes, key: bytes) -> str:
    nonce = get_random_bytes(GCM_NONCE_SIZE)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce, mac_len=GCM_TAG_SIZE)
    encrypted, tag = cipher.encrypt_and_digest(raw_bytes)
    payload = nonce + encrypted + tag
    return GCM_PREFIX + base64.b64encode(payload).decode('utf-8')

def _decrypt_with_key(cipher_text: str, key: bytes) -> bytes:
    # Preferred format: gcm:<base64(nonce + ciphertext + tag)>
    if cipher_text.startswith(GCM_PREFIX):
        encoded = cipher_text[len(GCM_PREFIX):]
        decoded = base64.b64decode(encoded)
        nonce = decoded[:GCM_NONCE_SIZE]
        tag = decoded[-GCM_TAG_SIZE:]
        encrypted = decoded[GCM_NONCE_SIZE:-GCM_TAG_SIZE]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce, mac_len=GCM_TAG_SIZE)
        return cipher.decrypt_and_verify(encrypted, tag)

    # Backward compatibility: legacy CBC payloads.
    return _decrypt_with_key_cbc(cipher_text, key)

def encrypt_aes(plain_text: str) -> str:
    return _encrypt_with_key(plain_text.encode('utf-8'), load_key("SECRET_KEY", 32))

def decrypt_aes(cipher_text: str) -> str:
    return _decrypt_with_key(cipher_text, load_key("SECRET_KEY", 32)).decode('utf-8')

def generate_dek() -> bytes:
    return get_random_bytes(32)

def generate_data_key() -> Tuple[bytes, str]:
    """
    Returns:
    - plaintext DEK bytes
    - encrypted DEK as base64 string
    """
    validate_encryption_config()
    if ENCRYPTION_PROVIDER == "kms":
        client = _get_kms_client()
        resp = client.generate_data_key(
            KeyId=KEK_KEY_ID,
            KeySpec="AES_256",
        )
        plaintext = resp["Plaintext"]
        ciphertext = resp["CiphertextBlob"]
        return plaintext, base64.b64encode(ciphertext).decode("utf-8")

    secret_key = load_key("SECRET_KEY", 32)
    dek = generate_dek()
    return dek, _encrypt_with_key(dek, secret_key)

def wrap_dek(dek: bytes) -> str:
    validate_encryption_config()
    if ENCRYPTION_PROVIDER == "kms":
        client = _get_kms_client()
        resp = client.encrypt(KeyId=KEK_KEY_ID, Plaintext=dek)
        return base64.b64encode(resp["CiphertextBlob"]).decode("utf-8")
    return _encrypt_with_key(dek, load_key("SECRET_KEY", 32))

def unwrap_dek(encrypted_dek: str, kek_key_id: Optional[str] = None) -> bytes:
    validate_encryption_config()
    if ENCRYPTION_PROVIDER == "kms":
        client = _get_kms_client()
        key_id = kek_key_id or KEK_KEY_ID
        resp = client.decrypt(
            KeyId=key_id,
            CiphertextBlob=base64.b64decode(encrypted_dek),
        )
        return resp["Plaintext"]
    return _decrypt_with_key(encrypted_dek, load_key("SECRET_KEY", 32))

def encrypt_with_dek(plain_text: str, dek: bytes) -> str:
    return _encrypt_with_key(plain_text.encode('utf-8'), dek)

def decrypt_with_dek(cipher_text: str, dek: bytes) -> str:
    return _decrypt_with_key(cipher_text, dek).decode('utf-8')

def get_kek_key_id() -> str:
    validate_encryption_config()
    return KEK_KEY_ID

# ======================================================
# Crypto
# ======================================================

def generate_blind_index(plain_text: str) -> str:
    signature = hmac.new(
        get_hash_key(),
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

