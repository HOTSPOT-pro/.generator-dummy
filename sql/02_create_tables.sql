CREATE TABLE plan (
    plan_id BIGSERIAL NOT NULL,
    plan_name VARCHAR(20) NOT NULL,
    plan_data_amount BIGINT NOT NULL,
    data_period VARCHAR(10) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("plan_id")
);

CREATE TABLE member (
    member_id BIGSERIAL NOT NULL,
    name VARCHAR(10) NOT NULL,
    birth VARCHAR(6) NOT NULL,
    status VARCHAR(10) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("member_id")
    
);

CREATE TABLE social_account (
    social_account_id BIGSERIAL NOT NULL,
    member_id BIGINT NOT NULL REFERENCES member(member_id),
    email VARCHAR(50) NOT NULL,
    social_id VARCHAR(50) NOT NULL,
    provider VARCHAR(10) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("social_account_id")
);

CREATE TABLE subscription (
    sub_id BIGSERIAL NOT NULL,
    plan_id BIGINT NOT NULL REFERENCES plan(plan_id),
    member_id BIGINT NOT NULL REFERENCES member(member_id),
    phone_enc VARCHAR(255) NOT NULL,
    phone_hash VARCHAR(64) NOT NULL,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("sub_id")
);

CREATE TABLE family (
    family_id BIGSERIAL NOT NULL,
    family_num INTEGER NOT NULL,
    family_data_amount BIGINT NOT NULL,
    priority_type VARCHAR(10) NOT NULL DEFAULT 'FIFO',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("family_id")
);

CREATE TABLE family_sub (
    family_sub_id BIGSERIAL NOT NULL,
    sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    family_id BIGINT NOT NULL REFERENCES family(family_id),
    family_role VARCHAR(10) NOT NULL,
    priority INTEGER,
    data_limit BIGINT,
    PRIMARY KEY ("family_sub_id")
);

CREATE TABLE notification (
    notification_id BIGSERIAL NOT NULL,
    sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    notification_type VARCHAR(50) NOT NULL,
    notification_content VARCHAR(200) NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    event_id VARCHAR(100) NOT NULL,
    PRIMARY KEY (notification_id),
    CONSTRAINT uk_notification_event_sub UNIQUE (event_id, sub_id)
);

CREATE TABLE family_apply (
    family_apply_id BIGSERIAL NOT NULL,
    requester_sub_id BIGINT NOT NULL,
    target_sub_id BIGINT NOT NULL,
    family_id BIGINT NOT NULL,
    doc_url VARCHAR(255),
    status VARCHAR(20) NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("family_apply_id")
);

CREATE TABLE notification_allow (
    notification_allow_id BIGSERIAL NOT NULL,
    sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    notification_category VARCHAR(20) NOT NULL,
    notification_allow BOOLEAN NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("notification_allow_id")
);

CREATE TABLE app_blocked_service (
    app_blocked_service_id BIGSERIAL NOT NULL,
    blocked_service_name VARCHAR(30) NOT NULL,
    blocked_service_code VARCHAR(30) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("app_blocked_service_id")
);

CREATE TABLE blocked_service_sub (
    blocked_service_sub_id BIGSERIAL NOT NULL,
    sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    blocked_service_id BIGINT NOT NULL REFERENCES app_blocked_service(app_blocked_service_id),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("blocked_service_sub_id")
);

CREATE TABLE block_policy (
    block_policy_id BIGSERIAL NOT NULL,
    policy_name VARCHAR(30) NOT NULL,
    policy_type VARCHAR(20) NOT NULL,
    policy_snapshot JSON NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("block_policy_id")
);

CREATE TABLE policy_sub (
    policy_sub_id BIGSERIAL NOT NULL,
    sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    date_snapshot JSON NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("policy_sub_id")
);

CREATE TABLE present_data (
    present_data_id BIGSERIAL NOT NULL,
    target_sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    provide_sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    data_amount BIGINT NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("present_data_id")
);

CREATE TABLE outbox_event (
    id UUID PRIMARY KEY,
    aggregatetype VARCHAR(100) NOT NULL,
    aggregateid VARCHAR(100) NOT NULL,
    type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT now()
);
