#!/usr/bin/env python3
"""
Data Processor Service
Consumes raw YouTube stats, calculates changes, and emits processed events
"""

import os
import json
import logging
from kafka import KafkaConsumer, KafkaProducer
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("data-processor")


class DataProcessor:
    def __init__(self):
        # Kafka config
        self.kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:29092")
        self.topic_raw = os.getenv("KAFKA_TOPIC_RAW", "youtube-raw-data")
        self.topic_processed = os.getenv("KAFKA_TOPIC_PROCESSED", "youtube-processed-data")

        # Business rule
        self.change_threshold = float(os.getenv("CHANGE_THRESHOLD", "0.05"))

        # Kafka consumer
        self.consumer = KafkaConsumer(
            self.topic_raw,
            bootstrap_servers=self.kafka_bootstrap,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            group_id="data-processor-group",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )

        # Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=self.kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        # PostgreSQL
        self.pg_conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "youtube_analytics"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        )

        self._init_db()

    # -------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------

    def _init_db(self):
        """Create state table if it does not exist"""
        with self.pg_conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS video_stats (
                    video_id VARCHAR(50) PRIMARY KEY,
                    title TEXT,
                    statistics JSONB NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.pg_conn.commit()

    def get_previous_stats(self, video_id):
        with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT statistics FROM video_stats WHERE video_id = %s",
                (video_id,),
            )
            row = cur.fetchone()
            return row["statistics"] if row else None

    def upsert_stats(self, video_id, title, statistics):
        with self.pg_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO video_stats (video_id, title, statistics)
                VALUES (%s, %s, %s)
                ON CONFLICT (video_id)
                DO UPDATE SET
                    statistics = EXCLUDED.statistics,
                    last_updated = CURRENT_TIMESTAMP
                """,
                (video_id, title, json.dumps(statistics)),
            )
            self.pg_conn.commit()

    # -------------------------------------------------------------------
    # Processing Logic
    # -------------------------------------------------------------------

    def calculate_changes(self, old_stats, new_stats):
        changes = {}

        for key in ["viewCount", "likeCount", "commentCount"]:
            old = int(old_stats.get(key, 0))
            new = int(new_stats.get(key, 0))

            if old == 0:
                changes[key] = 1.0 if new > 0 else 0.0
            else:
                changes[key] = (new - old) / old

        return changes

    def has_significant_change(self, changes):
        return any(abs(v) >= self.change_threshold for v in changes.values())

    def process_message(self, message):
        data = message.value

        video_id = data["video_id"]
        title = data.get("title", "Unknown")
        new_stats = data["statistics"]

        old_stats = self.get_previous_stats(video_id)

        # Always persist latest snapshot
        self.upsert_stats(video_id, title, new_stats)

        if not old_stats:
            logger.info(f"First observation for video {video_id}")
            return

        changes = self.calculate_changes(old_stats, new_stats)

        if not self.has_significant_change(changes):
            logger.info(f"No significant change for video {video_id}")
            return

        processed_event = {
            "video_id": video_id,
            "title": title,
            "changes": changes,
            "new_stats": new_stats,
        }

        self.producer.send(self.topic_processed, processed_event)
        logger.info(f"Published processed event for video {video_id}")

    # -------------------------------------------------------------------
    # Run Loop
    # -------------------------------------------------------------------

    def run(self):
        logger.info("Data Processor Service started")
        for message in self.consumer:
            try:
                self.process_message(message)
            except Exception as e:
                logger.exception(f"Failed to process message: {e}")


if __name__ == "__main__":
    processor = DataProcessor()
    processor.run()
