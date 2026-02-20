import os
import sys
import psycopg2

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.db_config import DB_CONFIG, OUTPUT_DIR

# SQL 파일 경로
SQL_DIR = os.path.join(PROJECT_ROOT, 'sql')

# SQL 파일 목록 (실행 순서)
SQL_FILES = [
    '01_drop_tables.sql',
    '02_create_tables.sql',
    '03_insert_master_data.sql'
]

CSV_TABLE_MAPPING = [
    ("member.csv", "member"),
    ("social_account.csv", "social_account"),
    ("subscription.csv", "subscription"),
    ("family.csv", "family"),
    ("family_sub.csv", "family_sub"),
    ("notification_allow.csv", "notification_allow"),
    ("policy_sub.csv", "policy_sub"),
    ("blocked_service_sub.csv", "blocked_service_sub"),
    ("present_data.csv", "present_data"),
    ("notification.csv", "notification"),
]

TABLE_PK_MAP = {
    "member": "member_id",
    "social_account": "social_account_id",
    "subscription": "sub_id",
    "family": "family_id",
    "family_sub": "family_sub_id",
    "notification_allow": "notification_allow_id",
    "policy_sub": "policy_sub_id",
    "blocked_service_sub": "blocked_service_sub_id",
    "present_data": "present_data_id",
    "notification": "notification_id",
}


def load_sql(filename):
    """SQL 파일 로드"""
    filepath = os.path.join(SQL_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def get_connection():
    """DB 연결 생성"""
    return psycopg2.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )


def init_tables(conn):
    """테이블 초기화 (DROP/CREATE)"""
    print("테이블 초기화 중...")

    with conn.cursor() as cur:
        for sql_file in SQL_FILES:
            print(f"  - {sql_file} 실행")
            sql = load_sql(sql_file)
            cur.execute(sql)

    conn.commit()
    print("테이블 초기화 완료!\n")


def load_csv(conn, csv_file, table_name):
    """CSV 파일을 테이블에 COPY"""
    csv_path = os.path.join(OUTPUT_DIR, csv_file)

    if not os.path.exists(csv_path):
        print(f"  [SKIP] {csv_file} 파일이 없습니다.")
        return 0

    with conn.cursor() as cur:
        with open(csv_path, 'r', encoding='utf-8') as f:
            copy_sql = f'COPY "{table_name}" FROM STDIN WITH (FORMAT CSV, NULL \'\\N\')'
            cur.copy_expert(copy_sql, f)

        # 삽입된 행 수 확인
        cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        count = cur.fetchone()[0]

    return count


def load_all_csv(conn):
    """모든 CSV 파일 로드"""
    print("CSV 데이터 로드 중...")
    print(f"CSV 파일 경로: {OUTPUT_DIR}\n")

    for csv_file, table_name in CSV_TABLE_MAPPING:
        print(f"  - {csv_file} -> {table_name}", end=" ")
        count = load_csv(conn, csv_file, table_name)
        print(f"({count:,} rows)")

    conn.commit()
    print("\nCSV 데이터 로드 완료!\n")


def create_indexes(conn):
    """인덱스 생성 (데이터 적재 후)"""
    print("인덱스 생성 중...")
    try:
        sql = load_sql('04_create_indexes.sql')
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("  - 04_create_indexes.sql 실행 완료")
    except Exception as e:
        print(f"  [ERROR] 인덱스 생성 실패: {e}")
        conn.rollback()
        raise

    print("인덱스 생성 완료!\n")


def reset_sequences(conn):
    """
    데이터 적재 후 시퀀스(PK) 값을 데이터 최대값으로 동기화
    """
    print("시퀀스(PK) 재설정 중...")
    
    with conn.cursor() as cur:
        for table, pk_col in TABLE_PK_MAP.items():
            try:
                sql = f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', '{pk_col}'), 
                        COALESCE((SELECT MAX({pk_col}) FROM "{table}"), 0) + 1, 
                        false
                    );
                """
                cur.execute(sql)
                print(f"  - {table}: 시퀀스 동기화 완료")
            except Exception as e:
                print(f"  - [SKIP] {table}: 시퀀스 없음 또는 설정 불가")

    conn.commit()
    print("시퀀스 재설정 완료!\n")

def verify_data(conn):
    """데이터 검증 (각 테이블 COUNT)"""
    print("데이터 검증 중...")

    tables = [
        "member",
        "social_account",
        "subscription",
        "family",
        "family_sub",
        "notification_allow",
        "policy_sub",
        "blocked_service_sub",
        "present_data",
        "notification"
    ]

    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cur.fetchone()[0]
            print(f"  - {table}: {count:,} rows")

    print("검증 완료!")


def main():
    print("=" * 60)
    print("CSV to PostgreSQL Loader")
    print("=" * 60 + "\n")

    try:
        conn = get_connection()
        print(f"DB 연결 성공: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}\n")

        # 1. 테이블 초기화
        init_tables(conn)

        # 2. CSV 로드
        load_all_csv(conn)
        
        # 3. 인덱스 생성
        create_indexes(conn)

        # 4. 시퀀스 재설정
        reset_sequences(conn)

        # 5. 검증
        verify_data(conn)

        conn.close()
        print("\n데이터 로드 완료!")

    except psycopg2.Error as e:
        print(f"\n[ERROR] DB 오류: {e}")
        raise
    except Exception as e:
        print(f"\n[ERROR] {e}")
        raise


if __name__ == "__main__":
    main()