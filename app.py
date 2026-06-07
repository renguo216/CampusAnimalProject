import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, send_from_directory, send_from_directory as static_send
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)
    
    UPLOAD_FOLDER = 'uploads'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(UPLOAD_FOLDER, filename)
    
    # Admin 后台静态文件服务
    @app.route('/admin')
    def admin_index():
        return send_from_directory('admin', 'index.html')
    
    @app.route('/admin/<path:filename>')
    def admin_static(filename):
        return send_from_directory('admin', filename)

    @app.route('/')
    def index():
        return jsonify({
            "status": "ok",
            "service": "Campus Animal Project API",
            "version": "1.0.0",
            "endpoints": [
                "/api/v1/community/posts",
                "/api/v1/user/<user_id>",
                "/api/v1/animals/search",
                "/api/v1/donation/pay",
                "/api/v1/user/follow/<user_id>",
                "/api/v1/community/posts/<post_id>/like",
                "/api/v1/community/posts/<post_id>/comment",
                "/api/v1/notices",
                "/api/v1/reimbursement/apply",
                "/api/v1/rescue/records",
                "/api/v1/volunteer/apply",
                "/api/v1/adoption/apply",
                "/api/v1/donation/projects",
                "/api/v1/points/exchange",
                "/api/v1/points/products"
            ]
        })

    app.url_map.strict_slashes = False
    from backend.api import register_all_blueprints
    register_all_blueprints(app, url_prefix='/api/v1')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
