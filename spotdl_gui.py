#!/usr/bin/env python3
"""
SpotDL Desktop GUI
A modern desktop interface for SpotDL
"""

import customtkinter as ctk
import subprocess
import threading
import os
import json
from pathlib import Path
from tkinter import filedialog, messagebox
import sys
from datetime import datetime

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class SpotDLGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Config file location
        self.config_file = Path.home() / ".spotdl_gui_config.json"

        # Window setup
        self.title("SpotDL GUI")
        self.geometry("1100x750")

        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        # Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="🎵 SpotDL GUI",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Sidebar buttons
        self.btn_download = ctk.CTkButton(
            self.sidebar,
            text="Download",
            command=lambda: self.show_frame("download")
        )
        self.btn_download.grid(row=1, column=0, padx=20, pady=10)

        self.btn_queue = ctk.CTkButton(
            self.sidebar,
            text="Queue",
            command=lambda: self.show_frame("queue")
        )
        self.btn_queue.grid(row=2, column=0, padx=20, pady=10)

        self.btn_settings = ctk.CTkButton(
            self.sidebar,
            text="Settings",
            command=lambda: self.show_frame("settings")
        )
        self.btn_settings.grid(row=3, column=0, padx=20, pady=10)

        # Theme switch
        self.theme_label = ctk.CTkLabel(self.sidebar, text="Theme:")
        self.theme_label.grid(row=7, column=0, padx=20, pady=(10, 0))

        self.theme_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Dark Mode",
            command=self.toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.grid(row=8, column=0, padx=20, pady=(0, 20))
        self.theme_switch.select()

        # Main content area
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Load settings first
        self.load_settings()

        # Initialize frames
        self.frames = {}
        self.create_download_frame()
        self.create_queue_frame()
        self.create_settings_frame()

        # Download queue
        self.download_queue = []
        self.current_process = None

        # Show download frame by default
        self.show_frame("download")

        # Check SpotDL
        self.check_spotdl()

        # Save settings on close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_settings(self):
        """Load settings from config file"""
        default_settings = {
            "format": "mp3",
            "bitrate": "320k",
            "threads": "4",
            "output": "{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}",
            "audio_providers": ["youtube-music", "youtube"],
            "lyrics_providers": ["genius", "musixmatch"],
            "download_folder": str(Path.home() / "Music"),
            "theme": "dark",
            "create_folder_per_url": False,
            "organize_playlists": True
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.settings = {**default_settings, **json.load(f)}
            except:
                self.settings = default_settings
        else:
            self.settings = default_settings

    def save_settings(self):
        """Save settings to config file"""
        try:
            # Update settings from UI
            self.settings["format"] = self.format_var.get()
            self.settings["bitrate"] = self.bitrate_var.get()
            self.settings["threads"] = self.threads_var.get()
            self.settings["output"] = self.template_entry.get()
            self.settings["download_folder"] = self.folder_entry.get()
            self.settings["theme"] = "dark" if self.theme_switch.get() == "dark" else "light"
            self.settings["create_folder_per_url"] = self.folder_per_url_var.get()
            self.settings["organize_playlists"] = self.organize_playlists_var.get()

            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)

            self.log_to_queue(f"✅ Settings saved to {self.config_file}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def on_closing(self):
        """Handle window close event"""
        self.save_settings()
        self.destroy()

    def check_spotdl(self):
        """Check if SpotDL is installed"""
        try:
            result = subprocess.run(
                ["spotdl", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.logo_label.configure(text=f"🎵 SpotDL GUI\n{version}")
        except:
            messagebox.showwarning(
                "SpotDL Not Found",
                "SpotDL is not installed or not in PATH.\n\n"
                "Install it with: pip install spotdl"
            )

    def is_playlist(self, url_or_query):
        """Detect if the URL/query is a playlist"""
        url_lower = url_or_query.lower()

        # Spotify playlists
        if "spotify.com/playlist" in url_lower:
            return True

        # YouTube playlists
        if "youtube.com/playlist" in url_lower or "list=" in url_lower:
            return True

        # Special Spotify queries that are playlists
        playlist_queries = [
            "all-user-playlists",
            "all-saved-playlists"
        ]
        if url_or_query.strip() in playlist_queries:
            return True

        return False

    def is_album(self, url_or_query):
        """Detect if the URL/query is an album"""
        url_lower = url_or_query.lower()

        # Spotify albums
        if "spotify.com/album" in url_lower:
            return True

        # Special Spotify query for saved albums
        if url_or_query.strip() == "all-user-saved-albums":
            return True

        return False

    def get_content_type(self, url_or_query):
        """Determine the content type (playlist, album, track, etc.)"""
        if self.is_playlist(url_or_query):
            return "playlist"
        elif self.is_album(url_or_query):
            return "album"
        elif "spotify.com/track" in url_or_query.lower():
            return "track"
        elif "spotify.com/artist" in url_or_query.lower():
            return "artist"
        elif "all-user-followed-artists" in url_or_query:
            return "artists"
        elif url_or_query.strip() == "saved":
            return "liked_songs"
        elif "youtube.com/watch" in url_or_query.lower() or "youtu.be" in url_or_query.lower():
            return "video"
        else:
            return "unknown"

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        if self.theme_switch.get() == "dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def show_frame(self, frame_name):
        """Show the specified frame"""
        for name, frame in self.frames.items():
            if name == frame_name:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

    def create_download_frame(self):
        """Create the download tab"""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        self.frames["download"] = frame

        # Title
        title = ctk.CTkLabel(
            frame,
            text="Download Music",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="w")

        # URL Input
        url_label = ctk.CTkLabel(frame, text="Spotify/YouTube URL or Query:")
        url_label.grid(row=1, column=0, sticky="w", pady=(0, 5))

        self.url_entry = ctk.CTkEntry(
            frame,
            placeholder_text="https://open.spotify.com/track/...",
            height=40
        )
        self.url_entry.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # Playlist name input (optional)
        playlist_name_label = ctk.CTkLabel(
            frame,
            text="Playlist Folder Name (optional - leave blank for auto):",
            font=ctk.CTkFont(size=11)
        )
        playlist_name_label.grid(row=3, column=0, sticky="w", pady=(5, 5))

        self.playlist_name_entry = ctk.CTkEntry(
            frame,
            placeholder_text="e.g., 'My Favorite Songs' or leave blank for auto-detect",
            height=35
        )
        self.playlist_name_entry.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        # Quick buttons
        quick_frame = ctk.CTkFrame(frame, fg_color="transparent")
        quick_frame.grid(row=5, column=0, sticky="ew", pady=(0, 20))

        quick_label = ctk.CTkLabel(quick_frame, text="Quick select:")
        quick_label.grid(row=0, column=0, padx=(0, 10))

        quick_options = [
            ("Liked Songs", "saved"),
            ("All Playlists", "all-user-playlists"),
            ("Followed Artists", "all-user-followed-artists"),
        ]

        for i, (label, value) in enumerate(quick_options):
            btn = ctk.CTkButton(
                quick_frame,
                text=label,
                width=120,
                height=28,
                command=lambda v=value: self.url_entry.insert(0, v)
            )
            btn.grid(row=0, column=i+1, padx=5)

        # Options
        options_frame = ctk.CTkFrame(frame)
        options_frame.grid(row=6, column=0, sticky="ew", pady=(0, 20))
        options_frame.grid_columnconfigure((0, 1), weight=1)

        # Format
        format_label = ctk.CTkLabel(options_frame, text="Format:")
        format_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.format_var = ctk.StringVar(value=self.settings.get("format", "mp3"))
        format_menu = ctk.CTkOptionMenu(
            options_frame,
            variable=self.format_var,
            values=["mp3", "flac", "ogg", "opus", "m4a", "wav"]
        )
        format_menu.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # Bitrate
        bitrate_label = ctk.CTkLabel(options_frame, text="Bitrate:")
        bitrate_label.grid(row=0, column=1, sticky="w", padx=10, pady=(10, 5))

        self.bitrate_var = ctk.StringVar(value=self.settings.get("bitrate", "320k"))
        bitrate_menu = ctk.CTkOptionMenu(
            options_frame,
            variable=self.bitrate_var,
            values=["auto", "320k", "256k", "192k", "128k", "96k"]
        )
        bitrate_menu.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 10))

        # Advanced options
        advanced_frame = ctk.CTkFrame(frame)
        advanced_frame.grid(row=7, column=0, sticky="ew", pady=(0, 20))
        advanced_frame.grid_columnconfigure((0, 1, 2), weight=1)

        adv_label = ctk.CTkLabel(
            advanced_frame,
            text="Advanced Options:",
            font=ctk.CTkFont(weight="bold")
        )
        adv_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10)

        self.preload_var = ctk.BooleanVar()
        preload_check = ctk.CTkCheckBox(
            advanced_frame,
            text="Preload URLs",
            variable=self.preload_var
        )
        preload_check.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.sponsor_block_var = ctk.BooleanVar()
        sponsor_check = ctk.CTkCheckBox(
            advanced_frame,
            text="Skip Sponsors",
            variable=self.sponsor_block_var
        )
        sponsor_check.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        self.skip_explicit_var = ctk.BooleanVar()
        explicit_check = ctk.CTkCheckBox(
            advanced_frame,
            text="Skip Explicit",
            variable=self.skip_explicit_var
        )
        explicit_check.grid(row=1, column=2, sticky="w", padx=10, pady=5)

        self.generate_lrc_var = ctk.BooleanVar()
        lrc_check = ctk.CTkCheckBox(
            advanced_frame,
            text="Generate LRC",
            variable=self.generate_lrc_var
        )
        lrc_check.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.playlist_numbering_var = ctk.BooleanVar()
        numbering_check = ctk.CTkCheckBox(
            advanced_frame,
            text="Playlist Numbering",
            variable=self.playlist_numbering_var
        )
        numbering_check.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        self.folder_per_url_var = ctk.BooleanVar(
            value=self.settings.get("create_folder_per_url", False)
        )
        folder_per_url_check = ctk.CTkCheckBox(
            advanced_frame,
            text="Folder per URL",
            variable=self.folder_per_url_var
        )
        folder_per_url_check.grid(row=2, column=2, sticky="w", padx=10, pady=5)

        self.organize_playlists_var = ctk.BooleanVar(
            value=self.settings.get("organize_playlists", True)
        )
        organize_playlists_check = ctk.CTkCheckBox(
            advanced_frame,
            text="Organize Playlists",
            variable=self.organize_playlists_var
        )
        organize_playlists_check.grid(row=3, column=0, sticky="w", padx=10, pady=(5, 10))

        # Buttons frame
        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.grid(row=8, column=0, sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=3)
        buttons_frame.grid_columnconfigure(1, weight=1)

        # Download button
        self.download_btn = ctk.CTkButton(
            buttons_frame,
            text="⬇️ Download",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_download
        )
        self.download_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Open folder button
        self.open_folder_btn = ctk.CTkButton(
            buttons_frame,
            text="📁 Open Folder",
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.open_download_folder,
            fg_color="gray40",
            hover_color="gray30"
        )
        self.open_folder_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def create_queue_frame(self):
        """Create the queue tab"""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        self.frames["queue"] = frame

        # Title
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header_frame,
            text="Download Queue & Output",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")

        # Clear button
        clear_btn = ctk.CTkButton(
            header_frame,
            text="Clear Queue",
            width=120,
            command=self.clear_queue
        )
        clear_btn.grid(row=0, column=1, padx=(10, 0))

        # Queue list (now with real-time output)
        self.queue_textbox = ctk.CTkTextbox(
            frame,
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.queue_textbox.grid(row=1, column=0, sticky="nsew")

    def create_settings_frame(self):
        """Create the settings tab"""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        self.frames["settings"] = frame

        # Title
        title = ctk.CTkLabel(
            frame,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Download folder
        folder_frame = ctk.CTkFrame(frame)
        folder_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        folder_frame.grid_columnconfigure(1, weight=1)

        folder_label = ctk.CTkLabel(
            folder_frame,
            text="Base Download Folder:",
            font=ctk.CTkFont(weight="bold")
        )
        folder_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w", columnspan=3)

        folder_label2 = ctk.CTkLabel(folder_frame, text="Folder:")
        folder_label2.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.folder_entry = ctk.CTkEntry(folder_frame)
        self.folder_entry.insert(0, self.settings.get("download_folder", str(Path.home() / "Music")))
        self.folder_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        browse_btn = ctk.CTkButton(
            folder_frame,
            text="Browse",
            width=100,
            command=self.browse_folder
        )
        browse_btn.grid(row=1, column=2, padx=10, pady=5)

        open_folder_btn = ctk.CTkButton(
            folder_frame,
            text="📁 Open Folder",
            width=100,
            command=self.open_download_folder,
            fg_color="gray40",
            hover_color="gray30"
        )
        open_folder_btn.grid(row=1, column=3, padx=(0, 10), pady=5)

        # Output template
        template_frame = ctk.CTkFrame(frame)
        template_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        template_frame.grid_columnconfigure(0, weight=1)

        template_label = ctk.CTkLabel(
            template_frame,
            text="Output Folder & File Structure:",
            font=ctk.CTkFont(weight="bold")
        )
        template_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.template_entry = ctk.CTkEntry(template_frame)
        self.template_entry.insert(0, self.settings.get("output", "{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}"))
        self.template_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))

        # Template help
        help_text = ctk.CTkLabel(
            template_frame,
            text="💡 This creates folders AND filenames. Use / for folders.",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        help_text.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 5))

        # Template examples
        examples_label = ctk.CTkLabel(
            template_frame,
            text="Examples:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray"
        )
        examples_label.grid(row=3, column=0, sticky="w", padx=10, pady=(5, 2))

        example1 = ctk.CTkLabel(
            template_frame,
            text="• {album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        )
        example1.grid(row=4, column=0, sticky="w", padx=20, pady=1)

        example2 = ctk.CTkLabel(
            template_frame,
            text="• {artist}/{album}/{title}.{output-ext}",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        )
        example2.grid(row=5, column=0, sticky="w", padx=20, pady=1)

        example3 = ctk.CTkLabel(
            template_frame,
            text="• {artists} - {title}.{output-ext}  (flat structure, no folders)",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        )
        example3.grid(row=6, column=0, sticky="w", padx=20, pady=(1, 5))

        variables_label = ctk.CTkLabel(
            template_frame,
            text="Variables: {title}, {artist}, {artists}, {album}, {album-artist}, {year}, {track-number}, {disc-number}, {genre}, {output-ext}",
            text_color="gray",
            font=ctk.CTkFont(size=9)
        )
        variables_label.grid(row=7, column=0, sticky="w", padx=10, pady=(0, 10))

        # Threads
        threads_frame = ctk.CTkFrame(frame)
        threads_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))

        threads_label = ctk.CTkLabel(threads_frame, text="Concurrent Downloads:")
        threads_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.threads_var = ctk.StringVar(value=self.settings.get("threads", "4"))
        threads_slider = ctk.CTkSlider(
            threads_frame,
            from_=1,
            to=16,
            number_of_steps=15,
            command=lambda v: self.threads_var.set(str(int(v)))
        )
        threads_slider.set(int(self.settings.get("threads", "4")))
        threads_slider.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        threads_value = ctk.CTkLabel(threads_frame, textvariable=self.threads_var)
        threads_value.grid(row=0, column=2, padx=10, pady=10)

        # Save settings button
        save_btn = ctk.CTkButton(
            frame,
            text="💾 Save Settings",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.save_settings
        )
        save_btn.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        # Config file location
        config_label = ctk.CTkLabel(
            frame,
            text=f"Config saved to: {self.config_file}",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        )
        config_label.grid(row=5, column=0, sticky="w")

    def browse_folder(self):
        """Browse for download folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)

    def open_download_folder(self):
        """Open the download folder in system file explorer"""
        folder = self.folder_entry.get()

        if not os.path.exists(folder):
            messagebox.showwarning(
                "Folder Not Found",
                f"The folder doesn't exist yet:\n{folder}\n\nIt will be created when you download something."
            )
            return

        try:
            # Windows
            if sys.platform == "win32":
                os.startfile(folder)
            # macOS
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            # Linux
            else:
                subprocess.run(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder:\n{str(e)}")

    def log_to_queue(self, message):
        """Add a message to the queue display"""
        self.queue_textbox.configure(state="normal")
        self.queue_textbox.insert("end", message)
        self.queue_textbox.configure(state="disabled")
        self.queue_textbox.see("end")

    def start_download(self):
        """Start a download"""
        query = self.url_entry.get().strip()

        if not query:
            messagebox.showwarning("No URL", "Please enter a Spotify or YouTube URL")
            return

        # Build command
        cmd = ["spotdl", query]

        # Add options
        cmd.extend(["--format", self.format_var.get()])
        cmd.extend(["--bitrate", self.bitrate_var.get()])
        cmd.extend(["--threads", self.threads_var.get()])
        cmd.extend(["--output", self.template_entry.get()])

        # Add flags
        if self.preload_var.get():
            cmd.append("--preload")
        if self.sponsor_block_var.get():
            cmd.append("--sponsor-block")
        if self.skip_explicit_var.get():
            cmd.append("--skip-explicit")
        if self.generate_lrc_var.get():
            cmd.append("--generate-lrc")
        if self.playlist_numbering_var.get():
            cmd.append("--playlist-numbering")

        # Determine download folder
        download_folder = self.folder_entry.get()

        # Check if this is a playlist
        is_playlist_url = self.is_playlist(query)

        # Handle playlist organization
        if is_playlist_url and self.organize_playlists_var.get():
            # Get custom playlist name or auto-generate
            custom_name = self.playlist_name_entry.get().strip()

            if custom_name:
                # Use custom name
                playlist_folder = self.sanitize_folder_name(custom_name)
            else:
                # Auto-generate from URL
                playlist_folder = self.sanitize_folder_name(query)

            # Create Playlists/{playlist-name} structure
            download_folder = os.path.join(download_folder, "Playlists", playlist_folder)
            os.makedirs(download_folder, exist_ok=True)

        # If "folder per URL" is enabled (for non-playlists or when playlist organization is off)
        elif self.folder_per_url_var.get():
            # Create folder name from URL/query
            folder_name = self.sanitize_folder_name(query)
            download_folder = os.path.join(download_folder, folder_name)
            os.makedirs(download_folder, exist_ok=True)

        # Log start with content type
        timestamp = datetime.now().strftime("%H:%M:%S")
        content_type = self.get_content_type(query)
        type_icons = {
            "playlist": "📃",
            "album": "💿",
            "track": "🎵",
            "artist": "🎤",
            "artists": "🎤",
            "liked_songs": "❤️",
            "video": "📹",
            "unknown": "📥"
        }
        icon = type_icons.get(content_type, "📥")

        self.log_to_queue(f"\n{'='*60}\n")
        self.log_to_queue(f"[{timestamp}] {icon} Starting download ({content_type})\n")
        self.log_to_queue(f"Query: {query}\n")
        self.log_to_queue(f"Folder: {download_folder}\n")
        self.log_to_queue(f"Command: {' '.join(cmd)}\n")
        self.log_to_queue(f"{'='*60}\n\n")

        # Clear inputs
        self.url_entry.delete(0, "end")
        self.playlist_name_entry.delete(0, "end")

        # Switch to queue tab
        self.show_frame("queue")

        # Start download in thread
        threading.Thread(
            target=self.run_download,
            args=(cmd, download_folder, query),
            daemon=True
        ).start()

    def sanitize_folder_name(self, url_or_query):
        """Create a safe folder name from URL or query"""
        # Handle special Spotify queries
        special_queries = {
            "saved": "Liked Songs",
            "all-user-playlists": "All My Playlists",
            "all-saved-playlists": "My Saved Playlists",
            "all-user-followed-artists": "Followed Artists",
            "all-user-saved-albums": "Saved Albums"
        }

        if url_or_query in special_queries:
            return special_queries[url_or_query]

        # Extract meaningful part from URL
        if "spotify.com/playlist" in url_or_query:
            # For Spotify playlists, use the playlist ID
            parts = url_or_query.split("/")
            if len(parts) >= 2:
                playlist_id = parts[-1].split("?")[0][:12]  # Get ID, remove query params
                return f"Spotify_Playlist_{playlist_id}"

        elif "spotify.com" in url_or_query:
            # For other Spotify URLs
            parts = url_or_query.split("/")
            if len(parts) >= 2:
                return f"Spotify_{parts[-2]}_{parts[-1][:8]}"

        elif "youtube.com/playlist" in url_or_query:
            # YouTube playlist
            list_id = url_or_query.split("list=")[-1].split("&")[0][:12]
            return f"YouTube_Playlist_{list_id}"

        elif "youtube.com" in url_or_query or "youtu.be" in url_or_query:
            # YouTube video
            return f"YouTube_{url_or_query.split('=')[-1][:8]}"

        # For other queries, just sanitize
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in url_or_query)
        return safe_name[:50]  # Limit length

    def run_download(self, cmd, download_folder, query):
        """Run spotdl command in background with real-time output"""
        try:
            os.makedirs(download_folder, exist_ok=True)

            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True,
                bufsize=1,  # Line buffered
                cwd=download_folder
            )

            # Read output line by line in real-time
            for line in process.stdout:
                self.log_to_queue(line)

            # Wait for completion
            process.wait()

            # Log completion
            timestamp = datetime.now().strftime("%H:%M:%S")
            if process.returncode == 0:
                self.log_to_queue(f"\n[{timestamp}] ✅ Download completed successfully!\n")
                self.log_to_queue(f"📁 Files saved to: {download_folder}\n")
            else:
                self.log_to_queue(f"\n[{timestamp}] ❌ Download failed with exit code {process.returncode}\n")

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_to_queue(f"\n[{timestamp}] ❌ Error: {str(e)}\n")

    def clear_queue(self):
        """Clear the queue display"""
        self.queue_textbox.configure(state="normal")
        self.queue_textbox.delete("1.0", "end")
        self.queue_textbox.configure(state="disabled")


def main():
    app = SpotDLGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
