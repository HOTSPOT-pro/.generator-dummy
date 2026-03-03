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
    birth VARCHAR(6),
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
    PRIMARY KEY ("social_account_id"),
    CONSTRAINT uk_social_account_provider_social_id UNIQUE (provider, social_id)
);

CREATE TABLE subscription (
    sub_id BIGSERIAL NOT NULL,
    plan_id BIGINT NOT NULL REFERENCES plan(plan_id),
    member_id BIGINT REFERENCES member(member_id),
    phone_enc VARCHAR(255) NOT NULL,
    phone_hash VARCHAR(64) NOT NULL,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("sub_id"),
    CONSTRAINT uk_subscription_member UNIQUE (member_id)
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
    PRIMARY KEY ("family_sub_id"),
    CONSTRAINT uk_family_sub_sub UNIQUE (sub_id)
);

CREATE TABLE notification (
    notification_id BIGSERIAL NOT NULL,
    sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    notification_type VARCHAR(50) NOT NULL,
    notification_title VARCHAR(100) NOT NULL,
    notification_content VARCHAR(200) NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    event_id VARCHAR(100) NOT NULL,
    PRIMARY KEY (notification_id),
    CONSTRAINT uk_notification_event_sub UNIQUE (event_id, sub_id)
);

CREATE TABLE family_apply (
    family_apply_id BIGSERIAL NOT NULL,
    requester_sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    family_id BIGINT,
    apply_type VARCHAR(10) NOT NULL,
    doc_url VARCHAR(255),
    status VARCHAR(20) NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("family_apply_id")
);

CREATE TABLE family_apply_target (
    family_apply_target_id BIGSERIAL NOT NULL,
    family_apply_id BIGINT NOT NULL REFERENCES family_apply(family_apply_id),
    target_sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    target_family_role VARCHAR(10) NOT NULL,
    PRIMARY KEY ("family_apply_target_id")
);

CREATE TABLE family_remove_schedule (
    family_remove_schedule_id BIGSERIAL NOT NULL,
    target_sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    family_id BIGINT NOT NULL REFERENCES family(family_id),
    status VARCHAR(20) NOT NULL,
    schedule_date DATE NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("family_remove_schedule_id")
);

CREATE TABLE notification_allow (
    notification_allow_id BIGSERIAL NOT NULL,
    sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    notification_category VARCHAR(20) NOT NULL,
    notification_allow BOOLEAN NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (notification_allow_id)
);

CREATE TABLE app_blocked_service (
    app_blocked_service_id BIGSERIAL NOT NULL,
    blocked_service_name VARCHAR(30) NOT NULL,
    blocked_service_code VARCHAR(30) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
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
    PRIMARY KEY ("blocked_service_sub_id"),
    CONSTRAINT uk_blocked_service_sub_sub_service UNIQUE (sub_id, blocked_service_id)
);

CREATE TABLE block_policy (
    block_policy_id BIGSERIAL NOT NULL,
    policy_name VARCHAR(30) NOT NULL,
    policy_description VARCHAR(255) NOT NULL DEFAULT '',
    family_id BIGINT,
    policy_type VARCHAR(20) NOT NULL,
    policy_snapshot JSON NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    modified_time TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY ("block_policy_id")
);

CREATE TABLE policy_sub (
    policy_sub_id BIGSERIAL NOT NULL,
    sub_id BIGINT NOT NULL REFERENCES subscription(sub_id),
    block_policy_id BIGINT NOT NULL REFERENCES block_policy(block_policy_id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
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

CREATE TABLE notification_outbox_event (
    id UUID NOT NULL,
    aggregatetype VARCHAR(100) NOT NULL,
    aggregateid   VARCHAR(100) NOT NULL,
    type          VARCHAR(100) NOT NULL,
    payload       TEXT NOT NULL,
    PRIMARY KEY (id)
);
