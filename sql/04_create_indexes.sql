CREATE INDEX IF NOT EXISTS idx_subscription_member
ON subscription(member_id);

CREATE INDEX IF NOT EXISTS idx_subscription_phone_hash
ON subscription(phone_hash);

CREATE INDEX IF NOT EXISTS idx_family_sub_family
ON family_sub(family_id);

CREATE INDEX IF NOT EXISTS idx_policy_sub_sub
ON policy_sub(sub_id);

CREATE INDEX IF NOT EXISTS idx_notification_sub
ON notification(sub_id);

CREATE INDEX IF NOT EXISTS idx_blocked_service_sub
ON blocked_service_sub(sub_id);

CREATE INDEX IF NOT EXISTS idx_present_data_target
ON present_data(target_sub_id);
