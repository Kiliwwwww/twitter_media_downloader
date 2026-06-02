import os
import secrets
from flask import Flask

from config import Config
from routes import main_bp
from routes_auth import auth_bp
from routes_profile import profile_bp
from routes_admin import admin_bp
import database


def get_or_create_secret_key() -> str:
    """获取或创建持久化的secret_key"""
    database.init_db()
    key = database.get_config('secret_key')
    if not key:
        key = secrets.token_hex(32)
        # 使用 INSERT OR IGNORE 确保不会重复插入
        with database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO config (key, value, description)
                VALUES (?, ?, ?)
            ''', ('secret_key', key, 'Flask session密钥（自动生成）'))
        # 如果已存在则更新
        if not database.get_config('secret_key'):
            database.update_config('secret_key', key)
    return key


def create_app() -> Flask:
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 配置应用
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config['DOWNLOAD_FOLDER'] = Config.DOWNLOAD_FOLDER
    
    # Session配置 - 使用持久化的secret_key
    app.secret_key = get_or_create_secret_key()
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30天
    
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