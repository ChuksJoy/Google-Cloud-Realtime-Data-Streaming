#  Real-Time YouTube Analytics Data Engineering Pipeline

##  Project Overview

In this project, I am building an end-to-end real-time data engineering pipeline that captures live activity from YouTube videos or playlists and delivers instant notifications to Telegram whenever an event occurs.

The goal of this project is to demonstrate how modern **streaming data architectures** work in practice — from API ingestion, to message streaming with Kafka, real-time processing using ksqlDB, and finally pushing insights to an external consumer (Telegram).

This project was inspired by [Codewithyu](https://www.youtube.com/watch?v=0aqSjJ3-4NI&list=PL_Ct8Cox2p8UlTfHyJc3RDGuGktPNs9Q3&index=40)

---

##  Project Roadmap

<img width="3087" height="1295" alt="image" src="https://github.com/user-attachments/assets/172adb94-76fa-463c-a4a4-8b8ee297062e" />

---

##  What I Am Learning & Implementing

Through this project, I am gaining hands-on experience with:

- Fetching real-time data from the **YouTube Data API** using Python
- Configuring **Google Cloud** to securely manage API access
- Building a **Kafka ecosystem** using Docker and Confluent containers
- Streaming data into Kafka topics with Python producers
- Processing and transforming streaming data using **ksqlDB**
- Using Kafka Connect to send data to **external systems**
- Sending **real-time alerts to Telegram** using a Telegram bot
- Applying **advanced Python concepts** for scalable data pipelines
- Designing a full **event-driven architecture**

---

##  High-Level Architecture
```text
          ┌───────────────┐
          │  YouTube API  │
          └───────┬──────┘
                  │ Pulls raw video & playlist data
                  ▼
          ┌───────────────┐
          │ YouTube Fetcher│
          │ (Python Service)│
          └───────┬──────┘
                  │ Produces messages
                  ▼
          ┌───────────────┐
          │  Kafka Broker │
          │  (PLAINTEXT:9092)│
          └───────┬──────┘
                  │ Streams raw data
                  ▼
          ┌───────────────┐
          │ ksqlDB Server │
          │ (Stream Processing) │
          └───────┬──────┘
                  │ Processed / Enriched data
                  ▼
          ┌───────────────┐
          │ Data Processor│
          │ (Python / ksqlDB)│
          └───────┬──────┘
           ┌──────┴──────┐
           │             │
   ┌───────────────┐  ┌───────────────┐
   │  PostgreSQL   │  │     Redis     │
   │ (Structured DB)│  │ (Cache / Queue)│
   └───────────────┘  └───────────────┘
           │             │
           ▼             ▼
   ┌───────────────┐  ┌───────────────┐
   │  API Service  │  │ Telegram Bot  │
   │ (Config / UI) │  │ (Notifications)│
   └───────────────┘  └───────────────┘

        ┌─────────────────────────┐
        │ Confluent Control Center │
        │ (Monitoring & Management)│
        └─────────────────────────┘
```
### System Architecture

The project implements a Stateful Stream Processing pattern across four containerised layers:

1. Ingestion Layer (Python 3.13 / YouTube Data API v3)
     - Polls the YouTube API for video statistics.
     - Implements idempotent production to ensure data integrity.
     - Publishes raw JSON events to a Kafka topic: youtube-raw-data.

2. Transport Layer (Confluent Kafka & KRaft/ZooKeeper)
     - Acts as the central message backbone for all microservices.
     - Managed via Confluent Control Center for real-time stream monitoring.

3. Processing Layer (Stateful Python Microservice)
   - Consumes raw events and compares them against a PostgreSQL State Store.
   - Calculates percentage changes in views, likes, and comments.
   - Emits “Significant Activity” events to the downstream topic (youtube-processed-data) only when a threshold (e.g., 5% change) is met.

4. Notification Layer (Async Telegram Bot API)
   - Consumes processed events and formats notifications in Markdown/HTML.
   - Uses asyncio to handle non-blocking Telegram API calls.
   - Implements post-consumer deduplication via PostgreSQL to prevent alert spam.
  
### Flow Description

1. **YouTube Fetcher** collects raw video and playlist data from the YouTube API and publishes messages to Kafka topics.  
2. **Kafka Broker** serves as the message bus, coordinating messaging and streaming. **ZooKeeper** manages cluster metadata.  
3. **ksqlDB Server** and **Data Processor** handle real-time stream processing, enrichment, and transformations.  
4. **PostgreSQL** stores processed structured data for analytics and reporting. **Redis** caches frequently accessed data for fast retrieval.  
5. **API Service** exposes processed data via REST endpoints. **Telegram Notifier** sends alerts based on processed data thresholds.  
6. **Confluent Control Center** provides a web-based dashboard for monitoring Kafka topics, streams, and connectors.  

This architecture is **modular and scalable**, allowing the addition of more Kafka brokers, ksqlDB nodes, or Connect workers for production environments.

All infrastructure components are orchestrated using **Docker Compose**, ensuring the entire system can be spun up locally with minimal setup.

---

##  Technologies Used

- **Python**
- **Apache Kafka**
- **ksqlDB**
- **Kafka Connect**
- **Docker & Docker Compose**
- **Google Cloud Platform (GCP)**
- **Telegram Bot API**

---

##  Project Features

-  Real-time ingestion of YouTube video and playlist activity  
-  Streaming and processing events with Kafka and ksqlDB  
-  Instant Telegram notifications for new activity  
-  Fully Dockerized setup for reproducibility  
-  Secure API configuration using Google Cloud  

## Key Data Engineering Patterns Demonstrated

- Stateful Change Data Capture (CDC): Tracks deltas over time instead of snapshots.
- Exactly-Once Processing: Combines Kafka offsets with database state to prevent duplicate notifications.
- Dead Letter Handling: Resilient deserializers handle malformed “Poison Pill” messages.
- Containerization: Full orchestration via Docker for reproducibility.
---
##  Useful References

- Confluent Documentation: https://docs.confluent.io/home/overview.html  
- YouTube API Documentation: https://developers.google.com/youtube  
- Kafka-Python Documentation: https://kafka-python.readthedocs.io  

---
**Clone and navigate to the project directory**

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
---
## Services

- **Kafka Broker**: `localhost:9092`
- **Schema Registry**: `http://localhost:8081`
- **ksqlDB Server**: `http://localhost:8088`
- **Kafka Connect**: `http://localhost:8083`
- **Control Center**: `http://localhost:9021`
- **API Service**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
---

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

