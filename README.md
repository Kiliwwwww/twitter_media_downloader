# 推特媒体下载器

中文 | [English](README_EN.md)

基于 [twitter_download](https://github.com/caolvchong-top/twitter_download) 项目实现的Web版本，使用 Flask + Vue3 + Element Plus 构建。

## 功能特性

- 🎯 输入推特用户ID，一键下载该用户的所有图文视频
- 📊 实时显示下载进度
- 📦 下载完成后自动打包为ZIP文件（按视频/图片/其他分类）
- 🔄 支持异步下载，不阻塞界面
- 🎨 现代化的 Element Plus 前端界面
- 🌙 支持暗黑模式，保护眼睛
- ⚙️ 配置管理 - 支持代理、Cookie等配置的持久化存储
- 📜 下载历史 - 查看和管理之前的下载记录
- 🧹 缓存清理 - 一键清理缓存文件和下载历史
- 🐳 支持 Docker 部署

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端 | Python 3.12 + Flask |
| 前端 | Vue3 + Element Plus |
| 数据库 | SQLite |
| HTTP客户端 | httpx |
| 容器化 | Docker + Docker Compose |

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
├── .dockerignore          # Docker忽略文件
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
    ├── favicon.svg        # 网站标签页图标
    ├── css/
    │   ├── common.css     # 公共基础样式
    │   ├── home.css       # 首页样式
    │   ├── config.css     # 配置页样式
    │   ├── history.css    # 历史页样式
    │   └── dark-mode.css  # 暗黑模式样式
    └── js/
        ├── app.js         # 主应用脚本
        ├── components.js  # 全局组件
        ├── utils.js       # 工具函数
        └── theme.js       # 主题切换脚本
```

## 部署方式

### 方式一：直接运行

**1. 安装依赖：**
```bash
pip install -r requirements.txt
```

**2. 启动服务：**

Linux/Mac:
```bash
./start.sh
```

Windows:
```cmd
start.bat
```

或直接运行:
```bash
python run.py
```

**3. 访问服务：**

打开浏览器访问 http://localhost:12345

---

### 方式二：Docker 部署（推荐）

#### 使用 Docker Compose

```bash
# 克隆项目
git clone https://github.com/Kiliwwwww/twitter_media_downloader.git
cd twitter_media_downloader

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 使用 Docker 命令

```bash
# 克隆项目
git clone https://github.com/Kiliwwwww/twitter_media_downloader.git
cd twitter_media_downloader

# 构建镜像
docker build -t twitter-downloader .

# 运行容器
docker run -d \
  -p 12345:12345 \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/data.db:/app/data.db \
  --name twitter-downloader \
  --restart unless-stopped \
  twitter-downloader

# 查看日志
docker logs -f twitter-downloader

# 停止容器
docker stop twitter-downloader
```

#### 数据持久化

Docker部署时，以下数据会持久化到宿主机：

| 宿主机路径 | 容器路径 | 说明 |
|-----------|---------|------|
| `./downloads` | `/app/downloads` | 下载的媒体文件 |
| `./data.db` | `/app/data.db` | 配置和历史记录数据库 |

#### 国内网络优化

Dockerfile 已配置使用阿里云 pip 镜像源，国内网络可直接构建。

如果 Docker 拉取基础镜像慢，可配置 Docker 镜像加速器：

```json
// /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://registry.docker-cn.com"
  ]
}
```

配置后重启 Docker：
```bash
sudo systemctl restart docker
```

---

## 默认账号

系统首次启动时会自动创建默认超管账号：

| 项目 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `123456` |

> ⚠️ 请在首次登录后及时修改默认密码！

---

## 页面说明

### 首页 (/)
- 输入推特用户名开始下载
- 实时显示下载进度
- 下载完成后可下载ZIP压缩包

### 配置管理 (/config)
- 管理代理地址配置
- 管理推特Cookie（auth_token和ct0）
- 配置自动持久化到SQLite数据库

### 下载历史 (/history)
- 查看所有下载记录
- 显示下载状态、文件数量等信息
- 失败时可查看详细错误信息
- 支持重新下载已完成的任务
- 支持删除历史记录
- 支持清理缓存（同时清空下载历史）

## 配置说明

配置存储在SQLite数据库 `data.db` 中，首次使用需在配置页面填写：

| 配置项 | 说明 |
|-------|------|
| `proxy` | 代理地址，如 `http://127.0.0.1:7890`（可选） |
| `auth_token` | Twitter Cookie中的auth_token |
| `ct0` | Twitter Cookie中的ct0 |

### 获取 Cookie

1. 登录 [twitter.com](https://twitter.com)
2. 打开浏览器开发者工具 (F12)
3. 切换到 Application/存储 标签
4. 在 Cookies 中找到 twitter.com
5. 分别复制 `auth_token` 和 `ct0` 的值

## 常见问题

### Q: 下载失败怎么办？
A: 请检查以下几点：
1. Cookie 是否有效且未过期
2. 代理设置是否正确
3. 网络连接是否正常
4. 目标用户是否为公开账号

### Q: 如何更新到最新版本？
A: 
```bash
git pull origin main
# 如果使用 Docker
docker-compose down
docker-compose up -d --build
```

### Q: 下载的文件保存在哪里？
A: 默认保存在项目目录下的 `downloads` 文件夹中，按用户名分目录存放。

### Q: 支持下载哪些类型的媒体？
A: 支持下载推特上的图片（jpg、png、webp）和视频（mp4、mov）。

## 注意事项

1. 需要有效的推特Cookie才能下载
2. 下载速度取决于网络环境和代理设置
3. 大量下载可能会触发推特API限制
4. 请遵守推特的使用条款和相关法律法规

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目基于 [twitter_download](https://github.com/caolvchong-top/twitter_download) 项目实现，感谢原作者的贡献。

## 更新日志

### v1.0.0 (2026-06-04)

**功能特性：**
- 支持输入推特用户ID下载图文视频
- 支持批量下载多个用户媒体
- 实时显示下载进度（SSE推送）
- 下载完成后自动打包ZIP（按视频/图片/其他分类）
- 支持导出推文数据为xlsx文件
- 配置管理 - 代理、Cookie等配置持久化存储
- 多用户支持 - 每个用户独立配置
- 下载历史 - 查看和管理下载记录
- 缓存清理 - 一键清理缓存和历史
- 实时日志系统
- 暗黑模式支持
- Docker部署支持

**修复：**
- 修复task_id包含特殊字符时无法删除历史记录的问题
- 修复跳过已存在文件时进度不更新的问题
- 修复配置API泄露secret_key的问题
- 修复头像模糊问题，使用高清版本

---

## 镜像仓库

- GitHub: https://github.com/Kiliwwwww/twitter_media_downloader
- Gitee: https://gitee.com/kili233/twitter_download_server
