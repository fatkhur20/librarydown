# LibraryDown - Universal Social Media Downloader

<div align="center">

**Download konten dari berbagai platform media sosial dengan mudah dan cepat!**

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API Docs](docs/API.md) • [Roadmap](docs/ROADMAP.md)

</div>

---

## 📖 Tentang Project

**LibraryDown** adalah aplikasi API-based untuk mengunduh konten dari platform media sosial seperti TikTok, YouTube, Instagram, dan Twitter/X. Dibangun dengan arsitektur modern menggunakan **FastAPI** dan **Celery** untuk processing asynchronous yang efisien.

### Kenapa LibraryDown?

- ⚡ **Lightweight**: Tidak menggunakan headless browser, lebih cepat dan hemat resource
- 🔄 **Asynchronous**: Download processing menggunakan Celery task queue
- 📊 **Tracking**: Database tracking untuk history downloads
- 🛡️ **Secure**: Rate limiting dan CORS protection
- 🧹 **Auto-cleanup**: File otomatis dihapus setelah TTL expired
- 📱 **Multi-platform**: Support TikTok, YouTube, Instagram, Twitter/X
- 🤖 **Telegram Bot**: Download langsung lewat bot Telegram (NEW!)

---

## ✨ Features

### ✅ Sudah Tersedia

- **TikTok Downloader** (Fully Working)
  - Video dan carousel/slideshow images
  - Metadata lengkap (caption, stats, author info)
  - Music/audio extraction

- **YouTube Downloader** (Implemented)
  - Video dengan berbagai quality options
  - Metadata dan statistics

- **Telegram Bot Downloader** (NEW!) 🤖
  - Download langsung dari bot Telegram
  - Support semua platform yang didukung
  - Interface interaktif dengan command
  - Single-step download (tanpa perlu polling)
  - Direct file delivery to chat

- **REST API**
  - FastAPI dengan automatic Swagger documentation
  - Rate limiting (10 req/min default)
  - CORS middleware

- **Task Management**
  - Asynchronous processing dengan Celery
  - Auto-retry dengan exponential backoff
  - Progress tracking

- **File Management**
  - Auto-cleanup dengan configurable TTL
  - Scheduled cleanup task (Celery Beat)

---

## 🚀 Installation

### Prerequisites

- Python 3.13+
- Redis server
- Git
- FFmpeg (for media processing)

### Quick Start

1. **Clone repository**

```bash
git clone <repository-url>
cd librarydown
```

2. **Run setup script**

```bash
# Traditional setup
chmod +x scripts/setup/setup.sh
./scripts/setup/setup.sh

# Or use the comprehensive management system
chmod +x scripts/utils/master-manager.sh
./scripts/utils/master-manager.sh setup
```

The traditional setup script will automatically:
- Create virtual environment
- Install dependencies
- Setup Redis (if not available)
- Copy .env.example to .env
- Create media folder

The new management system provides additional features:
- Auto-configure Telegram bot for cookie management
- Start all services with monitoring
- Environment auto-detection (systemd vs Termux)
- Comprehensive service management

3. **Activate virtual environment**

```bash
source venv/bin/activate
```

4. **Configure environment variables** (optional)

Edit `.env` sesuai kebutuhan:

```bash
nano .env
```

### Telegram Bot Configuration (NEW!)

To use the Telegram bot downloader:

1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
2. Get the bot token
3. Update your `.env` file:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_USER_ID=your_telegram_user_id
```

4. Start the bot:

```bash
./scripts/utils/start_bot.sh
```

---

## 💻 Usage

### Starting the Services

LibraryDown memerlukan 3 services yang berjalan bersamaan:

#### 1. Redis Server

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running, start it:
redis-server
```

#### 2. Celery Worker

Terminal baru:

```bash
source venv/bin/activate
celery -A src.workers.celery_app worker --loglevel=info
```

#### 3. Celery Beat (untuk scheduled cleanup)

Terminal baru:

```bash
source venv/bin/activate
celery -A src.workers.celery_app beat --loglevel=info
```

#### 4. FastAPI Server

Terminal baru:

```bash
source venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Telegram Bot Usage (NEW!) 🤖

After configuring and starting the bot:

#### Commands:
- `/start` - Welcome message and basic info
- `/help` - Detailed help information
- `/download` - Download a video (followed by URL)
- `/status` - Check bot status

#### Direct Usage:
Just send a video URL directly to the bot, and it will automatically download and send the video back to you!

#### Example:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

The bot will:
1. Recognize the platform (YouTube)
2. Start the download
3. Send the video file directly to your chat

### Menggunakan API

Setelah semua services running, API akan tersedia di:

- **API Base**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Example: Download TikTok Video

```bash
# Submit download task (async)
curl -X POST http://localhost:8000/api/v1/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://vt.tiktok.com/ZS593uwQc/"}'

# Response:
# {
#   "task_id": "abc123...",
#   "status": "queued",
#   "platform": "tiktok"
# }

# Check status
curl http://localhost:8000/api/v1/status/abc123...

# When status is SUCCESS, download URL akan tersedia di response
```

#### Example: Direct Download (NEW!)

```bash
# One-step download (sync) - returns the file directly
curl -O "http://localhost:8000/api/v1/download-sync?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=720p"

# For audio only:
curl -O "http://localhost:8000/api/v1/download-sync?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=audio"
```

Untuk dokumentasi API lengkap, lihat [API Documentation](docs/api/).

---

## 📁 Project Structure

Detailed project structure can be found in [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

```
librarydown/
├── README.md
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── src/
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── engine/
│   │   └── platforms/
│   ├── utils/
│   └── workers/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── docs/
│   ├── api/
│   ├── guides/
│   ├── security/
│   └── development/
├── scripts/
│   ├── setup/
│   ├── deploy/
│   ├── systemd/
│   ├── security/
│   └── utils/
├── data/
│   ├── db/
│   ├── logs/
│   └── temp/
├── media/
├── cookies/
└── venv/
```

---

## 🤖 Telegram Bot Features (NEW!)

### Bot Commands:
- `/start` - Welcome message and basic usage info
- `/help` - Detailed help with supported platforms
- `/download <URL>` - Download a specific video
- `/status` - Check bot status and statistics

### Direct Usage:
Simply send any supported video URL to the bot, and it will automatically:
1. Detect the platform
2. Start the download process
3. Send the video file directly to your chat

### Supported Platforms:
All platforms supported by the API are also available through the bot:
- YouTube, TikTok, Instagram, SoundCloud
- Dailymotion, Twitch, Reddit, Vimeo
- Facebook, Bilibili, LinkedIn, Pinterest

---

## ⚙️ Configuration

Semua konfigurasi ada di file `.env`:

### Application Settings

```bash
APP_NAME="Universal Social Media Downloader"
VERSION="2.0.0"
DEBUG=True                          # Set False for production
API_V1_STR="/api/v1"
API_BASE_URL="http://localhost:8000"
```

### Security

```bash
ALLOWED_ORIGINS=["*"]               # Specify domains for production
RATE_LIMIT_PER_MINUTE=10           # API rate limit per IP
```

### File Management

```bash
MEDIA_FOLDER=media
FILE_TTL_HOURS=24                   # Auto-delete after 24 hours
MAX_FILE_SIZE_MB=500               # Max download size
```

### Task Settings

```bash
MAX_RETRIES=3                       # Retry attempts for failed tasks
RETRY_BACKOFF=5                    # Exponential backoff base (seconds)
```

### Telegram Bot Settings (NEW!)

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here    # Get from @BotFather
TELEGRAM_USER_ID=your_user_id_here        # Your Telegram user ID
```

---

## 🛠️ Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run unit tests
pytest tests/unit/
```

### Running All Tests

```bash
# Run integration tests
pytest tests/integration/

# Run end-to-end tests
pytest tests/e2e/

# Run all tests
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint
flake8 src/

# Type check
mypy src/
```

---

## 📊 Monitoring & Logs

### Celery Monitoring

Monitor Celery tasks menggunakan Flower:

```bash
pip install flower
celery -A src.workers.celery_app flower
```

Access di: http://localhost:5555

### Logs

Logs menggunakan **loguru**. Check console output dari:
- FastAPI server (API requests)
- Celery worker (task execution)
- Celery beat (scheduled tasks)
- Telegram bot (NEW!)

---

## 🔒 Security Notes

⚠️ **Important untuk Production**:

1. **Disable DEBUG mode**: Set `DEBUG=False` di `.env`
2. **Configure CORS**: Update `ALLOWED_ORIGINS` dengan domain specific
3. **Use HTTPS**: Setup reverse proxy (nginx) dengan SSL
4. **Rate Limiting**: Adjust rate limit sesuai kebutuhan
5. **Database**: Backup database secara regular
6. **Redis**: Secure Redis dengan password jika exposed
7. **Firewall**: Restrict access ke Redis port (6379)

---

## 🤝 Contributing

Contributions are welcome! Silakan:

1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

Project ini menggunakan MIT License. Lihat `LICENSE` file untuk details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Celery](https://docs.celeryq.dev/) - Distributed task queue
- [httpx](https://www.python-httpx.org/) - Async HTTP client
- [loguru](https://github.com/Delgan/loguru) - Simplified logging
- [python-telegram-bot](https://python-telegram-bot.org/) - Telegram bot framework

---

## 📞 Support

Jika ada pertanyaan atau issues:

- 📧 Email: [your-email@example.com]
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/librarydown/issues)
- 📖 Documentation: [Full Documentation](docs/)

---

<div align="center">

**Made with ❤️ for the developer community**

</div>