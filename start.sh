#!/bin/bash

echo "=========================================="
echo "推特媒体下载器 - 启动脚本"
echo "=========================================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $? -ne 0 ]]; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi
echo "Python版本: $python_version"

# 检查依赖
echo "检查依赖..."
python3 -c "import flask" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo "安装Flask..."
    pip3 install flask
fi

python3 -c "import httpx" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo "安装httpx..."
    pip3 install httpx
fi

# 创建下载目录
mkdir -p downloads

echo "=========================================="
echo "启动推特媒体下载器..."
echo "访问地址: http://localhost:12345"
echo "按 Ctrl+C 停止服务器"
echo "=========================================="

# 启动Flask应用
python3 run.py