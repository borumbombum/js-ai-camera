# AI Camera - Real-time Object Detection

Real-time webcam object detection with Telegram notifications and timelapse recording.

## Quick Start

### Option 1: Client-side (No Python required)

```bash
npm install
npm run start
# Open http://localhost:4421
```

### Option 2: Server-side (Full Setup with Telegram)

```bash
# 1. Install dependencies
npm install
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 2. Start server
npm run server

# 3. Open in browser
# - Live detection: http://localhost:4422/stream
# - Timelapse viewer: http://localhost:4422/timelapse
# - MJPEG stream: http://localhost:4422/video_feed

# 4. Setup Telegram bot
# Send /start to @jsaicamerabot
```

## Features

- Real-time object detection using YOLOv8 (server) or COCO-SSD (client)
- Live video stream with bounding boxes and confidence scores
- Telegram notifications when a person or animal is detected
- Timelapse recording with configurable retention (default: 24 hours)
- Timelapse viewer with day-wide navigation and hour jump
- Event history with manual deletion option
- Alert thumbnails highlight detection events in timelapse

### Supported Animals

Detection for: dog, cat, bird, horse, sheep, cow, chicken, pig, rabbit

## Architecture

See [AGENTS.md](AGENTS.md) for full documentation.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | (required) | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | (required) | Your Telegram chat ID |
| `DETECTION_COOLDOWN` | 30 | Seconds between person notifications |
| `PERSON_CONFIDENCE_THRESHOLD` | 0.51 | Min confidence for person detection |
| `ANIMAL_CONFIDENCE_THRESHOLD` | 0.51 | Min confidence for animal detection |
| `ANIMAL_COOLDOWN` | 30 | Seconds between animal notifications |
| `SERVER_BASE_URL` | http://localhost:4422 | Public URL for Telegram links |
| `TIMELAPSE_RETENTION_HOURS` | 24 | Hours to keep timelapse images |

Copy `.env.example` to `.env` and configure as needed.
