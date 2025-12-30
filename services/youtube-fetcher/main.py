#!/usr/bin/env python3
"""
YouTube Data Fetcher Service
Fetches YouTube video/playlist data, casts stats to int, stores in Postgres, and publishes to Kafka
"""
import os
import time
import json
import logging
from kafka import KafkaProducer
from googleapiclient.discovery import build
import psycopg2
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeFetcher:
    def __init__(self):
        # Config
        self.kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:29092")
        self.kafka_topic = os.getenv("KAFKA_TOPIC", "youtube-raw-data")
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.playlist_id = os.getenv("YOUTUBE_PLAYLIST_ID")
        self.poll_interval = int(os.getenv("POLL_INTERVAL", "60"))

        # Kafka Producer
        self.producer = KafkaProducer(
            bootstrap_servers=self.kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all"
        )

        # YouTube API client
        self.youtube = build("youtube", "v3", developerKey=self.youtube_api_key)

        # PostgreSQL connection
        self.pg_conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "youtube_analytics"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        self._init_db()

    def _init_db(self):
        """Initialize table for deduplication and stats storage"""
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS video_stats (
                    video_id VARCHAR(255) NOT NULL,
                    title TEXT,
                    statistics JSONB,
                    timestamp BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (video_id, timestamp)
                );
            """)
            self.pg_conn.commit()

    def is_processed(self, video_id):
        """Check if video already processed in Postgres (deduplication)"""
        with self.pg_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM video_stats WHERE video_id = %s", (video_id,))
            return cur.fetchone() is not None

    def store_video_stats(self, video_id, title, statistics):
        """Store video stats in Postgres (JSONB compatible)"""
        timestamp = int(time.time())
        clean_stats = {k: int(v) for k, v in statistics.items() if str(v).isdigit()}
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO video_stats (video_id, title, statistics, timestamp)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (video_id, timestamp) DO NOTHING
            """, (video_id, title, json.dumps(clean_stats), timestamp))
            self.pg_conn.commit()

    def fetch_playlist_videos(self):
        """Fetch all video IDs from the playlist"""
        videos = []
        next_page_token = None
        while True:
            try:
                request = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=self.playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                for item in response.get("items", []):
                    videos.append(item["snippet"]["resourceId"]["videoId"])
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
            except Exception as e:
                logger.error(f"Error fetching playlist videos: {e}")
                break
        return videos

    def fetch_video_stats(self, video_id):
        """Fetch stats for a single video"""
        try:
            request = self.youtube.videos().list(
                part="statistics,snippet",
                id=video_id
            )
            response = request.execute()
            return response.get("items", [None])[0]
        except Exception as e:
            logger.error(f"Error fetching video stats: {e}")
            return None

    def process_and_publish(self):
        """Fetch videos, deduplicate, cast stats, store in Postgres, publish to Kafka"""
        video_ids = self.fetch_playlist_videos()
        for video_id in video_ids:
            if self.is_processed(video_id):
                continue
            video_data = self.fetch_video_stats(video_id)
            if not video_data:
                continue

            stats = video_data.get("statistics", {})
            processed_stats = {
                "viewCount": int(stats.get("viewCount", 0)),
                "likeCount": int(stats.get("likeCount", 0)),
                "commentCount": int(stats.get("commentCount", 0))
            }

            payload = {
                "video_id": video_id,
                "title": video_data["snippet"]["title"],
                "statistics": processed_stats,
                "timestamp": int(time.time())
            }

            # Publish to Kafka
            self.producer.send(self.kafka_topic, value=payload)
            logger.info(f"Published video: {video_data['snippet']['title']}")

            # Store in Postgres for deduplication
            self.store_video_stats(video_id, video_data["snippet"]["title"], processed_stats)

    def run(self):
        logger.info("YouTube Fetcher Service started")
        while True:
            try:
                self.process_and_publish()
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                logger.info("Shutting down fetcher...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(self.poll_interval)


if __name__ == "__main__":
    fetcher = YouTubeFetcher()
    fetcher.run()
