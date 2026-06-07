from flask import Flask


def register_all_blueprints(app: Flask, url_prefix: str = ''):
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
    from backend.api.ai_api import router as ai_router
    from backend.api.user_profile_api import router as user_profile_router
    from backend.api.volunteer_task_api import router as volunteer_task_router
    from backend.api.admin_api import router as admin_router
    from backend.api.hospital_api import router as hospital_router
    from backend.api.upload_api import router as upload_router

    if url_prefix:
        app.register_blueprint(user_router, url_prefix=f'{url_prefix}/user')
        app.register_blueprint(post_router, url_prefix=f'{url_prefix}/community')
        app.register_blueprint(animal_router, url_prefix=f'{url_prefix}/animals')
        app.register_blueprint(adoption_apply_router, url_prefix=f'{url_prefix}/adoption')
        app.register_blueprint(comment_router, url_prefix=f'{url_prefix}/comment')
        app.register_blueprint(donation_router, url_prefix=f'{url_prefix}/donation')
        app.register_blueprint(donation_project_router, url_prefix=f'{url_prefix}/donation')
        app.register_blueprint(exchange_router, url_prefix=f'{url_prefix}/points')
        app.register_blueprint(exchange_product_router, url_prefix=f'{url_prefix}/points')
        app.register_blueprint(follow_router, url_prefix=f'{url_prefix}/user')
        app.register_blueprint(like_router, url_prefix=f'{url_prefix}/community')
        app.register_blueprint(notice_router, url_prefix=f'{url_prefix}/notice')
        app.register_blueprint(reimbursement_router, url_prefix=f'{url_prefix}/reimbursement')
        app.register_blueprint(rescue_record_router, url_prefix=f'{url_prefix}/rescue')
        app.register_blueprint(volunteer_application_router, url_prefix=f'{url_prefix}/volunteer')
        app.register_blueprint(ai_router, url_prefix=f'{url_prefix}/ai')
        app.register_blueprint(user_profile_router, url_prefix=f'{url_prefix}/user')
        app.register_blueprint(volunteer_task_router, url_prefix=f'{url_prefix}/volunteer')
        app.register_blueprint(admin_router, url_prefix=f'{url_prefix}/admin')
        app.register_blueprint(hospital_router, url_prefix=f'{url_prefix}/hospitals')
        app.register_blueprint(upload_router, url_prefix=f'{url_prefix}/upload')
    else:
        app.register_blueprint(user_router)
        app.register_blueprint(post_router)
        app.register_blueprint(animal_router)
        app.register_blueprint(adoption_apply_router)
        app.register_blueprint(comment_router)
        app.register_blueprint(donation_router)
        app.register_blueprint(donation_project_router)
        app.register_blueprint(exchange_router)
        app.register_blueprint(exchange_product_router)
        app.register_blueprint(follow_router)
        app.register_blueprint(like_router)
        app.register_blueprint(notice_router)
        app.register_blueprint(reimbursement_router)
        app.register_blueprint(rescue_record_router)
        app.register_blueprint(volunteer_application_router)
        app.register_blueprint(ai_router)
        app.register_blueprint(user_profile_router)
        app.register_blueprint(volunteer_task_router)
        app.register_blueprint(admin_router)
        app.register_blueprint(hospital_router)
        app.register_blueprint(upload_router)
