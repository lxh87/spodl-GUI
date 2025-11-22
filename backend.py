#!/usr/bin/env python3
"""
SpotDL GUI Backend - Uses your local SpotDL installation
Works with SpotDL installed in C:\Windows\system32 or anywhere in PATH
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import uuid
import asyncio
import os
from typing import Optional, List, Dict
from pathlib import Path
import json

app = FastAPI(title="SpotDL GUI Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track active downloads
downloads: Dict[str, dict] = {}

class DownloadRequest(BaseModel):
    query: str
    audioProviders: List[str]
    lyricsProviders: List[str]
    format: str
    bitrate: str
    threads: int
    output: str
    overwrite: str
    preload: bool = False
    sponsorBlock: bool = False
    skipExplicit: bool = False
    fetchAlbums: bool = False
    playlistNumbering: bool = False
    generateLrc: bool = False
    dontFilterResults: bool = False
    onlyVerifiedResults: bool = False
    addUnavailable: bool = False
    printErrors: bool = True
    m3u: Optional[str] = None
    albumType: Optional[str] = None

def check_spotdl():
    """Check if SpotDL is available in PATH or common locations"""
    # Try direct command first
    try:
        result = subprocess.run(
            ["spotdl", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return "spotdl"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try common Windows locations
    common_paths = [
        r"C:\Windows\system32\spotdl.exe",
        r"C:\Windows\System32\spotdl.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python*\Scripts\spotdl.exe"),
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    raise Exception("SpotDL not found! Please ensure it's installed and in PATH")

async def run_download_task(download_id: str, cmd: List[str], query: str):
    """Background task to run spotdl command"""
    try:
        print(f"\n📥 Starting download: {query}")
        print(f"🔧 Command: {' '.join(cmd)}\n")

        # Run spotdl command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.expanduser("~/Music")  # Download to Music folder
        )

        downloads[download_id]["process"] = process
        downloads[download_id]["status"] = "downloading"

        # Wait for completion
        stdout, stderr = await process.communicate()

        stdout_text = stdout.decode('utf-8', errors='ignore')
        stderr_text = stderr.decode('utf-8', errors='ignore')

        # Log output
        if stdout_text:
            print(f"✅ SpotDL Output:\n{stdout_text}")
        if stderr_text and process.returncode != 0:
            print(f"❌ SpotDL Error:\n{stderr_text}")

        # Update status
        if process.returncode == 0:
            downloads[download_id]["status"] = "completed"
            downloads[download_id]["progress"] = 100
            print(f"✅ Download completed: {query}\n")
        else:
            downloads[download_id]["status"] = "failed"
            downloads[download_id]["error"] = stderr_text or "Download failed"
            print(f"❌ Download failed: {query}\n")

    except Exception as e:
        print(f"❌ Exception during download: {str(e)}\n")
        downloads[download_id]["status"] = "failed"
        downloads[download_id]["error"] = str(e)

@app.on_event("startup")
async def startup_event():
    """Check SpotDL availability on startup"""
    try:
        spotdl_path = check_spotdl()
        print("\n" + "="*60)
        print("🎵 SpotDL GUI Backend Starting...")
        print("="*60)
        print(f"✅ SpotDL found at: {spotdl_path}")
        print(f"📍 Downloads will be saved to: {os.path.expanduser('~/Music')}")
        print(f"🌐 API running at: http://localhost:8800")
        print(f"🖥️  Frontend should connect from: http://localhost:5173")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        print("Please install SpotDL: pip install spotdl\n")

@app.get("/")
async def root():
    return {
        "message": "SpotDL GUI Backend",
        "status": "running",
        "spotdl_available": True,
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        spotdl_path = check_spotdl()
        return {
            "status": "ok",
            "spotdl_path": spotdl_path,
            "download_folder": os.path.expanduser("~/Music")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/download")
async def download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Start a download using local SpotDL installation"""
    download_id = str(uuid.uuid4())

    try:
        spotdl_cmd = check_spotdl()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Build spotdl command
    cmd = [spotdl_cmd, request.query]

    # Add providers
    if request.audioProviders:
        cmd.extend(["--audio"] + request.audioProviders)
    if request.lyricsProviders:
        cmd.extend(["--lyrics"] + request.lyricsProviders)

    # Add format options
    cmd.extend([
        "--format", request.format,
        "--bitrate", request.bitrate,
        "--threads", str(request.threads),
        "--output", request.output,
        "--overwrite", request.overwrite,
    ])

    # Add boolean flags
    if request.preload:
        cmd.append("--preload")
    if request.sponsorBlock:
        cmd.append("--sponsor-block")
    if request.skipExplicit:
        cmd.append("--skip-explicit")
    if request.fetchAlbums:
        cmd.append("--fetch-albums")
    if request.playlistNumbering:
        cmd.append("--playlist-numbering")
    if request.generateLrc:
        cmd.append("--generate-lrc")
    if request.dontFilterResults:
        cmd.append("--dont-filter-results")
    if request.onlyVerifiedResults:
        cmd.append("--only-verified-results")
    if request.addUnavailable:
        cmd.append("--add-unavailable")
    if request.printErrors:
        cmd.append("--print-errors")

    # Add optional parameters
    if request.m3u:
        cmd.extend(["--m3u", request.m3u])
    if request.albumType:
        cmd.extend(["--album-type", request.albumType])

    # Initialize download tracking
    downloads[download_id] = {
        "id": download_id,
        "query": request.query,
        "status": "queued",
        "progress": 0,
        "command": " ".join(cmd),
        "format": request.format,
        "bitrate": request.bitrate,
    }

    # Start download in background
    background_tasks.add_task(run_download_task, download_id, cmd, request.query)

    return {
        "downloadId": download_id,
        "message": "Download started successfully"
    }

@app.get("/api/download/{download_id}/status")
async def get_status(download_id: str):
    """Get download status"""
    if download_id not in downloads:
        raise HTTPException(status_code=404, detail="Download not found")

    download = downloads[download_id]

    # Estimate progress based on status
    progress = 0
    if download["status"] == "queued":
        progress = 0
    elif download["status"] == "downloading":
        progress = 50  # Can't get real progress without parsing spotdl output
    elif download["status"] == "completed":
        progress = 100
    elif download["status"] == "failed":
        progress = 0

    return {
        "id": download_id,
        "status": download["status"],
        "progress": progress,
        "currentFile": download.get("query"),
        "error": download.get("error"),
    }

@app.delete("/api/download/{download_id}")
async def cancel_download(download_id: str):
    """Cancel a download"""
    if download_id not in downloads:
        raise HTTPException(status_code=404, detail="Download not found")

    download = downloads[download_id]

    # Try to kill the process if it's running
    if "process" in download:
        try:
            download["process"].kill()
            await download["process"].wait()
        except:
            pass

    download["status"] = "cancelled"

    return {"message": "Download cancelled"}

@app.get("/api/providers/audio")
async def get_audio_providers():
    """Get available audio providers"""
    return ["youtube", "youtube-music", "slider-kz", "soundcloud", "bandcamp", "piped"]

@app.get("/api/providers/lyrics")
async def get_lyrics_providers():
    """Get available lyrics providers"""
    return ["genius", "musixmatch", "azlyrics", "synced"]

@app.post("/api/validate")
async def validate_query(data: dict):
    """Validate a Spotify/YouTube URL or query"""
    query = data.get("query", "")

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
    elif query in ["saved", "all-user-playlists", "all-saved-playlists",
                   "all-user-followed-artists", "all-user-saved-albums"]:
        query_type = "spotify_special"

    return {
        "valid": bool(query),
        "type": query_type,
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8800,
        log_level="info"
    )
