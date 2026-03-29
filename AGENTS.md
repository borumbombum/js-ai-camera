# AI Camera Project

Real-time object detection camera system with Telegram notifications.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Webcam        │────▶│  Python Server  │────▶│   Telegram   │
│   (OpenCV)      │     │  (FastAPI)      │     │   Bot        │
└─────────────────┘     └────────┬────────┘     └──────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
              ┌──────────┐  ┌──────────┐  ┌──────────────┐
              │ MJPEG    │  │ WebSocket│  │ Screenshot   │
              │ Stream   │  │ (objects)│  │ on detection  │
              └────┬─────┘  └────┬─────┘  └──────────────┘
                   │             │
                   ▼             ▼
            ┌─────────────────────────┐
            │    /stream page        │
            │  (video + detections)  │
            └─────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Detection | YOLOv8 (ultralytics) |
| Web Server | FastAPI + Uvicorn |
| Stream | MJPEG |
| Real-time | WebSocket |
| Notifications | python-telegram-bot |
| Client-side | TensorFlow.js (COCO-SSD) |

## Running the Project

### Prerequisites

- Node.js (for static file server)
- Python 3.12+ with uv
- Webcam/USB camera

### Setup

```bash
# Install Node dependencies
npm install

# Install Python dependencies
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

### Running Servers

```bash
# Static site (client-side TensorFlow.js detection)
npm run start
# → http://localhost:4421

# Python server (server-side YOLOv8 detection)
npm run server
# → http://localhost:4422/stream
```

### Access via Tailscale

Replace `<tailscale-ip>` with your machine's Tailscale IP:

| Service | URL |
|---------|-----|
| Static site | http://<tailscale-ip>:4421 |
| Live detection UI | http://<tailscale-ip>:4422/stream |
| MJPEG stream | http://<tailscale-ip>:4422/video_feed |
| API root | http://<tailscale-ip>:4422 |

## Telegram Bot Setup

1. Start the server: `npm run server`
2. Send `/start` to @jsaicamerabot
3. Person detections will trigger notifications with screenshots

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | (embedded) | Telegram bot token |
| `DETECTION_COOLDOWN` | 30 | Seconds between Telegram notifications |

## Project Structure

```
├── index.html              # Client-side TensorFlow.js detection
├── package.json            # npm scripts
├── requirements.txt        # Python dependencies
├── AGENTS.md               # This file
├── server/
│   ├── detector.py         # YOLOv8 detection logic
│   ├── telegram_bot.py     # Telegram notifications
│   ├── stream_server.py     # FastAPI server
│   └── templates/
│       └── stream.html     # Live detection web UI
└── .venv/                  # Python virtual environment
```

## Key Files

| File | Purpose |
|------|---------|
| `server/detector.py` | YOLOv8 model loading, detection, bounding box drawing |
| `server/stream_server.py` | Camera capture, FastAPI routes, detection loop |
| `server/telegram_bot.py` | Async Telegram bot with notification sending |
| `server/templates/stream.html` | Web UI with MJPEG player + object list |

## Notes

- First run downloads YOLOv8n model (~6MB)
- MJPEG stream includes drawn bounding boxes (server-side)
- WebSocket broadcasts detection list in real-time
- Cooldown prevents Telegram spam (default: 30s between notifications)
