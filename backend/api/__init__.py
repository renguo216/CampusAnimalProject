"""
API 路由包

聚合所有 API 路由模块并注册到 FastAPI 应用。
使用 register_all_routers(app) 函数统一注册。
"""

from fastapi import FastAPI


def register_all_routers(app: FastAPI):
    """注册所有 API 路由到 FastAPI 应用"""
    from backend.api.user_api import router as user_router
    from backend.api.post_api import router as post_router
    from backend.api.animal_api import router as animal_router
    from backend.api.adoption_apply_api import router as adoption_apply_router
    from backend.api.comment_api import router as comment_router
    from backend.api.donation_api import router as donation_router
    from backend.api.donation_project_api import router as donation_project_router
    from backend.api.exchange_api import router as exchange_router
    from backend.api.exchange_product_api import router as exchange_product_router
    from backend.api.follow_api import router as follow_router
    from backend.api.like_api import router as like_router
    from backend.api.notice_api import router as notice_router
    from backend.api.reimbursement_api import router as reimbursement_router
    from backend.api.rescue_record_api import router as rescue_record_router
    from backend.api.volunteer_application_api import router as volunteer_application_router

    app.include_router(user_router)
    app.include_router(post_router)
    app.include_router(animal_router)
    app.include_router(adoption_apply_router)
    app.include_router(comment_router)
    app.include_router(donation_router)
    app.include_router(donation_project_router)
    app.include_router(exchange_router)
    app.include_router(exchange_product_router)
    app.include_router(follow_router)
    app.include_router(like_router)
    app.include_router(notice_router)
    app.include_router(reimbursement_router)
    app.include_router(rescue_record_router)
    app.include_router(volunteer_application_router)