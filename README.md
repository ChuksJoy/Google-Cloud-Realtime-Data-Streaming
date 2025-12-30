# YouTube Analytics Real-Time Pipeline

An end-to-end data engineering pipeline for real-time YouTube Analytics with Telegram notifications.

## Architecture

- **Kafka** (KRaft mode) - Message streaming
- **ksqlDB** - Stream processing
- **Schema Registry** - Schema management
- **PostgreSQL** - Data storage
- **Redis** - Caching
- **YouTube Fetcher** - Fetches YouTube data
- **Data Processor** - Processes and detects changes
- **Telegram Notifier** - Sends notifications
- **API Service** - REST API for monitoring

## Prerequisites

- Docker and Docker Compose
- YouTube Data API v3 key
- Telegram Bot Token

## Setup

1. **Clone and navigate to the project directory**

2. **Create `.env` file**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your credentials. See **[SETUP_CREDENTIALS.md](SETUP_CREDENTIALS.md)** for detailed instructions on obtaining:
   - `YOUTUBE_API_KEY` - Get from [Google Cloud Console](https://console.cloud.google.com/)
   - `YOUTUBE_CHANNEL_ID` or `YOUTUBE_PLAYLIST_ID` - Your YouTube channel/playlist ID
   - `TELEGRAM_BOT_TOKEN` - Create a bot via [@BotFather](https://t.me/botfather)
   - `TELEGRAM_CHAT_ID` - Your Telegram chat ID

   **Verify your credentials** (optional but recommended):
   ```bash
   pip install requests python-dotenv
   python verify_credentials.py
   ```

3. **Initialize PostgreSQL database**:
   ```bash
   docker-compose up -d postgres
   docker exec -i postgres psql -U postgres -d youtube_analytics < services/api-service/init_db.sql
   ```

4. **Start all services**:
   ```bash
   docker-compose up -d
   ```

## Services

- **Kafka Broker**: `localhost:9092`
- **Schema Registry**: `http://localhost:8081`
- **ksqlDB Server**: `http://localhost:8088`
- **Kafka Connect**: `http://localhost:8083`
- **Control Center**: `http://localhost:9021`
- **API Service**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /videos` - List all videos
- `GET /videos/{video_id}/stats` - Get video statistics
- `GET /ksqldb/status` - Check ksqlDB status

## Usage

1. The pipeline automatically fetches YouTube data at the configured interval
2. When significant changes are detected (based on `CHANGE_THRESHOLD`), notifications are sent to Telegram
3. Monitor the pipeline via Control Center at `http://localhost:9021`
4. Query data via the API service at `http://localhost:8000`

## Monitoring

- **Control Center**: `http://localhost:9021` - Kafka and ksqlDB monitoring
- **API Docs**: `http://localhost:8000/docs` - FastAPI documentation

## Stopping Services

```bash
docker-compose down
```

To remove volumes:
```bash
docker-compose down -v
```

