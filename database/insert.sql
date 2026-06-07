-- ============================================
-- 插入测试数据（与完整表结构匹配）
-- ============================================

-- 1. 用户表
INSERT INTO `t_user` (`user_id`, `nickname`, `avatarURL`, `role`, `points`, `volunteer_id`, `admin_id`, `level`, `phone_number`, `like_count`, `follower_count`, `following_count`, `is_active`, `created_at`) VALUES
('user_001', '热心小张', 'https://example.com/avatar1.jpg', 1, 120, NULL, NULL, NULL, '13800138001', 5, 2, 3, 1, NOW()),
('user_002', '志愿者小李', 'https://example.com/avatar2.jpg', 2, 350, 'VOL2024001', NULL, 2, '13800138002', 28, 15, 10, 1, NOW()),
('user_003', '管理员王老师', 'https://example.com/avatar3.jpg', 3, 500, NULL, 'ADMIN001', NULL, '13800138003', 10, 8, 5, 1, NOW()),
('user_004', '爱猫小陈', 'https://example.com/avatar4.jpg', 1, 80, NULL, NULL, NULL, '13800138004', 2, 1, 6, 1, NOW()),
('user_005', '救助达人', 'https://example.com/avatar5.jpg', 2, 620, 'VOL2024002', NULL, 3, '13800138005', 45, 22, 12, 1, NOW());

-- 2. 动物档案表
INSERT INTO `t_animal` (`name`, `breed`, `color`, `vector`, `status`, `age`, `gender`, `is_neutered`, `is_vaccinated`, `personality`, `description`, `photo_urls`, `found_location`, `created_at`) VALUES
('橘座', '中华田园猫', '橘色', '{"fur":"short","size":"medium"}', 0, 18, 1, 1, 1, '亲人、贪吃、爱晒太阳', '橘座是学校食堂附近的常客，性格温和。', '["https://example.com/juzuo1.jpg"]', '第一食堂门口花坛', NOW()),
('小白', '中华田园猫', '白色', '{"fur":"long","size":"small"}', 0, 8, 2, 0, 1, '胆小但温柔', '小白在图书馆附近被发现。', '["https://example.com/xiaobai1.jpg"]', '图书馆北侧灌木丛', NOW()),
('大黄', '中华田园犬', '黄褐色', '{"fur":"short","size":"large"}', 2, 36, 1, 1, 1, '忠诚、护校', '大黄是学校的“保安队长”。', '["https://example.com/dahuang1.jpg"]', '操场看台下方', NOW()),
('花花', '三花猫', '三花', '{"fur":"short","size":"medium"}', 0, 12, 2, 1, 1, '活泼好动', '花花是女生宿舍的团宠。', '["https://example.com/huahua1.jpg"]', '女生宿舍7号楼前', NOW()),
('小黑', '奶牛猫', '黑白', '{"fur":"short","size":"small"}', 1, 24, 1, 1, 1, '独立高冷', '小黑已被领养。', '["https://example.com/xiaohei1.jpg"]', '教学楼B区停车场', NOW());

-- 3. 募捐项目表
INSERT INTO `t_donation_project` (`title`, `description`, `target_amount`, `current_amount`, `participant_count`, `status`, `created_at`) VALUES
('流浪猫过冬物资', '购买猫粮、猫窝和驱虫药', 5000.00, 3250.00, 42, 1, NOW()),
('大黄后腿治疗', '拍片和药物治疗', 3000.00, 1850.00, 23, 1, NOW()),
('校园TNR计划', '抓捕-绝育-放归', 8000.00, 2100.00, 15, 1, NOW()),
('动物救助站修缮', '修缮围栏和猫舍', 10000.00, 10000.00, 67, 0, DATE_SUB(NOW(), INTERVAL 30 DAY)),
('应急医疗基金', '紧急救治', 20000.00, 5600.00, 88, 1, NOW());

-- 4. 积分商品表
INSERT INTO `t_exchange_product` (`name`, `description`, `points_required`, `image_url`, `stock`, `status`, `created_at`) VALUES
('定制动物徽章', '一套4枚金属徽章', 50, 'https://example.com/badge.jpg', 100, 1, NOW()),
('猫咪帆布袋', '环保帆布袋', 120, 'https://example.com/bag.jpg', 50, 1, NOW()),
('动物救助明信片', '一套12张', 30, 'https://example.com/card.jpg', 200, 1, NOW()),
('宠物零食礼包', '进口零食混合装', 200, 'https://example.com/snack.jpg', 30, 1, NOW()),
('志愿者T恤', '纯棉T恤', 180, 'https://example.com/shirt.jpg', 40, 0, NOW());

-- 5. 帖子表
INSERT INTO `t_post` (`post_id`, `user_id`, `content`, `image_urls`, `like_count`, `comment_count`, `share_count`, `status`, `created_at`) VALUES
('post_001', 'user_001', '今天在食堂门口看到橘座晒太阳，太可爱了！', '["https://example.com/post1_1.jpg"]', 12, 3, 2, 1, NOW()),
('post_002', 'user_002', '救助站今天给小白洗了澡，有想领养的吗？', '["https://example.com/post2_1.jpg"]', 28, 5, 4, 1, NOW()),
('post_003', 'user_005', '紧急！图书馆后面有只受伤的鸟，求帮助！', '["https://example.com/post3_1.jpg"]', 7, 2, 1, 1, NOW()),
('post_004', 'user_003', '【公告】本周六救助站开放参观，欢迎报名', NULL, 15, 8, 6, 1, NOW()),
('post_005', 'user_004', '花花今天在宿舍楼下对我喵喵叫，太治愈了', '["https://example.com/post5_1.jpg"]', 9, 1, 0, 0, NOW());

-- 6. 系统公告表
INSERT INTO `t_notice` (`notice_id`, `title`, `content`, `is_top`, `created_at`) VALUES
('NOT2024001', '春季动物疫苗接种通知', '请志愿者协助接种疫苗', 1, NOW()),
('NOT2024002', '领养流程更新公告', '审核时间缩短为3个工作日', 0, NOW()),
('NOT2024003', '动物救助站值班表（5月）', '5月值班安排已发布', 0, NOW()),
('NOT2024004', '积分商城上新啦', '新上线动物主题文具', 1, NOW()),
('NOT2024005', '救助记录填写规范提醒', '请提供准确位置和照片', 0, NOW());

-- 7. 评论表
INSERT INTO `t_comment` (`post_id`, `user_id`, `content`, `parent_comment_id`, `like_count`, `created_at`) VALUES
('post_001', 'user_002', '橘座真的很亲人，每次路过都会蹭蹭', NULL, 5, NOW()),
('post_001', 'user_004', '我也有拍到它！改天发出来', NULL, 2, NOW()),
('post_002', 'user_005', '小白性格怎么样？适合新手吗？', NULL, 3, NOW()),
('post_002', 'user_001', '回复：小白比较胆小，建议有耐心的同学', 3, 1, NOW()),
('post_004', 'user_002', '已经报名了，期待参观！', NULL, 4, NOW());

-- 8. 领养申请表
INSERT INTO `t_adoptionapply` (`apply_id`, `pet_id`, `user_id`, `status`, `content`, `review_comment`, `created_at`) VALUES
('APP2024001', 2, 'user_001', 1, '我非常喜欢小白，家里已准备齐全', '审核通过，请保持联系', NOW()),
('APP2024002', 1, 'user_004', 0, '橘座太可爱了，想领养', NULL, NOW()),
('APP2024003', 4, 'user_002', 0, '花花和我很投缘', NULL, NOW()),
('APP2024004', 3, 'user_005', 2, '想领养大黄，但宿舍条件有限', '抱歉，大黄需要较大空间', NOW()),
('APP2024005', 5, 'user_003', 1, '小黑已在我家生活两周，补办手续', '确认领养成功', NOW());

-- 9. 捐赠记录表
INSERT INTO `t_donation` (`donation_id`, `user_id`, `project_id`, `amount`, `created_at`, `status`, `reviewed_by`, `reviewed_at`, `review_comment`) VALUES
('DON2024001', 'user_001', 1, 50.00, NOW(), 1, 'user_003', NOW(), '已到账'),
('DON2024002', 'user_002', 2, 100.00, NOW(), 1, 'user_003', NOW(), '已到账'),
('DON2024003', 'user_004', 1, 20.00, NOW(), 1, 'user_003', NOW(), '已到账'),
('DON2024004', 'user_005', 3, 200.00, NOW(), 0, NULL, NULL, NULL),
('DON2024005', 'user_003', 5, 500.00, NOW(), 1, 'user_003', NOW(), '管理员代捐');

-- 10. 积分兑换记录表
INSERT INTO `t_exchange` (`user_id`, `product_id`, `points_used`, `status`, `created_at`, `updated_at`, `reviewed_by`, `reviewed_at`, `review_comment`, `contact_info`) VALUES
('user_002', 1, 50, 1, NOW(), NOW(), 'user_003', NOW(), '已发货', '13800138002'),
('user_001', 3, 30, 0, NOW(), NULL, NULL, NULL, NULL, 'user001@example.com'),
('user_005', 2, 120, 1, NOW(), NOW(), 'user_003', NOW(), '待领取', '宿舍3号楼101'),
('user_004', 4, 200, 2, NOW(), NOW(), 'user_003', NOW(), '库存不足', '13800138004'),
('user_003', 5, 180, 1, NOW(), NOW(), 'user_003', NOW(), '内部兑换', '办公室A201');

-- 11. 关注表
INSERT INTO `t_follow` (`from_user_id`, `to_user_id`, `created_at`) VALUES
('user_001', 'user_002', NOW()),
('user_001', 'user_005', NOW()),
('user_004', 'user_002', NOW()),
('user_004', 'user_003', NOW()),
('user_005', 'user_002', NOW());

-- 12. 点赞表
INSERT INTO `t_like` (`target_type`, `target_id`, `target_owner_id`, `user_id`, `is_deleted`, `created_at`) VALUES
('post', 'post_001', 'user_001', 'user_002', 0, NOW()),
('post', 'post_001', 'user_001', 'user_004', 0, NOW()),
('comment', '4', 'user_001', 'user_005', 0, NOW()),
('post', 'post_002', 'user_002', 'user_001', 0, NOW()),
('post', 'post_004', 'user_003', 'user_005', 0, NOW());

-- 13. 积分变动日志表
INSERT INTO `t_points_log` (`user_id`, `delta`, `before_points`, `after_points`, `reason`, `created_at`) VALUES
('user_001', 10, 110, 120, '发帖奖励', NOW()),
('user_001', -30, 120, 90, '兑换商品', NOW()),
('user_002', 20, 330, 350, '完成救助任务', NOW()),
('user_005', 50, 570, 620, '捐赠奖励', NOW()),
('user_004', 5, 75, 80, '评论获赞', NOW());

-- 14. 报销单表
INSERT INTO `t_reimbursement` (`reimb_id`, `user_id`, `amount`, `status`, `type`, `description`, `receipt_urls`, `review_comment`, `reviewed_by`, `reviewed_at`, `updated_at`, `pet_id`, `project_id`, `created_at`) VALUES
('REB2024001', 'user_002', 150.00, 1, '医疗', '购买大黄的消炎药', '["https://example.com/receipt1.jpg"]', '符合规定', 'user_003', NOW(), NOW(), 3, 2, NOW()),
('REB2024002', 'user_005', 80.00, 0, '物资', '购买猫粮5kg', '["https://example.com/receipt2.jpg"]', NULL, NULL, NULL, NULL, 1, 1, NOW()),
('REB2024003', 'user_001', 200.00, 2, '医疗', '受伤小鸟检查费', '["https://example.com/receipt3.jpg"]', '缺少发票', 'user_003', NOW(), NOW(), NULL, 5, NOW()),
('REB2024004', 'user_004', 45.00, 1, '其他', '购买猫砂盆', '["https://example.com/receipt4.jpg"]', '已通过', 'user_003', NOW(), NOW(), 2, NULL, NOW()),
('REB2024005', 'user_002', 300.00, 0, '医疗', '花花绝育手术', '["https://example.com/receipt5.jpg"]', NULL, NULL, NULL, NULL, 4, 3, NOW());

-- 15. 救助记录表（包含完整字段）
INSERT INTO `t_rescuerecord` (`record_id`, `user_id`, `helper_id`, `pet_id`, `title`, `location`, `description`, `status`, `found_location_text`, `need_type`, `photo_urls`, `priority`, `resolved_by`, `animal_name`, `location_lat`, `location_lng`, `updated_at`, `completed_at`, `is_deleted`, `created_at`) VALUES
('RES2024001', 'user_001', 'user_002', 3, '大黄后腿受伤', '操场看台', '走路一瘸一拐', 3, '操场看台下方', '医疗', '["https://example.com/rescue1.jpg"]', 2, 'user_002', '大黄', 39.9042000, 116.4074000, NOW(), NOW(), 0, NOW()),
('RES2024002', 'user_004', 'user_005', NULL, '教学楼幼猫', '教学楼B区', '空调外机下发现幼猫', 1, '教学楼B区东侧', '救援', '["https://example.com/rescue2.jpg"]', 1, NULL, '小咪', 39.9041000, 116.4072000, NOW(), NULL, 0, NOW()),
('RES2024003', 'user_005', 'user_002', 1, '橘座打架受伤', '第一食堂', '脸部有抓伤', 3, '食堂门口', '医疗', '["https://example.com/rescue3.jpg"]', 1, 'user_002', '橘座', 39.9045000, 116.4076000, NOW(), NOW(), 0, NOW()),
('RES2024004', 'user_002', NULL, NULL, '鸟类救助', '图书馆', '鸽子翅膀受伤', 0, '图书馆门口台阶', '救援', '["https://example.com/rescue4.jpg"]', 1, NULL, '鸽子', 39.9043000, 116.4077000, NOW(), NULL, 0, NOW()),
('RES2024005', 'user_003', 'user_005', 4, '花花被困树上', '女生宿舍', '爬树下不来', 3, '女生宿舍7号楼前', '救援', '["https://example.com/rescue5.jpg"]', 0, 'user_005', '花花', 39.9046000, 116.4071000, NOW(), NOW(), 0, NOW());

-- 16. 志愿者申请表
INSERT INTO `t_volunteer_application` (`user_id`, `status`, `apply_content`, `review_comment`, `reviewed_by`, `reviewed_at`, `updated_at`, `created_at`) VALUES
('user_001', 1, '我每天都有空，很喜欢小动物', '欢迎加入', 'user_003', NOW(), NOW(), NOW()),
('user_004', 0, '我想为校园动物尽一份力', NULL, NULL, NULL, NULL, NOW()),
('user_005', 1, '已参与多次救助，希望正式加入', '表现积极', 'user_003', NOW(), NOW(), NOW()),
('user_002', 2, '之前申请过，但现在课业繁忙', '建议有空再申请', 'user_003', NOW(), NOW(), NOW()),
('user_003', 1, '管理员自荐', '特殊批准', 'user_003', NOW(), NOW(), NOW());