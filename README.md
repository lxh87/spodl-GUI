# 🎵 SpotDL Desktop GUI

A beautiful, modern desktop application for SpotDL - no browser needed!

![Features](https://img.shields.io/badge/Python-3.8+-blue)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey)

## ✨ Features

- 🎨 **Modern, Clean Interface** - Dark/Light theme support
- 🚀 **Simple Setup** - Just run one Python file
- 🎵 **All SpotDL Features** - Full access to all CLI options
- 📊 **Real-time Queue** - Track your downloads
- ⚙️ **Customizable** - Format, bitrate, output templates, and more
- 💻 **Cross-Platform** - Works on Windows, Mac, and Linux

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install customtkinter
```

Or install everything:
```bash
pip install -r requirements.txt
```

### 2. Run the App

```bash
python spotdl_gui.py
```

That's it! 🎉

## 📸 What It Looks Like

```
┌─────────────────────────────────────────────┐
│  🎵 SpotDL GUI          [Dark Mode] [Light] │
├──────────┬──────────────────────────────────┤
│          │  Download Music                  │
│ Download │                                  │
│ Queue    │  [Spotify/YouTube URL]           │
│ Settings │                                  │
│          │  Format: [MP3  ▼]                │
│          │  Bitrate: [320k ▼]               │
│          │                                  │
│          │  ☑ Preload  ☑ Skip Sponsors      │
│          │  ☐ Skip Explicit  ☐ Generate LRC │
│          │                                  │
│          │  [⬇️ Download]                   │
└──────────┴──────────────────────────────────┘
```

## 🎯 How to Use

### Download a Song/Playlist

1. **Paste URL** - Spotify or YouTube link
2. **Choose options** - Format, bitrate, etc.
3. **Click Download** - It starts immediately!
4. **Check Queue** - See progress in the Queue tab

### Quick Shortcuts

Use the quick buttons for:
- **Liked Songs** - Downloads all your saved tracks
- **All Playlists** - Downloads all your playlists
- **Followed Artists** - Downloads from artists you follow

### Supported URLs

- Spotify tracks, albums, playlists, artists
- YouTube videos and playlists
- Special queries: `saved`, `all-user-playlists`, etc.

## ⚙️ Settings

### Download Folder
Choose where your music is saved (default: Music folder)

### Output Template
Customize filenames using variables:
- `{artists} - {title}.{output-ext}` → "Artist - Song.mp3"
- `{album}/{track-number} - {title}.{output-ext}` → "Album/01 - Song.mp3"
- `{year}/{artist}/{album}/{title}.{output-ext}` → "2024/Artist/Album/Song.mp3"

### Available Variables
- `{title}`, `{artist}`, `{artists}`, `{album}`
- `{album-artist}`, `{genre}`, `{year}`
- `{track-number}`, `{disc-number}`
- `{isrc}`, `{publisher}`, `{output-ext}`

### Concurrent Downloads
Adjust how many songs download at once (1-16 threads)

## 🎨 Themes

Toggle between **Dark Mode** and **Light Mode** with the switch in the sidebar!

## 📋 Requirements

- **Python 3.8+**
- **SpotDL** - Install with `pip install spotdl`
- **CustomTkinter** - Install with `pip install customtkinter`

## 🔧 Advanced Features

### Preload URLs
Pre-fetch download links for faster processing

### Skip Sponsors
Use SponsorBlock to skip sponsored segments (YouTube)

### Skip Explicit
Automatically skip songs marked as explicit

### Generate LRC
Create synced lyrics files (.lrc) for music players

### Playlist Numbering
Add playlist position to track metadata

## 📁 Where Are My Downloads?

By default, downloads go to your **Music folder**:
- **Windows**: `C:\Users\YourName\Music`
- **Mac**: `~/Music`
- **Linux**: `~/Music`

You can change this in **Settings → Download Folder**

## 🐛 Troubleshooting

### "SpotDL not found"
Make sure SpotDL is installed:
```bash
pip install spotdl
spotdl --version
```

### Downloads not appearing
1. Check the **Queue** tab for errors
2. Check your **Download Folder** in Settings
3. Make sure you have write permissions to the folder

### GUI not opening
Make sure CustomTkinter is installed:
```bash
pip install customtkinter
```

## 🆚 Desktop vs Web GUI

**Desktop GUI (This)**:
- ✅ Simpler setup (one command)
- ✅ Native desktop app
- ✅ No browser needed
- ✅ Lighter weight

**Web GUI** (in `spotdl-gui/`):
- ✅ Modern web technologies
- ✅ Can run on remote server
- ✅ Access from any device
- ✅ More features (planned)

Choose what works best for you!

## 📝 Tips

1. **Batch Downloads** - Paste playlist URLs to download multiple songs
2. **Custom Templates** - Organize your library with folder structures
3. **Quality Settings** - Use FLAC for lossless, MP3 320k for high quality
4. **Spotify Login** - Configure in SpotDL config for your library access

## 🚀 Next Steps

Want even more features? Try:
- The **Web GUI** - Modern React interface (see `spotdl-gui/` folder)
- **SpotDL CLI** - Direct command-line access

## ❤️ Credits

- **SpotDL** - The amazing CLI tool that powers everything
- **CustomTkinter** - Beautiful modern GUI framework
- **You** - For using this app!

---

**Enjoy your music!** 🎵

Need help? Check the SpotDL documentation at https://spotdl.rtfd.io/
