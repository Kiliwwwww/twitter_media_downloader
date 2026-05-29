from flask import Flask

from config import Config
from routes import main_bp


def create_app() -> Flask:
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 配置应用
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config['DOWNLOAD_FOLDER'] = Config.DOWNLOAD_FOLDER
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    
    return app


app = create_app()

if __name__ == '__main__':
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )