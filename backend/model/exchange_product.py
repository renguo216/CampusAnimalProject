class ExchangeProduct:
    def __init__(self, product_id, name, description=None,
                 points_required=0, image_url=None, stock=0,
                 status=1, created_at=None):
        self.product_id = product_id          # 商品ID
        self.name = name                      # 商品名称
        self.description = description        # 商品描述
        self.points_required = points_required  # 所需积分
        self.image_url = image_url            # 商品图片
        self.stock = stock                    # 库存数量
        self.status = status                  # 状态：0-下架，1-上架
        self.created_at = created_at          # 创建时间