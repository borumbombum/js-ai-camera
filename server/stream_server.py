import os
import sqlite3
import cv2
import asyncio
import json
import time
import numpy as np
from collections import deque
from datetime import datetime
from io import BytesIO
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

from detector import ObjectDetector, Detection
from telegram_bot import TelegramNotifier

DB_PATH = Path(__file__).parent / "events.db"

DETECTION_COOLDOWN = int(os.getenv("DETECTION_COOLDOWN", "30"))
PERSON_CONFIDENCE_THRESHOLD = float(os.getenv("PERSON_CONFIDENCE_THRESHOLD", "0.51"))
ANIMAL_CONFIDENCE_THRESHOLD = float(os.getenv("ANIMAL_CONFIDENCE_THRESHOLD", "0.51"))
ANIMAL_COOLDOWN = int(os.getenv("ANIMAL_COOLDOWN", "30"))


class Camera:
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.current_frame: Optional[np.ndarray] = None
        self.current_detections: List[Detection] = []
        self.last_person_detection = 0
        self.last_animal_detection = 0

    def open(self):
        log_event(f"Opening camera {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            log_event(f"Failed to open camera {self.camera_index}", "ERROR")
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        log_event("Camera opened successfully")
        return True

    def read(self) -> Optional[np.ndarray]:
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
        return frame if ret else None

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()
camera = Camera()
detector = ObjectDetector()
log_buffer = deque(maxlen=100)


def log_event(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = {"timestamp": timestamp, "level": level, "message": message}
    log_buffer.append(entry)
    print(f"[{timestamp}] [{level}] {message}")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            objects TEXT NOT NULL,
            telegram_message_id INTEGER,
            telegram_url TEXT,
            screenshot_path TEXT
        )
    """)
    conn.commit()
    conn.close()
    log_event("Database initialized")


def save_event(
    objects: str,
    telegram_message_id: Optional[int] = None,
    screenshot_path: Optional[str] = None,
) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO events (timestamp, objects, telegram_message_id, telegram_url, screenshot_path) VALUES (?, ?, ?, ?, ?)",
        (
            datetime.now().isoformat(),
            objects,
            telegram_message_id,
            None,
            screenshot_path,
        ),
    )
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id


def get_events_from_db(limit: int = 100) -> List[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT id, timestamp, objects, telegram_message_id, telegram_url, screenshot_path FROM events ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "objects": row[2],
            "telegram_message_id": row[3],
            "telegram_url": f"https://t.me/jsaicamerabot/{row[3]}" if row[3] else None,
            "screenshot_path": row[4],
        }
        for row in rows
    ]


def delete_event(event_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


telegram = TelegramNotifier(log_callback=lambda msg, level=None: log_event(msg, level))


async def detection_loop():
    while True:
        frame = camera.read()
        if frame is None:
            await asyncio.sleep(0.1)
            continue

        detections = detector.detect(frame)
        frame_with_boxes = detector.draw_detections(frame, detections)
        camera.current_frame = frame_with_boxes
        camera.current_detections = detections

        detection_data = [
            {"class": d.class_name, "confidence": float(d.confidence), "bbox": d.bbox}
            for d in sorted(detections, key=lambda x: x.confidence, reverse=True)
        ]
        await manager.broadcast(
            json.dumps({"type": "detections", "data": detection_data})
        )

        persons = detector.get_person_detections(
            detections, PERSON_CONFIDENCE_THRESHOLD
        )
        if (
            persons
            and (time.time() - camera.last_person_detection) > DETECTION_COOLDOWN
        ):
            camera.last_person_detection = time.time()
            asyncio.create_task(handle_detection(frame, persons))
            log_event(f"Person detected! Sending Telegram notification", "WARNING")

        animals = detector.get_animal_detections(
            detections, ANIMAL_CONFIDENCE_THRESHOLD
        )
        if animals and (time.time() - camera.last_animal_detection) > ANIMAL_COOLDOWN:
            camera.last_animal_detection = time.time()
            asyncio.create_task(handle_detection(frame, animals))
            animal_types = ", ".join(sorted(set(a.class_name for a in animals)))
            log_event(
                f"Animal detected ({animal_types})! Sending Telegram notification",
                "WARNING",
            )

        await asyncio.sleep(0.1)


async def handle_detection(frame, persons):
    success, message_id, status = await telegram.send_detection_alert(frame, persons)
    objects_str = ", ".join(sorted(set(p.class_name for p in persons)))
    event_id = save_event(objects_str, message_id)
    log_event(f"Event saved: id={event_id}, telegram_msg_id={message_id}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    camera.open()
    asyncio.create_task(detection_loop())
    asyncio.create_task(telegram.start())
    yield
    camera.release()
    await telegram.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {
        "message": "AI Camera Server",
        "stream": "/stream",
        "video_feed": "/video_feed",
    }


@app.get("/stream")
async def stream_page():
    template_path = Path(__file__).parent / "templates" / "stream.html"
    with open(template_path, "r") as f:
        return HTMLResponse(f.read())


def generate_mjpeg():
    while True:
        frame = camera.current_frame
        if frame is not None:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
        time.sleep(0.03)


@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(
        generate_mjpeg(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/screenshot")
async def screenshot():
    frame = camera.current_frame
    if frame is None:
        log_event("Screenshot failed: no frame available", "ERROR")
        return {"error": "No frame available"}

    if camera.current_detections:
        log_event(
            f"Screenshot: triggering Telegram notification for {len(camera.current_detections)} objects",
            "INFO",
        )
        asyncio.create_task(
            telegram.send_detection_alert(frame, camera.current_detections)
        )
    else:
        log_event("Screenshot: no detections to notify", "INFO")

    _, buffer = cv2.imencode(".jpg", frame)
    return StreamingResponse(BytesIO(buffer.tobytes()), media_type="image/jpeg")


@app.get("/detections")
async def get_detections():
    return {
        "detections": [
            {"class": d.class_name, "confidence": float(d.confidence), "bbox": d.bbox}
            for d in camera.current_detections
        ]
    }


@app.get("/logs")
async def get_logs():
    return {"logs": list(log_buffer)}


@app.get("/events")
async def get_events_endpoint(limit: int = 100):
    return {"events": get_events_from_db(limit)}


@app.delete("/events/{event_id}")
async def delete_event_endpoint(event_id: int):
    if delete_event(event_id):
        return {"success": True, "message": f"Event {event_id} deleted"}
    raise HTTPException(status_code=404, detail="Event not found")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4422)
