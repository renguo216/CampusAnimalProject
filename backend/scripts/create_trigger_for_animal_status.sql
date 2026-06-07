-- ==============================================
-- 动物领养状态自动更新脚本
-- 当t_adoptionapply表的status字段更新为1（已通过）时，
-- 自动将对应动物的status字段更新为1（已领养）
-- ==============================================

-- 1. 删除已存在的触发器（如果有）
DROP TRIGGER IF EXISTS trg_adoption_approved_update_animal;

-- 2. 创建触发器：当领养申请状态更新为已通过时，自动更新动物状态
DELIMITER //

CREATE TRIGGER trg_adoption_approved_update_animal
AFTER UPDATE ON t_adoptionapply
FOR EACH ROW
BEGIN
    -- 当申请状态从待审核(0)变为已通过(1)时
    IF OLD.status = 0 AND NEW.status = 1 THEN
        -- 更新对应动物的状态为已领养(1)
        UPDATE t_animal
        SET status = 1
        WHERE pet_id = NEW.pet_id;
    END IF;
END//

DELIMITER ;

-- 3. 测试：查询当前审核通过但动物状态未更新的记录
SELECT
    aa.apply_id AS 申请ID,
    aa.pet_id AS 动物ID,
    a.name AS 动物名称,
    a.status AS 当前动物状态,
    aa.status AS 申请状态
FROM t_adoptionapply aa
JOIN t_animal a ON aa.pet_id = a.pet_id
WHERE aa.status = 1 AND a.status = 0;

-- 4. 手动修复已存在的数据（如果有）
UPDATE t_animal a
JOIN t_adoptionapply aa ON a.pet_id = aa.pet_id
SET a.status = 1
WHERE aa.status = 1 AND a.status = 0;

-- 5. 验证修复结果
SELECT
    pet_id AS 动物ID,
    name AS 动物名称,
    CASE status
        WHEN 0 THEN '可领养'
        WHEN 1 THEN '已领养'
        ELSE '未知'
    END AS 状态
FROM t_animal
WHERE pet_id IN (SELECT pet_id FROM t_adoptionapply WHERE status = 1);

-- ==============================================
-- 完成
-- ==============================================

SELECT '✅ 脚本执行完成！触发器已创建，未来审核通过时动物状态会自动更新。' AS result;