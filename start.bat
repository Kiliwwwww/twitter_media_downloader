@echo off
chcp 65001 >nul

echo ==========================================
echo 推特媒体下载器 - 启动脚本
echo ==========================================

REM 检查Python版本
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python3
    pause
    exit /b 1
)

REM 检查Python依赖
echo 检查Python依赖...
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装Flask...
    pip install flask
)

python -c "import httpx" >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装httpx...
    pip install httpx
)

REM 检查Node.js和npm
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到npm，请先安装npm
    pause
    exit /b 1
)

REM 检查Vue3项目依赖
echo 检查Vue3项目依赖...
if not exist vue\node_modules (
    echo 安装Vue3项目依赖...
    cd vue
    npm install
    cd ..
)

REM 创建下载目录
if not exist downloads mkdir downloads

echo ==========================================
echo 启动推特媒体下载器...
echo 后端地址: http://localhost:12345
echo 前端地址: http://localhost:5173
echo 按 Ctrl+C 停止服务器
echo ==========================================

REM 启动Vue3开发服务器（后台）
echo 启动Vue3前端开发服务器...
cd vue
start "" /B npm run dev
cd ..
REM 等待Vue3服务器启动
timeout /t 2 /nobreak >nul

REM 启动Flask应用
echo 启动推特媒体下载器后端...
python run.py
pause