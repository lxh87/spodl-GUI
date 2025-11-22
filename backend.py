#!/usr/bin/env python3
"""
Simple mock backend for SpotDL GUI testing
This simulates the API without actually downloading anything
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from typing import Optional, List
import random

app = FastAPI(title="SpotDL Mock API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock download storage
downloads = {}

class DownloadRequest(BaseModel):
    query: str
    audioProviders: List[str]
    lyricsProviders: List[str]
    format: str
    bitrate: str
    threads: int
    output: str
    overwrite: str
    preload: bool
    sponsorBlock: bool
    skipExplicit: bool
    fetchAlbums: bool
    playlistNumbering: bool
    generateLrc: bool
    dontFilterResults: bool
    onlyVerifiedResults: bool
    addUnavailable: bool
    printErrors: bool
    m3u: Optional[str] = None
    albumType: Optional[str] = None

@app.get("/")
async def root():
    return {
        "message": "SpotDL Mock API Server",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "download": "POST /api/download",
            "status": "GET /api/download/{id}/status",
            "cancel": "DELETE /api/download/{id}",
            "providers": "GET /api/providers/{audio|lyrics}"
        }
    }

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Mock API is running"}

@app.post("/api/download")
async def download(request: DownloadRequest):
    download_id = str(uuid.uuid4())

    # Simulate download
    downloads[download_id] = {
        "id": download_id,
        "query": request.query,
        "status": "downloading",
        "progress": 0,
        "format": request.format,
        "bitrate": request.bitrate,
    }

    print(f"📥 Mock download started: {request.query}")
    print(f"   Format: {request.format}, Bitrate: {request.bitrate}")
    print(f"   Audio providers: {', '.join(request.audioProviders)}")

    return {
        "downloadId": download_id,
        "message": "Mock download started successfully"
    }

@app.get("/api/download/{download_id}/status")
async def get_status(download_id: str):
    if download_id not in downloads:
        raise HTTPException(status_code=404, detail="Download not found")

    download = downloads[download_id]

    # Simulate progress
    if download["status"] == "downloading":
        download["progress"] = min(download["progress"] + random.randint(5, 20), 100)

        if download["progress"] >= 100:
            download["status"] = "completed"

    return {
        "id": download_id,
        "status": download["status"],
        "progress": download["progress"],
        "currentFile": f"Song from: {download['query']}" if download["status"] == "downloading" else None,
    }

@app.delete("/api/download/{download_id}")
async def cancel_download(download_id: str):
    if download_id not in downloads:
        raise HTTPException(status_code=404, detail="Download not found")

    downloads[download_id]["status"] = "cancelled"
    print(f"❌ Mock download cancelled: {download_id}")

    return {"message": "Download cancelled"}

@app.get("/api/providers/audio")
async def get_audio_providers():
    return ["youtube", "youtube-music", "slider-kz", "soundcloud", "bandcamp", "piped"]

@app.get("/api/providers/lyrics")
async def get_lyrics_providers():
    return ["genius", "musixmatch", "azlyrics", "synced"]

@app.post("/api/validate")
async def validate_query(data: dict):
    query = data.get("query", "")

    # Simple validation
    is_url = query.startswith("http")
    is_spotify = "spotify.com" in query
    is_youtube = "youtube.com" in query or "youtu.be" in query

    query_type = None
    if is_spotify:
        if "/track/" in query:
            query_type = "spotify_track"
        elif "/album/" in query:
            query_type = "spotify_album"
        elif "/playlist/" in query:
            query_type = "spotify_playlist"
        elif "/artist/" in query:
            query_type = "spotify_artist"
    elif is_youtube:
        query_type = "youtube_video" if "/watch" in query else "youtube_playlist"
    elif query in ["saved", "all-user-playlists"]:
        query_type = "spotify_special"

    return {
        "valid": bool(query),
        "type": query_type,
    }

if __name__ == "__main__":
    import uvicorn
    print("\n🎵 Starting SpotDL Mock API Server...")
    print("📍 Server will run at: http://localhost:8800")
    print("🌐 Frontend should connect to: http://localhost:5173")
    print("\n⚠️  This is a MOCK server - no actual downloads will happen!\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8800,
        log_level="info"
    )
