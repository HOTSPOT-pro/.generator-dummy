CREATE INDEX IF NOT EXISTS idx_subscription_member
ON subscription(member_id);

CREATE INDEX IF NOT EXISTS idx_subscription_phone_hash
ON subscription(phone_hash);

CREATE INDEX IF NOT EXISTS idx_subscription_phone_key_version
ON subscription(phone_key_version);

CREATE INDEX IF NOT EXISTS idx_subscription_phone_key_bucket
ON subscription(phone_key_bucket_id);

CREATE INDEX IF NOT EXISTS idx_subscription_key_bucket_status
ON subscription_key(bucket_id, status);

CREATE UNIQUE INDEX IF NOT EXISTS uk_subscription_key_active
ON subscription_key(bucket_id)
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_family_sub_family
ON family_sub(family_id);

CREATE INDEX IF NOT EXISTS idx_policy_sub_sub
ON policy_sub(sub_id);

CREATE INDEX IF NOT EXISTS idx_policy_sub_policy
ON policy_sub(block_policy_id);

CREATE INDEX IF NOT EXISTS idx_family_apply_requester_status
ON family_apply(requester_sub_id, status);

CREATE INDEX IF NOT EXISTS idx_family_apply_target_apply
ON family_apply_target(family_apply_id);

CREATE INDEX IF NOT EXISTS idx_family_apply_target_sub
ON family_apply_target(target_sub_id);

CREATE INDEX IF NOT EXISTS idx_family_remove_schedule_status_date
ON family_remove_schedule(status, schedule_date);

CREATE INDEX IF NOT EXISTS idx_notification_sub
ON notification(sub_id);

CREATE INDEX IF NOT EXISTS idx_blocked_service_sub
ON blocked_service_sub(sub_id);

CREATE INDEX IF NOT EXISTS idx_present_data_target
ON present_data(target_sub_id);

CREATE UNIQUE INDEX uk_social_account_provider_social_id
ON social_account (provider, social_id)
WHERE is_deleted = false;

CREATE INDEX IF NOT EXISTS idx_family_active_list
ON family(family_id)
WHERE is_deleted = false;

CREATE INDEX IF NOT EXISTS idx_family_sub_family_role_sub
ON family_sub(family_id, family_role, sub_id);

CREATE INDEX IF NOT EXISTS idx_subscription_active_sub
ON subscription(sub_id)
WHERE is_deleted = false;

CREATE INDEX IF NOT EXISTS idx_member_active_member
ON member(member_id)
WHERE is_deleted = false;
