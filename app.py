import os
import secrets
from flask import Flask

from config import Config
from routes import main_bp
from routes_auth import auth_bp
from routes_profile import profile_bp
from routes_admin import admin_bp
import database


def create_app() -> Flask:
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 配置应用
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config['DOWNLOAD_FOLDER'] = Config.DOWNLOAD_FOLDER
    
    # Session配置
    app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30天
    
    # 初始化数据库
    database.init_db()
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    
    return app


app = create_app()

if __name__ == '__main__':
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )