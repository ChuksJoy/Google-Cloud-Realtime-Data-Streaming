-- Initialize database schema for YouTube Analytics
CREATE TABLE IF NOT EXISTS video_stats (
    video_id VARCHAR(255) NOT NULL,
    title TEXT,
    statistics JSONB,
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (video_id, timestamp)
);

-- Index for faster lookups by video_id
CREATE INDEX IF NOT EXISTS idx_video_id ON video_stats(video_id);
-- Index for faster timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_timestamp ON video_stats(timestamp DESC);
-- Table for deduplication of videos fetched from YouTube
CREATE TABLE IF NOT EXISTS processed_videos (
    video_id VARCHAR(50) PRIMARY KEY,
    last_fetched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
