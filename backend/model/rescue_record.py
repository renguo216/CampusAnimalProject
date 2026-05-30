class RescueRecord:
    def __init__(self, record_id, user_id, helper_id=None, pet_id=None,
                 title=None, location=None, description=None, status=0,
                 found_location_text=None, need_type=None, photo_urls=None,
                 priority=0, animal_name=None, resolved_by=None,
                 location_lat=None, location_lng=None,
                 updated_at=None, completed_at=None, is_deleted=0,
                 created_at=None):
        self.record_id = record_id              # 记录编号
        self.user_id = user_id                  # 上报人ID
        self.helper_id = helper_id              # 接单志愿者ID（可空）
        self.pet_id = pet_id                    # 关联动物ID（可空）
        self.title = title                      # 救助标题
        self.location = location                # 发现位置（经纬度或地址）
        self.description = description          # 情况说明
        self.status = status                    # 状态：0-待接单，1-救助中，2-待确认，3-已完成，4-已关闭
        self.found_location_text = found_location_text  # 前端显示的位置文本
        self.need_type = need_type              # 需求类型
        self.photo_urls = photo_urls            # 救助图片链接（JSON数组）
        self.priority = priority                # 优先级：0-普通，1-紧急，2-非常紧急
        self.animal_name = animal_name          # 暂时使用的动物名字（未建档前）
        self.resolved_by = resolved_by          # 完成/关闭操作人ID
        self.location_lat = location_lat        # 精确纬度
        self.location_lng = location_lng        # 精确经度
        self.updated_at = updated_at            # 最后修改时间
        self.completed_at = completed_at        # 救助完成或关闭的时间
        self.is_deleted = is_deleted            # 软删除标记：0-未删除，1-已删除
        self.created_at = created_at            # 创建时间