# SpotDL GUI - Phase 1 (MVP)

A modern, user-friendly web interface for [SpotDL](https://github.com/spotDL/spotify-downloader) - Download music from Spotify & YouTube with metadata.

![Tech Stack](https://img.shields.io/badge/React-18-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Tailwind](https://img.shields.io/badge/Tailwind-3-blue)
![Vite](https://img.shields.io/badge/Vite-5-purple)

## Features (Phase 1 - MVP)

- **Download Interface**: Clean URL input with support for Spotify/YouTube URLs and special queries
- **Provider Selection**: Choose audio (YouTube, YouTube Music, SoundCloud, etc.) and lyrics providers
- **Quality Settings**: Configure format (MP3, FLAC, etc.), bitrate, threads, and output templates
- **Download Queue**: Real-time progress tracking with visual feedback
- **Advanced Options**: Preload, sponsor block, skip explicit, and more
- **Settings Management**: Spotify authentication and persistent configuration
- **Dark/Light Theme**: Automatic theme switching based on system preference

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Axios** - HTTP client
- **Lucide React** - Icons

## Prerequisites

- Node.js 18+ and npm
- SpotDL installed (preferably in `C:\Windows\system32` on Windows or available in PATH)
- A backend API server (see Backend Setup below)

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` to set your backend API URL:

```env
VITE_API_URL=http://localhost:8800/api
```

### 3. Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### 4. Build for Production

```bash
npm run build
```

Built files will be in the `dist/` directory.

## Backend Setup

This frontend requires a backend API to communicate with SpotDL. You have several options:

### Option 1: Use SpotDL's Built-in Web Server

```bash
spotdl web --port 8800
```

**Note**: The built-in web server may have limited API endpoints. For full functionality, use Option 2.

### Option 2: Create a Custom Backend (Recommended)

Create a simple Python FastAPI/Flask server that wraps SpotDL CLI commands. Example structure:

```python
# backend.py (FastAPI example)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/download")
async def download(options: dict):
    # Build spotdl command from options
    # Execute subprocess
    # Return download ID
    pass

@app.get("/api/download/{download_id}/status")
async def get_status(download_id: str):
    # Return download progress
    pass
```

Run with:

```bash
uvicorn backend:app --port 8800
```

## Project Structure

```
src/
├── components/
│   ├── common/          # Reusable UI components (Button, Input, Select)
│   ├── download/        # Download-specific components
│   ├── layout/          # Layout components (Header, Sidebar)
│   └── queue/           # Queue management components
├── pages/               # Main page components
├── services/            # API service layer
├── store/              # Zustand state management
├── types/              # TypeScript type definitions
└── lib/                # Utilities
```

## Configuration

### Download Options

All download options are configurable through the UI and persist in localStorage:

- **Audio Format**: MP3, FLAC, OGG, Opus, M4A, WAV
- **Bitrate**: Auto, 320k, VBR 0-9, etc.
- **Providers**: Multiple audio and lyrics providers with priority ordering
- **Output Template**: Customizable filename format using variables like `{artist}`, `{title}`, etc.

### Spotify Authentication

Configure in Settings page:

- OAuth login (recommended)
- Manual Client ID/Secret
- Direct authorization token

Get credentials from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

## Supported URL Formats

- **Spotify**: Track, Album, Playlist, Artist URLs
- **YouTube**: Video, Playlist URLs
- **Special Queries**:
  - `saved` - Your liked songs
  - `all-user-playlists` - All user playlists
  - `all-saved-playlists` - Created playlists only
  - `all-user-followed-artists` - Followed artists
  - `all-user-saved-albums` - Saved albums
- **Search Queries**: Use prefixes `album:`, `playlist:`, `artist:`
- **Manual Matching**: `YouTubeURL|SpotifyURL`

## Keyboard Shortcuts

- `Ctrl+V` in search input - Paste and focus
- Theme toggle via header button

## Roadmap

### Phase 2 (Upcoming)
- Sync functionality
- Metadata editor
- Enhanced error handling
- Batch operations

### Phase 3
- Playlist manager
- Archive management
- Advanced filters

### Phase 4
- Drag & drop support
- Custom keyboard shortcuts
- Logs viewer
- Performance optimizations

## Contributing

This is a work in progress. Contributions welcome!

## License

MIT License - see LICENSE file for details

## Credits

- [SpotDL](https://github.com/spotDL/spotify-downloader) - The amazing CLI tool this GUI wraps
- Built with love using React, TypeScript, and Tailwind CSS

---

**Note**: This is Phase 1 (MVP). More features coming soon!
