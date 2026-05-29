# 推特媒体下载器

基于 [twitter_download](https://github.com/caolvchong-top/twitter_download) 项目实现的Web版本，使用Flask + Vue3 + Element Plus 构建。

## 功能特性

- 🎯 输入推特用户ID，一键下载该用户的所有图文视频
- 📊 实时显示下载进度
- 📦 下载完成后自动打包为ZIP文件
- 🔄 支持异步下载，不阻塞界面
- 🎨 现代化的Element Plus前端界面
- ⚙️ 配置管理 - 支持代理、Cookie等配置的持久化存储
- 📜 下载历史 - 查看和管理之前的下载记录

## 项目结构

```
twitter_download_server/
├── app.py                 # Flask应用工厂
├── config.py              # 配置文件
├── database.py            # 数据库操作
├── models.py              # 数据模型
├── routes.py              # 路由处理
├── services.py            # 业务逻辑
├── run.py                 # 启动脚本
├── requirements.txt       # 依赖列表
├── Dockerfile             # Docker镜像配置
├── docker-compose.yml     # Docker Compose配置
├── README.md              # 项目说明
├── start.sh               # Linux/Mac启动脚本
├── start.bat              # Windows启动脚本
├── data.db                # SQLite数据库（自动创建）
├── downloader/            # 下载器模块
│   ├── __init__.py
│   └── twitter_downloader.py
├── templates/             # HTML模板
│   ├── index.html         # 首页
│   ├── config.html        # 配置管理页
│   └── history.html       # 下载历史页
└── static/                # 静态文件
    └── js/
        └── app.js
```

## 运行项目

### 方式一：直接运行

**安装依赖：**
```bash
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

**或直接运行:**
```bash
python run.py
```

### 方式二：Docker 运行

**使用 Docker Compose（推荐）：**
```bash
docker-compose up -d
```

**或使用 Docker 命令：**
```bash
# 构建镜像
docker build -t twitter-downloader .

# 运行容器
docker run -d \
  -p 12345:12345 \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/data.db:/app/data.db \
  --name twitter-downloader \
  twitter-downloader
```

访问 http://localhost:12345 即可使用。

## 页面说明

### 首页
- 输入推特用户名开始下载
- 实时显示下载进度
- 下载完成后可下载ZIP压缩包

### 配置管理 (/config)
- 管理代理地址配置
- 管理推特Cookie配置
- 配置自动持久化到SQLite数据库

### 下载历史 (/history)
- 查看所有下载记录
- 显示下载状态、文件数量等信息
- 支持重新下载已完成的任务
- 支持删除历史记录

## 配置说明

配置存储在SQLite数据库 `data.db` 中，可通过配置管理页面进行修改：

- `proxy`: 代理地址（默认: http://127.0.0.1:7890）
- `cookie`: 推特Cookie（需要包含auth_token和ct0）

## 注意事项

1. 需要有效的推特Cookie才能下载
2. 下载速度取决于网络环境和代理设置
3. 大量下载可能会触发推特API限制
4. 请遵守推特的使用条款和相关法律法规

## 原项目参考

本项目基于 [twitter_download](https://github.com/caolvchong-top/twitter_download) 项目实现，感谢原作者的贡献。