# AI Camera - Real-time Object Detection

Real-time webcam object detection with optional Telegram notifications when people are detected.

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
# - MJPEG stream:   http://localhost:4422/video_feed

# 4. Setup Telegram bot
# Send /start to @jsaicamerabot
```

## Features

- Real-time object detection using YOLOv8 (server) or COCO-SSD (client)
- Live video stream with bounding boxes
- Real-time object list with confidence scores
- Telegram notifications when a person is detected

## Architecture

See [AGENTS.md](AGENTS.md) for full documentation.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | (embedded) | Telegram bot token |
| `DETECTION_COOLDOWN` | 30 | Seconds between notifications |
