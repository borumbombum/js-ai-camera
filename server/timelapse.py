import os
import cv2
import asyncio
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

TIMELAPSE_RETENTION_HOURS = int(os.getenv("TIMELAPSE_RETENTION_HOURS", "24"))


class TimelapseRecorder:
    def __init__(self, storage_dir: str = "recordings", interval: float = 2.0):
        self.storage_dir = Path(storage_dir)
        self.interval = interval
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self._frame_getter = None
        self._latest_path: Optional[Path] = None

    def set_frame_getter(self, getter):
        self._frame_getter = getter

    async def start(self):
        self.running = True
        self.task = asyncio.create_task(self._capture_loop())
        asyncio.create_task(self._cleanup_loop())
        print(
            f"[Timelapse] Started recording every {self.interval}s to {self.storage_dir}"
        )

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("[Timelapse] Stopped")

    async def _capture_loop(self):
        while self.running:
            try:
                await self._capture()
            except Exception as e:
                print(f"[Timelapse] Capture error: {e}")
            await asyncio.sleep(self.interval)

    async def _capture(self):
        if self._frame_getter is None:
            return

        frame = self._frame_getter()
        if frame is None:
            return

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%H")
        time_str = now.strftime("%M_%S")
        filename = f"{time_str}.jpg"

        folder = self.storage_dir / date_str / hour_str
        folder.mkdir(parents=True, exist_ok=True)

        filepath = folder / filename
        cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        self._latest_path = filepath

    async def _cleanup_loop(self):
        while self.running:
            await asyncio.sleep(3600)
            self.cleanup()

    def cleanup(self):
        cutoff = datetime.now() - timedelta(hours=TIMELAPSE_RETENTION_HOURS)
        removed = 0
        for date_folder in self.storage_dir.iterdir():
            if not date_folder.is_dir():
                continue
            try:
                folder_date = datetime.strptime(date_folder.name, "%Y-%m-%d")
                if folder_date < cutoff:
                    shutil.rmtree(date_folder)
                    removed += 1
            except ValueError:
                continue
        if removed:
            print(
                f"[Timelapse] Cleaned up {removed} old folders (retention: {TIMELAPSE_RETENTION_HOURS}h)"
            )

    def get_image_path(self, timestamp: datetime) -> Optional[Path]:
        date_str = timestamp.strftime("%Y-%m-%d")
        hour_str = timestamp.strftime("%H")
        minute_str = timestamp.strftime("%M")
        second = int(timestamp.strftime("%S"))
        rounded_second = (second // 2) * 2
        time_str = f"{minute_str}_{rounded_second:02d}"

        folder = self.storage_dir / date_str / hour_str
        filepath = folder / f"{time_str}.jpg"

        if filepath.exists():
            return filepath
        return None

    def list_images(self, date: str, hour: int) -> list:
        folder = self.storage_dir / date / f"{hour:02d}"
        if not folder.exists():
            return []

        images = []
        for f in sorted(folder.glob("*.jpg")):
            images.append(f"/timelapse/image?path={f}")
        return images

    def get_latest_image_path(self) -> Optional[Path]:
        if self._latest_path:
            return self._latest_path
        return None
