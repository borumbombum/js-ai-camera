import os
import asyncio
from io import BytesIO
import cv2
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8782764125:AAHXcr1moRapuiSsEs6-piSV4QClW91Umvk")

class TelegramNotifier:
    def __init__(self, token: str = TELEGRAM_BOT_TOKEN):
        self.token = token
        self.application = None
        self.chat_id = None
        
    async def start(self):
        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("id", self.get_id_command))
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("👋 Camera bot active! You'll receive notifications when people are detected.")
        self.chat_id = update.effective_chat.id
        
    async def get_id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"Your chat ID: {update.effective_chat.id}")
        self.chat_id = update.effective_chat.id
        
    async def send_detection_alert(self, frame: np.ndarray, detections: list):
        if self.chat_id is None:
            print("No chat ID configured. Send /start to the bot first.")
            return
            
        _, buffer = cv2.imencode('.jpg', frame)
        photo = BytesIO(buffer)
        photo.name = 'detection.jpg'
        
        detection_text = "\n".join([f"• {d.class_name} ({d.confidence:.1%})" for d in detections])
        message = f"🚨 Person Detected!\n\n{detection_text}"
        
        try:
            await self.application.bot.send_photo(
                chat_id=self.chat_id,
                photo=photo,
                caption=message
            )
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")
            
    def set_chat_id(self, chat_id: int):
        self.chat_id = chat_id
        
    async def stop(self):
        if self.application:
            await self.application.stop()
