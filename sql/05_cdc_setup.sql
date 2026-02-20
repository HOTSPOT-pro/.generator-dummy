-- Debezium CDC 설정

-- outbox_event 권한
GRANT SELECT ON TABLE public.outbox_event TO debezium;

-- WAL 기반 Logical Replication용
ALTER TABLE public.outbox_event REPLICA IDENTITY FULL;

-- publication 생성 (존재하면 무시)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_publication WHERE pubname = 'debezium_pub'
    ) THEN
        CREATE PUBLICATION debezium_pub
        FOR TABLE public.outbox_event;
    END IF;
END $$;