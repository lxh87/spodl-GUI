# 🚀 Quick Start Guide

## Setup (One Time Only)

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

That's it! The backend will automatically find your SpotDL installation.

---

## Running the App

### Step 1: Start Backend

```bash
python backend.py
```

You should see:
```
🎵 SpotDL GUI Backend Starting...
✅ SpotDL found at: spotdl (or C:\Windows\system32\spotdl.exe)
📍 Downloads will be saved to: C:\Users\YourName\Music
🌐 API running at: http://localhost:8800
```

### Step 2: Start Frontend (in new terminal)

```bash
cd spotdl-gui
npm run dev
```

### Step 3: Open Browser

Visit **http://localhost:5173**

---

## 🎵 Download Your First Song

1. **Paste a Spotify or YouTube URL** (e.g., `https://open.spotify.com/track/...`)
2. **Click Download**
3. **Check the Queue tab** to see progress
4. **Find your music** in `C:\Users\YourName\Music` folder

---

## ⚙️ Where Downloads Are Saved

By default, downloads go to your **Music folder**:
- **Windows**: `C:\Users\YourName\Music`
- **Mac/Linux**: `~/Music`

You can change this by editing the output template in the **Settings** page or using the **output template** in the Download page.

---

## 🎛️ Customize Your Downloads

### In the GUI:

1. **Format**: Choose MP3, FLAC, OGG, etc.
2. **Bitrate**: Select quality (320k recommended)
3. **Providers**: Pick audio sources (YouTube Music, SoundCloud, etc.)
4. **Output Template**: Customize filenames (default: `{artists} - {title}.{output-ext}`)

### Example Templates:

- `{artists} - {title}.{output-ext}` → "Artist Name - Song Title.mp3"
- `{album}/{track-number} - {title}.{output-ext}` → "Album Name/01 - Song Title.mp3"
- `Music/{year}/{artist}/{album}/{title}.{output-ext}` → "Music/2024/Artist/Album/Song.mp3"

---

## 🔍 What URLs Work?

### Spotify:
- **Track**: `https://open.spotify.com/track/...`
- **Album**: `https://open.spotify.com/album/...`
- **Playlist**: `https://open.spotify.com/playlist/...`
- **Artist**: `https://open.spotify.com/artist/...`

### YouTube:
- **Video**: `https://www.youtube.com/watch?v=...`
- **Playlist**: `https://www.youtube.com/playlist?list=...`

### Special Spotify Queries:
- `saved` - Your liked songs
- `all-user-playlists` - All your playlists
- `all-saved-playlists` - Playlists you created
- `all-user-followed-artists` - Artists you follow
- `all-user-saved-albums` - Albums you saved

---

## ❓ Troubleshooting

### "SpotDL not found"
- Make sure SpotDL is installed: `spotdl --version`
- If in `C:\Windows\system32`, the backend will find it automatically

### CORS Errors
- Make sure you restarted `npm run dev` after the first setup
- Backend must be running on port 8800

### Downloads Not Appearing
- Check the backend terminal for error messages
- Check `C:\Users\YourName\Music` folder
- Look at the Queue tab in the GUI for status

---

## 🛑 Stopping the App

1. **Stop Frontend**: Press `Ctrl+C` in the terminal running `npm run dev`
2. **Stop Backend**: Press `Ctrl+C` in the terminal running `python backend.py`

---

## 📝 Next Steps

- Configure **Spotify credentials** in Settings for access to your library
- Try **batch downloads** by pasting playlist URLs
- Customize **output templates** for organized music folders
- Enable **lyrics download** with synced lyrics

Enjoy your music! 🎵
