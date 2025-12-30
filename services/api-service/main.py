#!/usr/bin/env python3
"""
API Service for YouTube Analytics Pipeline
Provides REST API for configuration and monitoring
"""
import os
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube Analytics API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        database=os.getenv('POSTGRES_DB', 'youtube_analytics'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres')
    )

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "YouTube Analytics API", "status": "running"}

@app.get("/health")
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@app.get("/videos")
def get_videos():
    """Get all videos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT video_id, title, MAX(timestamp) as last_updated
            FROM video_stats
            GROUP BY video_id, title
            ORDER BY last_updated DESC
            """
        )
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        videos = [
            {
                "video_id": row[0],
                "title": row[1],
                "last_updated": row[2]
            }
            for row in results
        ]
        return {"videos": videos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos/{video_id}/stats")
def get_video_stats(video_id: str):
    """Get statistics for a specific video"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT statistics, timestamp
            FROM video_stats
            WHERE video_id = %s
            ORDER BY timestamp DESC
            LIMIT 10
            """
        )
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        stats = [
            {
                "statistics": json.loads(row[0]),
                "timestamp": row[1]
            }
            for row in results
        ]
        return {"video_id": video_id, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ksqldb/status")
def ksqldb_status():
    """Check ksqlDB status"""
    try:
        ksqldb_url = os.getenv('KSQLDB_URL', 'http://ksqldb-server:8088')
        import requests
        response = requests.get(f"{ksqldb_url}/info")
        return {"status": "connected", "ksqldb_info": response.json()}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

