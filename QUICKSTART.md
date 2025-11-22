# 🎵 SpotDL Desktop GUI - Quick Start

A beautiful Python desktop app for SpotDL. No browser needed!

## 🚀 Super Quick Start

### 1. Install
```bash
pip install customtkinter
```

### 2. Run
```bash
python spotdl_gui.py
```

**That's it!** 🎉

---

## 📸 What You Get

- 🎨 **Beautiful modern interface** (dark/light themes)
- 📥 **Download tab** - Paste URLs, configure quality, download
- 📊 **Queue tab** - Real-time SpotDL output with progress
- ⚙️ **Settings tab** - Customize everything, auto-saves

---

## 🎯 Quick Example

1. **Run:** `python spotdl_gui.py`
2. **Paste:** Any Spotify or YouTube URL
3. **Click:** ⬇️ Download button
4. **Watch:** Real-time output in Queue tab
5. **Done:** Click 📁 Open Folder to see your music!

---

## ⚙️ Features

### **Download Tab:**
- URL input with quick shortcuts (Liked Songs, Playlists, etc.)
- Format: MP3, FLAC, OGG, Opus, M4A, WAV
- Bitrate: Auto, 320k, 256k, 192k, etc.
- Advanced: Preload, skip sponsors, generate lyrics, etc.
- **Folder per URL**: Create separate folder for each download
- **📁 Open Folder button**: Open download folder instantly

### **Queue Tab:**
- **Real-time SpotDL CLI output** - see exactly what's happening!
- Progress bars, download speeds, conversion status
- Timestamps for every action
- Monospace font for easy reading

### **Settings Tab:**
- **Base Download Folder**: Choose where music is saved
- **Output Structure**: Organize by artist/album/year
  - Default: `{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}`
  - Creates folders like: `Artist Name/2024 - Album Name/01 - Song.mp3`
- **Concurrent Downloads**: 1-16 threads
- **💾 Auto-save**: Settings saved when you close the app
- **Config file**: `~/.spotdl_gui_config.json`

---

## 🎨 Customization

### **Folder Structure Examples:**

```python
# Organized by artist → year/album → tracks (DEFAULT)
{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}
# Result: Artist Name/2024 - Album Name/01 - Song Title.mp3

# Simple: artist → album → songs
{artist}/{album}/{title}.{output-ext}
# Result: Artist Name/Album Name/Song Title.mp3

# Flat (all in one folder)
{artists} - {title}.{output-ext}
# Result: Artist Name - Song Title.mp3

# By genre
{genre}/{artist}/{album}/{title}.{output-ext}
# Result: Rock/Artist Name/Album Name/Song Title.mp3
```

### **Available Variables:**
- `{title}`, `{artist}`, `{artists}`, `{album}`, `{album-artist}`
- `{year}`, `{track-number}`, `{disc-number}`, `{genre}`
- `{output-ext}` (automatically becomes .mp3, .flac, etc.)

---

## 🎵 Supported URLs

### **Spotify:**
- Tracks: `https://open.spotify.com/track/...`
- Albums: `https://open.spotify.com/album/...`
- Playlists: `https://open.spotify.com/playlist/...`
- Artists: `https://open.spotify.com/artist/...`

### **YouTube:**
- Videos: `https://www.youtube.com/watch?v=...`
- Playlists: `https://www.youtube.com/playlist?list=...`

### **Special Spotify Queries:**
- `saved` - Your liked songs
- `all-user-playlists` - All your playlists
- `all-saved-playlists` - Playlists you created
- `all-user-followed-artists` - Artists you follow
- `all-user-saved-albums` - Albums you saved

---

## 📁 Where Are My Downloads?

**Default location:**
- **Windows**: `C:\Users\YourName\Music`
- **Mac**: `~/Music`
- **Linux**: `~/Music`

**Change it:**
1. Go to Settings tab
2. Click "Browse" to choose a new folder
3. Or edit the path directly

**Open it:**
- Click **📁 Open Folder** button (Download tab or Settings tab)

---

## 🐛 Troubleshooting

### **"SpotDL not found"**
```bash
pip install spotdl
spotdl --version
```

### **GUI doesn't open**
```bash
pip install customtkinter
```

### **Downloads not working**
1. Check Queue tab for error messages
2. Verify SpotDL is installed: `spotdl --version`
3. Check your internet connection

### **Can't find downloaded files**
1. Click **📁 Open Folder** button
2. Or check Settings → Base Download Folder

---

## 💡 Pro Tips

1. **Organize by year**: Use `{album-artist}/{year} - {album}/...`
2. **Batch download**: Paste playlist URLs
3. **High quality**: Use FLAC format + auto bitrate
4. **Watch progress**: Queue tab shows real-time output
5. **Folder per URL**: Check the box to organize each download separately

---

## 🔧 Requirements

- **Python 3.8+**
- **SpotDL**: `pip install spotdl`
- **CustomTkinter**: `pip install customtkinter`

---

## 📝 Config File

Settings auto-save to: `~/.spotdl_gui_config.json`

You can edit manually if needed!

---

**Enjoy your music!** 🎵

Need help? Check SpotDL docs: https://spotdl.rtfd.io/
