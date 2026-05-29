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

REM 检查依赖
echo 检查依赖...
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

REM 创建下载目录
if not exist downloads mkdir downloads

echo ==========================================
echo 启动推特媒体下载器...
echo 访问地址: http://localhost:12345
echo 按 Ctrl+C 停止服务器
echo ==========================================

REM 启动Flask应用
python run.py
pause