-- 创建触发器：当领养申请审核通过时，自动更新动物状态为已领养
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

DELIMITER ;

-- 创建触发器：当新增领养申请审核通过时（直接插入已通过状态）
DELIMITER $$

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