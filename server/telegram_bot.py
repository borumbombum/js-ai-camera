import os
import asyncio
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

import cv2
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


class TelegramNotifier:
    def __init__(self, token: str = None, log_callback=None):
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.log = log_callback or (lambda msg, level=None: print(msg))
        self.application = None

    async def start(self):
        if not self.token:
            self.log(
                "Telegram bot token not configured. Set TELEGRAM_BOT_TOKEN in .env",
                "ERROR",
            )
            return

        if self.chat_id:
            self.log(f"Telegram configured with chat ID: {self.chat_id}")
        else:
            self.log(
                "No chat ID configured. Send /start to the bot or set TELEGRAM_CHAT_ID in .env",
                "WARNING",
            )

        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("id", self.get_id_command))
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 Camera bot active! You'll receive notifications when people are detected."
        )
        self.chat_id = update.effective_chat.id
        self.log(f"Chat ID registered: {self.chat_id}")

    async def get_id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"Your chat ID: {update.effective_chat.id}")
        self.chat_id = update.effective_chat.id

    async def send_detection_alert(self, frame: np.ndarray, detections: list):
        if not self.chat_id:
            self.log("Cannot send notification: no chat ID configured", "ERROR")
            return

        if not self.application:
            self.log("Cannot send notification: bot not initialized", "ERROR")
            return

        _, buffer = cv2.imencode(".jpg", frame)
        photo = BytesIO(buffer)
        photo.name = "detection.jpg"

        if not detections:
            message = "📷 Screenshot\n\nNo objects detected"
        else:
            unique_classes = ", ".join(sorted(set(d.class_name for d in detections)))
            detection_text = "\n".join(
                [f"• {d.class_name} ({d.confidence:.1%})" for d in detections]
            )
            message = f"🚨 Detection Alert!\n\n{unique_classes}\n\n{detection_text}"

        try:
            await self.application.bot.send_photo(
                chat_id=self.chat_id, photo=photo, caption=message
            )
            self.log(
                f"Telegram notification sent: {len(detections)} object(s) detected",
                "INFO",
            )
        except Exception as e:
            self.log(f"Failed to send Telegram notification: {e}", "ERROR")

    def set_chat_id(self, chat_id: int):
        self.chat_id = chat_id

    async def stop(self):
        if self.application:
            await self.application.stop()
