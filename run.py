#!/usr/bin/env python3
"""
推特媒体下载器 - 启动脚本
"""

import os
import sys
from app import app

def main():
    """启动Flask应用"""
    print("=" * 50)
    print("推特媒体下载器")
    print("=" * 50)
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    # 确保下载目录存在
    download_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
    os.makedirs(download_folder, exist_ok=True)
    
    # 启动Flask应用
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )

if __name__ == '__main__':
    main()