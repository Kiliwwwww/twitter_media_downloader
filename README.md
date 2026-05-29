# 推特媒体下载器

基于 [twitter_download](https://github.com/caolvchong-top/twitter_download) 项目实现的Web版本，使用Flask + Vue3 构建。

## 功能特性

- 🎯 输入推特用户ID，一键下载该用户的所有图文视频
- 📊 实时显示下载进度
- 📦 下载完成后自动打包为ZIP文件
- 🔄 支持异步下载，不阻塞界面
- 🎨 现代化的Vue3前端界面

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行项目

```bash
python run.py
```

或者直接运行：

```bash
python app.py
```

访问 http://localhost:5000 即可使用。

## 使用说明

1. 在输入框中输入推特用户名（@后面的字符）
2. 点击"开始下载"按钮
3. 等待下载完成，期间可以看到下载进度
4. 下载完成后点击"下载压缩包"按钮保存文件

## 配置说明

### 代理配置

默认使用代理 `http://127.0.0.1:7890`，如需修改，请编辑 `app.py` 文件中的代理配置。

### Cookie配置

默认使用预设的Cookie，如需修改，请编辑 `app.py` 文件中的Cookie配置。

## 项目结构

```
twitter_download_server/
├── app.py                 # Flask主应用
├── run.py                 # 启动脚本
├── requirements.txt       # 依赖列表
├── README.md             # 项目说明
├── test_app.py           # 测试文件
├── downloader/           # 下载器模块
│   ├── __init__.py
│   └── twitter_downloader.py
├── templates/            # HTML模板
│   └── index.html
├── static/              # 静态文件
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── downloads/           # 下载文件目录（自动创建）
```

## 注意事项

1. 需要有效的推特Cookie才能下载
2. 下载速度取决于网络环境和代理设置
3. 大量下载可能会触发推特API限制
4. 请遵守推特的使用条款和相关法律法规

## 原项目参考

本项目基于 [twitter_download](https://github.com/caolvchong-top/twitter_download) 项目实现，感谢原作者的贡献。