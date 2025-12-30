#!/usr/bin/env python3
"""
Telegram Notifier Service
Consumes processed YouTube analytics from Kafka
and sends notifications to Telegram (deduplicated via Postgres)
"""

import os
import json
import logging
import asyncio
from kafka import KafkaConsumer
from telegram import Bot
from telegram.error import TelegramError
import psycopg2
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        # Kafka
        self.kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:29092")
        self.kafka_topic = os.getenv("KAFKA_TOPIC", "youtube-processed-data")

        # Telegram
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.notification_threshold = float(
            os.getenv("NOTIFICATION_THRESHOLD", "0.05")
        )

        # Telegram Bot (async-only in v21+)
        self.bot = Bot(token=self.bot_token)

       # Define a safe deserializer
        def safe_deserialize(m):
            try:
                return json.loads(m.decode("utf-8"))
            except json.JSONDecodeError:
                logger.warning(f"Skipping non-JSON message found in topic: {m}")
                return None

        # Kafka Consumer (sync is fine)
        self.consumer = KafkaConsumer(
            self.kafka_topic,
            bootstrap_servers=self.kafka_bootstrap,
            value_deserializer=safe_deserialize,
            group_id="telegram-notifier-group",
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )

        # Postgres (deduplication)
        self.pg_conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "youtube_analytics"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        )

        self._init_db()

    def _init_db(self):
        """Create notification tracking table"""
        with self.pg_conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    video_id VARCHAR(50) PRIMARY KEY,
                    view_count BIGINT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (video_id, view_count)
                );
                """
            )
            self.pg_conn.commit()

    def is_sent(self, video_id: str, view_count: int) -> bool:
        with self.pg_conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM sent_notifications WHERE video_id = %s AND view_count = %s",
                (video_id, view_count),
            )
            return cur.fetchone() is not None

    def mark_as_sent(self, video_id: str, view_count: int):
        with self.pg_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sent_notifications (video_id, view_count)
                VALUES (%s, %s)
                ON CONFLICT (video_id, view_count) DO NOTHING
                """,
                (video_id,),
            )
            self.pg_conn.commit()

    def format_message(self, data: dict) -> str:
        title = data.get("title", "Unknown Video")
        video_id = data.get("video_id", "")
        changes = data.get("changes", {})
        new_stats = data.get("new_stats", {})

        msg = "🚀 *YouTube Analytics Alert*\n\n"
        msg += f"📹 *Video:* {title}\n"
        msg += f"🔗 [Watch on YouTube](https://www.youtube.com/watch?v={video_id})\n\n"

        msg += "📈 *Detected Changes:*\n"
        for stat, change in changes.items():
            if abs(change) >= self.notification_threshold:
                emoji = "📈" if change > 0 else "📉"
                msg += f"{emoji} {stat}: {abs(change) * 100:.2f}%\n"

        msg += "\n📊 *Current Stats:*\n"
        msg += f"👁️ Views: {new_stats.get('viewCount', 0):,}\n"
        msg += f"👍 Likes: {new_stats.get('likeCount', 0):,}\n"
        msg += f"💬 Comments: {new_stats.get('commentCount', 0):,}\n"

        return msg

    async def send_notification(self, data: dict):
        video_id = data.get("video_id")
        view_count = data.get("new_stats", {}).get("viewCount", 0)
        if not video_id or self.is_sent(video_id, view_count):
            return

        try:
            message = self.format_message(data)
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
            logger.info(f"Telegram alert sent: {data.get('title')}")
            self.mark_as_sent(video_id, view_count)

        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    async def run(self):
        logger.info("Telegram Notifier Service started (async)")
        for message in self.consumer:
            if message.value is None:
                continue
            try:
                await self.send_notification(message.value)
            except Exception as e:
                logger.error(f"Consumer loop error: {e}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    notifier = TelegramNotifier()
    asyncio.run(notifier.run())
