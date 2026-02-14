-- PLAN
INSERT INTO plan (
    plan_id, 
    plan_name, 
    plan_data_amount, 
    data_period,
    is_deleted,
    created_time,
    modified_time
)
VALUES
(1, '5G 시그니처', -1, 'MONTH', FALSE, now(), now()),
(2, '5G 스탠다드', 153600, 'MONTH', FALSE, now(), now()),
(3, '5G 베이직+', 24576, 'MONTH', FALSE, now(), now()),
(4, 'LTE 데이터 33', 1536, 'MONTH', FALSE, now(), now()),
(5, 'LTE 다이렉트 45', 1024, 'DAY', FALSE, now(), now());

-- APP BLOCKED SERVICE
INSERT INTO app_blocked_service (
    app_blocked_service_id,
    blocked_service_name,
    blocked_service_code,
    is_deleted,
    created_time,
    modified_time
)
VALUES
(1,'카카오톡','MSG_KAKAO', FALSE, now(), now()),
(2,'라인','MSG_LINE', FALSE, now(), now()),
(3,'유튜브','MEDIA_YOUTUBE', FALSE, now(), now()),
(4,'넷플릭스','MEDIA_NETFLIX', FALSE, now(), now()),
(5,'치지직','MEDIA_CHZZK', FALSE, now(), now()),
(6,'숲','MEDIA_SOOP', FALSE, now(), now()),
(7,'인스타그램','SNS_INSTAGRAM', FALSE, now(), now()),
(8,'틱톡','SNS_TIKTOK', FALSE, now(), now()),
(9,'페이스북','SNS_FACEBOOK', FALSE, now(), now()),
(10,'EBS','STUDY_EBS', FALSE, now(), now()),
(11,'메가스터디','STUDY_MEGA', FALSE, now(), now()),
(12,'업비트','FIN_UPBIT', FALSE, now(), now()),
(13,'키움증권','FIN_KIWOOM', FALSE, now(), now()),
(14,'크롬','WEB_CHROME', FALSE, now(), now()),
(15,'사파리','WEB_SAFARI', FALSE, now(), now()),
(16,'롤토체스','GAME_TFT', FALSE, now(), now()),
(17,'모바일배그','GAME_PUBG_M', FALSE, now(), now()),
(18,'네이버웹툰','TOON_NAVER', FALSE, now(), now()),
(19,'카카오웹툰','TOON_KAKAO', FALSE, now(), now());


-- BLOCK POLICY
INSERT INTO block_policy (
    block_policy_id,
    policy_name,
    policy_type,
    policy_snapshot,
    is_deleted,
    created_time,
    modified_time
)
VALUES
(1,'수면모드','SCHEDULED','{"days":["MON","TUE","WED","THU","FRI","SAT","SUN"],"startTime":"00:00","endTime":"07:00"}',FALSE,now(),now()),
(2,'방해 금지 모드','ONCE','{"durationMinutes":180}',FALSE,now(),now()),
(3,'수업 집중 모드','SCHEDULED','{"days":["MON","TUE","WED","THU","FRI"],"startTime":"09:00","endTime":"14:00"}',FALSE,now(),now()),
(4,'시험 기간 집중 모드','ONCE','{"startTime":"06:00","endTime":"23:59"}',FALSE,now(),now());
