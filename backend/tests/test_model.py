# 文件路径: backend/tests/test_model.py

from backend.model.user import User
from backend.model.animal import Animal
from backend.model.adoption_apply import AdoptionApply
from backend.model.donation import Donation
from backend.model.post import Post
from backend.model.notice import Notice
from backend.model.reimbursement import Reimbursement
from backend.model.rescue_record import RescueRecord

def test_user():
    u = User("wx_123456", "小明", 1, avatarURL="http://example.com/avatar.jpg", points=10)
    print(f"User: {u.nickname}, 角色: {u.role}, 积分: {u.points}")

def test_animal():
    a = Animal("pet_001", "小花", "中华田园猫", status=0)
    print(f"Animal: {a.name}, 品种: {a.breed}, 状态: {a.status}")

def test_adoption_apply():
    apply = AdoptionApply("apply_001", "pet_001", "wx_123456", status=1, content="我很喜欢这只猫")
    print(f"AdoptionApply: 申请ID={apply.apply_id}, 状态={apply.status}")

def test_donation():
    d = Donation("don_001", 100.50, target_pet_id="pet_001")
    print(f"Donation: 金额={d.amount}, 目标宠物={d.target_pet_id}")

def test_post():
    p = Post("post_001", "今天在校园看到一只流浪猫，很可爱！", like_count=5)
    print(f"Post: 内容={p.content[:20]}..., 点赞数={p.like_count}")

def test_notice():
    n = Notice("notice_001", "领养须知", "请先阅读以下领养流程...")
    print(f"Notice: 标题={n.title}")

def test_reimbursement():
    r = Reimbursement("reimb_001", 50.00, status=1)
    print(f"Reimbursement: 金额={r.amount}, 状态={r.status}")

def test_rescue_record():
    record = RescueRecord("record_001", "图书馆后门", "发现一只腿部受伤的猫")
    print(f"RescueRecord: 位置={record.location}, 描述={record.description}")

if __name__ == "__main__":
    print("=== 开始测试所有 Model ===")
    test_user()
    test_animal()
    test_adoption_apply()
    test_donation()
    test_post()
    test_notice()
    test_reimbursement()
    test_rescue_record()
    print("=== 所有 Model 测试通过 ===")