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

# 检查Node.js和npm
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到Node.js，请先安装Node.js${NC}"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo -e "${RED}错误: 未找到npm，请先安装npm${NC}"
    exit 1
fi

# 检查并安装Python依赖
echo -e "${YELLOW}检查Python依赖...${NC}"
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

# 检查Vue3项目依赖
echo -e "${YELLOW}检查Vue3项目依赖...${NC}"
if [ ! -d "vue/node_modules" ]; then
    echo -e "${YELLOW}安装Vue3项目依赖...${NC}"
    (cd vue && npm install)
fi

# 定义清理函数
cleanup() {
    echo -e "\n${YELLOW}正在停止服务...${NC}"
    # 杀死Vue3开发服务器
    if kill -0 $VUE_PID 2>/dev/null; then
        kill $VUE_PID 2>/dev/null
    fi
    # 杀死Flask应用
    if kill -0 $PYTHON_PID 2>/dev/null; then
        kill $PYTHON_PID 2>/dev/null
    fi
    # 等待进程退出
    wait $VUE_PID $PYTHON_PID 2>/dev/null
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# 启动Vue3开发服务器（后台）
echo -e "${GREEN}启动Vue3前端开发服务器...${NC}"
(cd vue && npm run dev) &
VUE_PID=$!

# 等待Vue3服务器启动
sleep 2

# 启动Flask应用（后台）
echo -e "${GREEN}启动推特媒体下载器后端...${NC}"
python3 run.py &
PYTHON_PID=$!

# 等待任一进程退出
while kill -0 $VUE_PID 2>/dev/null && kill -0 $PYTHON_PID 2>/dev/null; do
    sleep 1
done

# 清理
cleanup