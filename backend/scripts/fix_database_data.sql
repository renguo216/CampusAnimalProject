-- ==============================================
-- 数据库数据修复脚本
-- 1. 修复photo_urls字段的绝对URL问题
-- 2. 创建触发器确保审核通过后动物状态自动更新
-- ==============================================

USE campus_animal;

-- ==============================================
-- 第一部分：修复photo_urls字段的绝对URL
-- ==============================================

-- 创建临时表存储修复数据
DROP TABLE IF EXISTS temp_fix_photo_urls;
CREATE TEMPORARY TABLE temp_fix_photo_urls (
    pet_id INT,
    old_photo_urls TEXT,
    new_photo_urls TEXT
);

-- 提取需要修复的记录
INSERT INTO temp_fix_photo_urls (pet_id, old_photo_urls)
SELECT pet_id, photo_urls 
FROM t_animal 
WHERE photo_urls IS NOT NULL 
  AND (photo_urls LIKE '%http://%' OR photo_urls LIKE '%https://%');

-- 更新记录：将绝对URL替换为相对路径
UPDATE t_animal a
JOIN temp_fix_photo_urls t ON a.pet_id = t.pet_id
SET a.photo_urls = REGEXP_REPLACE(
    a.photo_urls,
    'https?://[^/]+/uploads/',
    '/uploads/'
);

-- 查看修复结果
SELECT pet_id, photo_urls FROM t_animal WHERE pet_id IN (SELECT pet_id FROM temp_fix_photo_urls);

SELECT CONCAT('修复了 ', COUNT(*), ' 条记录') AS result FROM temp_fix_photo_urls;

-- ==============================================
-- 第二部分：创建触发器确保审核通过后动物状态自动更新
-- ==============================================

DELIMITER $$

-- 删除已存在的触发器
DROP TRIGGER IF EXISTS trg_update_animal_status_after_adoption_approved;

CREATE TRIGGER trg_update_animal_status_after_adoption_approved
AFTER UPDATE ON t_adoptionapply
FOR EACH ROW
BEGIN
    -- 当申请状态从待审核(0)变为已通过(1)时
    IF OLD.status = 0 AND NEW.status = 1 THEN
        -- 更新动物状态为已领养(1)
        UPDATE t_animal 
        SET status = 1 
        WHERE pet_id = NEW.pet_id;
    END IF;
END$$

-- 创建触发器：当新增领养申请审核通过时（直接插入已通过状态）
DROP TRIGGER IF EXISTS trg_update_animal_status_after_adoption_insert;

CREATE TRIGGER trg_update_animal_status_after_adoption_insert
AFTER INSERT ON t_adoptionapply
FOR EACH ROW
BEGIN
    -- 当申请状态直接为已通过(1)时
    IF NEW.status = 1 THEN
        -- 更新动物状态为已领养(1)
        UPDATE t_animal 
        SET status = 1 
        WHERE pet_id = NEW.pet_id;
    END IF;
END$$

DELIMITER ;

SELECT '触发器创建成功' AS result;

-- ==============================================
-- 第三部分：手动更新已审核通过但动物状态未更新的记录
-- ==============================================

-- 更新所有审核通过但动物状态仍为可领养的记录
UPDATE t_animal a
JOIN t_adoptionapply aa ON a.pet_id = aa.pet_id
SET a.status = 1
WHERE aa.status = 1 AND a.status = 0;

SELECT CONCAT('更新了 ', ROW_COUNT(), ' 条动物状态') AS result;

-- ==============================================
-- 完成
-- ==============================================

SELECT '数据库修复完成！' AS final_result;