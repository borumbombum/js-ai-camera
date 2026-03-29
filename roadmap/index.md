# AI Camera Roadmap

## v1.0 (Current)

### Features
- [ ] [001: Continuous alert marking for timelapse](./001-continuous-alert-marking.md) - Track all detection frames, not just Telegram-triggering ones

## v0.x (Completed)

### Core Detection System
- [x] YOLOv8 person detection with configurable confidence threshold
- [x] Animal detection (dog, cat, bird, horse, sheep, cow, chicken, pig, rabbit)
- [x] Separate cooldowns for person and animal detections
- [x] Telegram notifications with emojis
- [x] Bounding boxes on Telegram screenshots

### Web UI
- [x] Live camera stream with MJPEG feed
- [x] Real-time object detection display
- [x] Forest DaisyUI theme
- [x] Sidebar menu (Live Camera, Timelapse, Event History, Server Logs, Telegram)
- [x] Screenshot button

### Timelapse
- [x] 24-hour rolling timelapse recording (2s intervals)
- [x] Timelapse viewer with date/hour selection
- [x] Alert highlighting in thumbnails
- [x] Deep-linking from Telegram messages

### Server Management
- [x] npm run server/stop/restart scripts
- [x] SQLite event storage
- [x] Configuration via .env
