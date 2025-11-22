# Backend Setup Guide

The SpotDL GUI frontend needs a backend API to function. You have several options:

## Option 1: Mock Backend (For Testing UI Only) ⚡️

**Use this if you just want to test the UI without actual downloads.**

### Setup:
```bash
# Install dependencies
pip install -r requirements.txt

# Run the mock server
python backend.py
```

The mock server will:
- ✅ Accept download requests
- ✅ Simulate progress updates
- ❌ NOT actually download anything

This is perfect for UI development and testing!

---

## Option 2: Real Backend with SpotDL 🎵

**Use this for actual music downloads.**

### Setup:

1. **Install Python dependencies:**
```bash
pip install fastapi uvicorn pydantic spotdl
```

2. **Create `backend_real.py`:**

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import uuid
from typing import List, Optional
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

async def run_download(download_id: str, cmd: List[str]):
    """Background task to run spotdl download"""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        downloads[download_id]["process"] = process

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            downloads[download_id]["status"] = "completed"
        else:
            downloads[download_id]["status"] = "failed"
            downloads[download_id]["error"] = stderr.decode()

    except Exception as e:
        downloads[download_id]["status"] = "failed"
        downloads[download_id]["error"] = str(e)

@app.post("/api/download")
async def download(request: DownloadRequest, background_tasks: BackgroundTasks):
    download_id = str(uuid.uuid4())

    # Build spotdl command
    cmd = ["spotdl", request.query]

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

    # Add flags
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

    if request.m3u:
        cmd.extend(["--m3u", request.m3u])

    # Initialize download tracking
    downloads[download_id] = {
        "id": download_id,
        "query": request.query,
        "status": "downloading",
        "progress": 0,
        "command": " ".join(cmd),
    }

    # Start download in background
    background_tasks.add_task(run_download, download_id, cmd)

    return {
        "downloadId": download_id,
        "message": "Download started"
    }

@app.get("/api/download/{download_id}/status")
async def get_status(download_id: str):
    if download_id not in downloads:
        raise HTTPException(status_code=404, detail="Download not found")

    download = downloads[download_id]

    # TODO: Parse spotdl output for actual progress
    # For now, return basic status
    return {
        "id": download_id,
        "status": download["status"],
        "progress": 100 if download["status"] == "completed" else 50,
    }

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8800)
```

3. **Run it:**
```bash
python backend_real.py
```

---

## Option 3: Use SpotDL's Built-in Web Server

```bash
spotdl web --port 8800
```

**Note:** The built-in server may not have all the API endpoints our frontend expects. The custom backends above are recommended.

---

## Testing the Connection

1. **Start backend** (choose one option above)
2. **Start frontend:**
   ```bash
   cd spotdl-gui
   npm run dev
   ```
3. **Open browser:** http://localhost:5173
4. **Check console** - you should see no CORS errors

---

## Troubleshooting

### CORS Errors Still Appearing?

1. **Check backend is running:** Visit http://localhost:8800/api/health
2. **Check Vite proxy:** Make sure you restarted `npm run dev` after editing `vite.config.ts`
3. **Check ports:** Backend must be on 8800, frontend on 5173

### Backend Not Starting?

```bash
# Install dependencies
pip install -r requirements.txt

# Check if port 8800 is available
# On Windows:
netstat -ano | findstr :8800

# On Linux/Mac:
lsof -i :8800
```

---

## Production Deployment

For production, you'll need to:

1. Build the frontend: `npm run build`
2. Serve the `dist/` folder with nginx or similar
3. Run the backend as a systemd service or with gunicorn
4. Update CORS origins to your production domain
5. Use environment variables for configuration
