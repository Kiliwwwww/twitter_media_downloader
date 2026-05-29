#!/usr/bin/env python3
"""
推特媒体下载器 - 启动脚本
"""

import os
from app import app
from config import Config


def main():
    """启动Flask应用"""
    print("=" * 50)
    print("推特媒体下载器")
    print("=" * 50)
    print(f"访问地址: http://localhost:{Config.PORT}")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    # 确保下载目录存在
    os.makedirs(Config.DOWNLOAD_FOLDER, exist_ok=True)
    
    # 启动Flask应用
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT,
        threaded=True
    )


if __name__ == '__main__':
    main()