import os


class Config:
    """应用配置"""
    
    # 基础路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 下载目录
    DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')
    
    # Flask配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 12345
    
    @classmethod
    def get_proxy(cls, user_id: int = None) -> str:
        """获取代理配置（从数据库）"""
        from database import get_config
        return get_config('proxy', user_id) or 'http://127.0.0.1:7890'
    
    @classmethod
    def get_cookie(cls, user_id: int = None) -> str:
        """获取Cookie配置（从数据库拼接）"""
        from database import get_config
        auth_token = get_config('auth_token', user_id) or ''
        ct0 = get_config('ct0', user_id) or ''
        if auth_token and ct0:
            return f'auth_token={auth_token}; ct0={ct0};'
        return ''