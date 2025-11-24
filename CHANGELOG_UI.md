# UI Improvements - Command Preview & Paste Button

## Changes Made

### 1. **URL Field - Added Paste Button** 📋
- **Location**: Download tab, URL input field
- **Design**: Clipboard icon (📋) button on the right side of URL field
- **Function**: Pastes clipboard content directly into URL field
- **Behavior**: Automatically updates command preview after pasting

### 2. **Command Preview Section** 🖥️
- **Location**: Download tab, below Download/Open Folder buttons
- **Components**:
  - Label: "Command Preview:"
  - Read-only entry field showing the exact spotdl command
  - Copy button (📄) on the right side

### 3. **Command Preview Features**
- **Real-time Updates**: Updates automatically when you change:
  - URL/query
  - Format (mp3, flac, etc.)
  - Bitrate
  - Threads
  - Template (in Settings)
  - Any checkbox options (Preload, Skip Explicit, etc.)

- **Copy Functionality**:
  - Click 📄 button to copy full command
  - Visual feedback: Shows "✓" for 1 second after copying
  - Command is copied to system clipboard

- **Accurate Command**: Shows the exact command that will be executed, including:
  ```
  spotdl [URL] --format mp3 --bitrate 320k --threads 4 --output [template] [flags...]
  ```

## Visual Layout

```
┌─────────────────────────────────────────────────────────┐
│ Spotify/YouTube URL or Query:                          │
│ ┌──────────────────────────────────────────────┐ ┌───┐ │
│ │ https://open.spotify.com/track/...          │ │📋 │ │
│ └──────────────────────────────────────────────┘ └───┘ │
│                                                         │
│ [Quick Select Buttons]                                  │
│                                                         │
│ [Format/Bitrate Options]                               │
│ [Advanced Options]                                      │
│                                                         │
│ ┌──────────────────────────────┐ ┌──────────────────┐ │
│ │    ⬇️ Download                │ │  📁 Open Folder  │ │
│ └──────────────────────────────┘ └──────────────────┘ │
│                                                         │
│ Command Preview:                                        │
│ ┌──────────────────────────────────────────────┐ ┌───┐ │
│ │ spotdl [url] --format mp3 --bitrate 320k... │ │📄 │ │
│ └──────────────────────────────────────────────┘ └───┘ │
└─────────────────────────────────────────────────────────┘
```

## Design Consistency

- **Same design language** as URL field
- **Icon-only buttons** (📋 and 📄) for compact layout
- **Monospace font** for command preview (Consolas)
- **Read-only field** prevents accidental editing
- **Automatic updates** - no manual refresh needed

## Use Cases

### 1. Quick Copy-Paste Workflow
```
User: Copies Spotify URL
  ↓
Click 📋 (paste button)
  ↓
Command preview updates automatically
  ↓
Review command
  ↓
Click Download or copy command with 📄
```

### 2. Advanced Users
```
Adjust settings (format, bitrate, template)
  ↓
Watch command preview update in real-time
  ↓
Copy command with 📄
  ↓
Paste in terminal for manual execution
```

### 3. Learning Tool
```
New users can see exactly what spotdl command
will be executed based on their GUI selections
```

## Technical Details

### New Methods Added

1. **`paste_url()`**
   - Reads system clipboard
   - Inserts into URL field
   - Updates command preview

2. **`copy_command()`**
   - Copies command to clipboard
   - Shows visual confirmation (✓)
   - Resets after 1 second

3. **`update_command_preview()`**
   - Reads all current settings
   - Builds exact command string
   - Updates preview field
   - Called on any setting change

### Event Bindings

The command preview updates automatically on:
- URL field key release
- Format dropdown change
- Bitrate dropdown change
- Threads slider change
- Any checkbox toggle
- Template changes in Settings
- Save settings button click

## Benefits

✅ **Transparency**: Users see exactly what command runs
✅ **Learning**: Helps users understand spotdl CLI
✅ **Debugging**: Easy to copy and test commands manually
✅ **Convenience**: One-click paste and copy
✅ **Professional**: Matches modern CLI tool GUIs

## Future Enhancements (Optional)

- [ ] Add syntax highlighting to command preview
- [ ] Add "Edit Command" mode for advanced users
- [ ] Show output folder path in preview
- [ ] Add command history dropdown
- [ ] Export command to .bat/.sh file
