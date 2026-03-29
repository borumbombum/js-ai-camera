# AI Camera Project

Real-time object detection camera system with Telegram notifications and timelapse recording.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Webcam        │────▶│  Python Server  │────▶│   Telegram   │
│   (OpenCV)      │     │  (FastAPI)      │     │   Bot        │
└─────────────────┘     └────────┬────────┘     └──────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
   ┌──────────┐            ┌──────────┐            ┌──────────────┐
   │ MJPEG    │            │ WebSocket│            │ Timelapse   │
   │ Stream   │            │ (objects)│            │ Recording   │
   └────┬─────┘            └────┬─────┘            └──────┬───────┘
        │                        │                        │
        ▼                        ▼                        ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                      Web UI                                 │
   │  /stream (Live Camera)  |  /timelapse (Timelapse Viewer)   │
   └─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Detection | YOLOv8 (ultralytics) |
| Web Server | FastAPI + Uvicorn |
| Stream | MJPEG |
| Real-time | WebSocket |
| Notifications | python-telegram-bot |
| Database | SQLite |
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
| Timelapse Viewer | http://<tailscale-ip>:4422/timelapse |
| MJPEG stream | http://<tailscale-ip>:4422/video_feed |
| API root | http://<tailscale-ip>:4422 |

## Telegram Bot Setup

1. Start the server: `npm run server`
2. Send `/start` to @jsaicamerabot
3. Person/Animal detections will trigger notifications with screenshots

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | (required) | Telegram bot token |
| `TELEGRAM_CHAT_ID` | (required) | Your Telegram chat ID |
| `DETECTION_COOLDOWN` | 30 | Seconds between person notifications |
| `PERSON_CONFIDENCE_THRESHOLD` | 0.51 | Min confidence for person detection |
| `ANIMAL_CONFIDENCE_THRESHOLD` | 0.51 | Min confidence for animal detection |
| `ANIMAL_COOLDOWN` | 30 | Seconds between animal notifications |
| `SERVER_BASE_URL` | http://localhost:4422 | Public URL for Telegram links |
| `TIMELAPSE_RETENTION_HOURS` | 24 | Hours to keep timelapse images |

## Project Structure

```
├── index.html              # Client-side TensorFlow.js detection
├── package.json            # npm scripts
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration
├── AGENTS.md               # This file
├── README.md               # User documentation
├── server/
│   ├── detector.py         # YOLOv8 detection logic
│   ├── telegram_bot.py     # Telegram notifications
│   ├── stream_server.py    # FastAPI server
│   ├── timelapse.py        # Timelapse recording with cleanup
│   ├── events.db           # SQLite database for events
│   ├── recordings/         # Timelapse images (YYYY-MM-DD/HH/MM_SS.jpg)
│   └── templates/
│       ├── stream.html     # Live Camera web UI
│       └── timelapse.html  # Timelapse Viewer web UI
└── .venv/                  # Python virtual environment
```

## Key Files

| File | Purpose |
|------|---------|
| `server/detector.py` | YOLOv8 model loading, detection, bounding box drawing |
| `server/stream_server.py` | Camera capture, FastAPI routes, detection loop |
| `server/telegram_bot.py` | Async Telegram bot with notification sending |
| `server/timelapse.py` | Timelapse recording (every 2s) and hourly cleanup |
| `server/templates/stream.html` | Live Camera UI with MJPEG player + object list |
| `server/templates/timelapse.html` | Timelapse Viewer with day navigation + alerts |

## Timelapse System

### Recording
- Captures frame every 2 seconds
- Images stored as `recordings/YYYY-MM-DD/HH/MM_SS.jpg`
- Retention cleanup runs hourly (deletes date folders older than retention)

### Viewer
- Loads all images for selected date (not per-hour)
- Hour dropdown for quick navigation to specific hour
- Alert thumbnails highlight detection events with red ring
- Click thumbnails to navigate to specific image
- "Show All Images" toggle for full day view
- Click main image to see detection details modal

### Detection Screenshot Delay
- When detection triggers, waits 1 second before capturing screenshot
- This ensures the screenshot shows the actual object, not a frame from 2s earlier

## Event History

- Events stored in SQLite database with timestamps and detection details
- Events are kept forever (no automatic deletion)
- Manual deletion via the Event History drawer
- Events link to timelapse with exact timestamp when screenshot exists
- Events without screenshots shown with "(image deleted)" indicator

## Notes

- First run downloads YOLOv8n model (~6MB)
- MJPEG stream includes drawn bounding boxes (server-side)
- WebSocket broadcasts detection list in real-time
- Cooldown prevents Telegram spam (default: 30s between notifications)
- Retention is per-date-folder, not per-image (oldest date folders are deleted)
