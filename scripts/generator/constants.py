from enum import Enum


# ======================================================
# ENUM
# ======================================================

class NotificationType(str, Enum):
    # 정책
    TIME_WINDOW_POLICY_APPLIED = "TIME_WINDOW_POLICY_APPLIED"
    TIME_WINDOW_POLICY_RELEASED = "TIME_WINDOW_POLICY_RELEASED"
    IMMEDIATE_BLOCK_APPLIED = "IMMEDIATE_BLOCK_APPLIED"
    IMMEDIATE_BLOCK_RELEASED = "IMMEDIATE_BLOCK_RELEASED"

    # 앱 차단
    SERVICE_ACCESS_BLOCKED = "SERVICE_ACCESS_BLOCKED"
    SERVICE_ACCESS_RELEASED = "SERVICE_ACCESS_RELEASED"

    # 데이터 선물
    PRESENT_DATA = "PRESENT_DATA"

    # 데이터 사용량 (향후 대비)
    SINGLE_USAGE_THRESHOLD_50 = "SINGLE_USAGE_THRESHOLD_50"
    SINGLE_USAGE_THRESHOLD_30 = "SINGLE_USAGE_THRESHOLD_30"
    SINGLE_USAGE_THRESHOLD_10 = "SINGLE_USAGE_THRESHOLD_10"
    SINGLE_USAGE_EXHAUSTED = "SINGLE_USAGE_EXHAUSTED"

class FamilyRole(str, Enum):
    OWNER = "OWNER"
    PARENT = "PARENT"
    CHILD = "CHILD"

class PolicyType(str, Enum):
    SCHEDULED = "SCHEDULED"
    ONCE = "ONCE"

class PriorityType(str, Enum):
    FIFO = "FIFO"
    PRIORITY = "PRIORITY"

class NotificationCategory(str, Enum):
    DATA = "DATA"
    POLICY = "POLICY"
    APP_SERVICE = "APP_SERVICE"
    PRESENT = "PRESENT"


# ======================================================
# 상수
# ======================================================

TOTAL_USERS = 1_000_000
TOTAL_FAMILIES = 250_000

PRIORITY_FAMILY_RATE = 0.2
MOTHER_SAME_LASTNAME_RATE = 0.3

FAMILY_SIZES = [2, 3, 4, 5, 6, 7, 8]
FAMILY_SIZE_WEIGHTS = [30, 30, 20, 10, 5, 3, 2]

KB = 1
MB = 1024 * KB
GB = 1024 * MB

PLANS = {
    1: {'name': '5G 시그니처', 'amount': -1, 'period': 'MONTH'},  # 무제한
    2: {'name': '5G 스탠다드', 'amount': 150 * GB, 'period': 'MONTH'},     # 150GB
    3: {'name': '5G 베이직+', 'amount': 24 * GB, 'period': 'MONTH'},      # 24GB
    4: {'name': 'LTE 데이터 33', 'amount': int(1.5 * GB), 'period': 'MONTH'},  # 1.5GB
    5: {'name': 'LTE 다이렉트 45', 'amount': 1 * GB, 'period': 'DAY'},     # 1GB/day
}

PROVIDERS = ['KAKAO', 'GOOGLE']

APP_BLOCKED_SERVICES = [
    ("카카오톡", "MSG_KAKAO"), 
    ("라인", "MSG_LINE"), 
    ("유튜브", "MEDIA_YOUTUBE"), 
    ("넷플릭스", "MEDIA_NETFLIX"), 
    ("치지직", "MEDIA_CHZZK"), 
    ("숲", "MEDIA_SOOP"), 
    ("인스타그램", "SNS_INSTAGRAM"), 
    ("틱톡", "SNS_TIKTOK"), 
    ("페이스북", "SNS_FACEBOOK"), 
    ("EBS", "STUDY_EBS"), 
    ("메가스터디", "STUDY_MEGA"), 
    ("업비트", "FIN_UPBIT"), 
    ("키움증권", "FIN_KIWOOM"), 
    ("크롬", "WEB_CHROME"), 
    ("사파리", "WEB_SAFARI"), 
    ("롤토체스", "GAME_TFT"), 
    ("모바일배그", "GAME_PUBG_M"), 
    ("네이버웹툰", "TOON_NAVER"), 
    ("카카오웹툰", "TOON_KAKAO")
]

PREFERRED_CODES = [
    "SNS_INSTAGRAM",
    "SNS_TIKTOK",
    "SNS_FACEBOOK",
    "GAME_TFT",
    "GAME_PUBG_M",
    "MEDIA_YOUTUBE",
    "MEDIA_NETFLIX",
    "MEDIA_CHZZK",
    "MEDIA_SOOP",
    "TOON_NAVER",
    "TOON_KAKAO",
    "FIN_UPBIT",
    "FIN_KIWOOM"
]

block_policies = [
        {
            "name": "수면모드",
            "type": PolicyType.SCHEDULED,
            "snapshot": {
                "days": ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"],
                "startTime": "00:00",
                "endTime": "07:00"
            }
        },
        {
            "name": "방해 금지 모드",
            "type": PolicyType.ONCE,
            "snapshot": {
                "durationMinutes": 180
            }
        },
        {
            "name": "수업 집중 모드",
            "type": PolicyType.SCHEDULED,
            "snapshot": {
                "days": ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"],
                "startTime": "09:00",
                "endTime": "14:00"
            }
        },
        {
            "name": "시험 기간 집중 모드",
            "type": PolicyType.ONCE,
            "snapshot": {
                "startTime": "06:00",
                "endTime": "23:59"
            }
        }
    ]

LAST_NAMES = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '신', '한']

LAST_NAME_WEIGHTS = [
    21, 15, 8, 5, 4, 3, 2.5, 2, 2, 1.5, 1.5, 1
]

FIRST_SYLLABLES = [
    "민","서","지","현","우","준","예","수","도","채",
    "하","유","은","진","다","아","태","성","주","경"
]

SECOND_SYLLABLES = [
    "훈","빈","영","림","호","원","윤","희","연","아",
    "현","준","민","솔","찬","혁","진","은","재","린"
]
