# Twitter Media Downloader

A web version based on [twitter_download](https://github.com/caolvchong-top/twitter_download), built with Flask + Vue3 + Element Plus.

[中文文档](README.md) | English

## Features

- Download all images and videos from a Twitter user with one click
- Real-time download progress display
- Auto-packaging into ZIP files after download (categorized by video/image/other)
- Asynchronous download support, non-blocking UI
- Modern Element Plus frontend interface
- Dark mode support
- Configuration management - persistent storage for proxy, Cookie, etc.
- Download history - view and manage previous download records
- Cache cleanup - one-click cache and history clearing
- Docker deployment support

## Tech Stack

| Category | Technology |
|----------|------------|
| Backend | Python 3.12 + Flask |
| Frontend | Vue3 + Element Plus |
| Database | SQLite |
| HTTP Client | httpx |
| Containerization | Docker + Docker Compose |

## Project Structure

```
twitter_download_server/
├── app.py                 # Flask application factory
├── config.py              # Configuration file
├── database.py            # Database operations
├── models.py              # Data models
├── routes.py              # Route handlers
├── services.py            # Business logic
├── run.py                 # Startup script
├── requirements.txt       # Dependencies
├── Dockerfile             # Docker image config
├── docker-compose.yml     # Docker Compose config
├── .dockerignore          # Docker ignore file
├── README.md              # Project documentation
├── start.sh               # Linux/Mac startup script
├── start.bat              # Windows startup script
├── data.db                # SQLite database (auto-created)
├── downloader/            # Downloader module
│   ├── __init__.py
│   └── twitter_downloader.py
├── templates/             # HTML templates
│   ├── index.html         # Home page
│   ├── config.html        # Config page
│   └── history.html       # History page
└── static/                # Static files
    ├── favicon.svg        # Favicon
    ├── css/
    │   ├── common.css     # Common styles
    │   ├── home.css       # Home page styles
    │   ├── config.css     # Config page styles
    │   ├── history.css    # History page styles
    │   └── dark-mode.css  # Dark mode styles
    └── js/
        ├── app.js         # Main app script
        ├── components.js  # Global components
        ├── utils.js       # Utility functions
        └── theme.js       # Theme toggle script
```

## Deployment

### Option 1: Direct Run

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Start the service:**

Linux/Mac:
```bash
./start.sh
```

Windows:
```cmd
start.bat
```

Or run directly:
```bash
python run.py
```

**3. Access the service:**

Open browser and visit http://localhost:12345

---

### Option 2: Docker Deployment (Recommended)

#### Using Docker Compose

```bash
# Clone the project
git clone https://github.com/Kiliwwwww/twitter_media_downloader.git
cd twitter_media_downloader

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

#### Using Docker Commands

```bash
# Clone the project
git clone https://github.com/Kiliwwwww/twitter_media_downloader.git
cd twitter_media_downloader

# Build image
docker build -t twitter-downloader .

# Run container
docker run -d \
  -p 12345:12345 \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/data.db:/app/data.db \
  --name twitter-downloader \
  --restart unless-stopped \
  twitter-downloader

# View logs
docker logs -f twitter-downloader

# Stop container
docker stop twitter-downloader
```

#### Data Persistence

When deploying with Docker, the following data will be persisted to the host:

| Host Path | Container Path | Description |
|-----------|---------------|-------------|
| `./downloads` | `/app/downloads` | Downloaded media files |
| `./data.db` | `/app/data.db` | Configuration and history database |

---

## Pages

### Home (/)
- Enter Twitter username to start download
- Real-time download progress display
- Download ZIP package after completion

### Configuration (/config)
- Manage proxy settings
- Manage Twitter Cookie (auth_token and ct0)
- Configuration auto-persisted to SQLite database

### Download History (/history)
- View all download records
- Display download status, file count, etc.
- View detailed error messages for failed downloads
- Re-download completed tasks
- Delete history records
- Clear cache (also clears download history)

## Configuration

Configuration is stored in SQLite database `data.db`. Fill in the configuration page on first use:

| Config Item | Description |
|-------------|-------------|
| `proxy` | Proxy address, e.g., `http://127.0.0.1:7890` (optional) |
| `auth_token` | auth_token from Twitter Cookie |
| `ct0` | ct0 from Twitter Cookie |

### Getting Cookie

1. Log in to [twitter.com](https://twitter.com)
2. Open browser Developer Tools (F12)
3. Switch to Application/Storage tab
4. Find twitter.com in Cookies
5. Copy the values of `auth_token` and `ct0`

## FAQ

### Q: What to do if download fails?
A: Please check the following:
1. Cookie is valid and not expired
2. Proxy settings are correct
3. Network connection is working
4. Target user has a public account

### Q: How to update to the latest version?
A:
```bash
git pull origin main
# If using Docker
docker-compose down
docker-compose up -d --build
```

### Q: Where are downloaded files saved?
A: By default, saved in the `downloads` folder in the project directory, organized by username.

### Q: What media types are supported?
A: Supports downloading images (jpg, png, webp) and videos (mp4, mov) from Twitter.

## Notes

1. Valid Twitter Cookie is required for downloading
2. Download speed depends on network environment and proxy settings
3. Bulk downloads may trigger Twitter API rate limits
4. Please comply with Twitter's Terms of Service and applicable laws

## Contributing

Issues and Pull Requests are welcome!

## License

This project is based on [twitter_download](https://github.com/caolvchong-top/twitter_download). Thanks to the original author.

## Changelog

### v1.0.0 (2026-06-04)

**Features:**
- Download images/videos by Twitter user ID
- Batch download support for multiple users
- Real-time download progress (SSE push)
- Auto-packaging into ZIP after download (categorized by type)
- Export tweet data to xlsx files
- Configuration management - persistent storage for proxy, Cookie, etc.
- Multi-user support - independent configuration per user
- Download history - view and manage download records
- Cache cleanup - one-click cache and history clearing
- Real-time logging system
- Dark mode support
- Docker deployment support

**Fixes:**
- Fixed issue where history records with special characters in task_id could not be deleted
- Fixed progress not updating when skipping existing files
- Fixed configuration API leaking secret_key
- Fixed blurry avatar issue, using HD version

---

## Mirror Repositories

- GitHub: https://github.com/Kiliwwwww/twitter_media_downloader
- Gitee: https://gitee.com/kili233/twitter_download_server
