#!/bin/bash

# 推特媒体下载器 - 启动脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3，请先安装Python3${NC}"
    exit 1
fi

# 检查并安装依赖
echo -e "${YELLOW}检查依赖...${NC}"
python3 -c "import flask" 2>/dev/null || {
    echo -e "${YELLOW}安装Flask...${NC}"
    pip3 install flask -q
}
python3 -c "import httpx" 2>/dev/null || {
    echo -e "${YELLOW}安装httpx...${NC}"
    pip3 install httpx -q
}

# 创建下载目录
mkdir -p downloads

# 启动Flask应用
echo -e "${GREEN}启动推特媒体下载器...${NC}"
python3 run.py