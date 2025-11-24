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

# Import our enhanced metadata handler
from metadata_handler import SpotifyMetadataHandler

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class SpotDLGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Config file location
        self.config_file = Path.home() / ".spotdl_gui_config.json"

        # Initialize metadata handler (works with pip, source, or spotdl.exe)
        self.metadata_handler = SpotifyMetadataHandler()

        # Window setup
        self.title("SpotDL GUI")
        self.geometry("1100x850")

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

        # Initialize command preview
        self.update_command_preview()

        # Check SpotDL
        self.check_spotdl()

        # Save settings on close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_settings(self):
        """Load settings from config file"""
        default_settings = {
            "format": "mp3",
            "bitrate": "320k",
            "playlist_output": "{list-name}/{list-position} - {artists} - {title}.{output-ext}",
            "threads": "4",
            "output": "{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}",
            "audio_providers": ["youtube-music", "youtube"],
            "lyrics_providers": ["genius", "musixmatch"],
            "download_folder": str(Path.home() / "Music"),
            "theme": "dark",
            "create_folder_per_url": True,
            "playlist_folder_name": ""
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
            self.settings["playlist_output"] = self.playlist_template_entry.get()
            self.settings["download_folder"] = self.folder_entry.get()
            self.settings["theme"] = "dark" if self.theme_switch.get() == "dark" else "light"
            self.settings["create_folder_per_url"] = self.folder_per_url_var.get()

            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)

            self.log_to_queue(f"✅ Settings saved to {self.config_file}\n")

            # Update command preview with new settings
            self.update_command_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def on_closing(self):
        """Handle window close event"""
        self.save_settings()
        self.destroy()

    def check_spotdl(self):
        """Check if SpotDL is installed (initial check)"""
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
                "Install it with: pip install spotdl\n"
                "Or use the Install button in Settings."
            )

    def check_spotdl_installation(self):
        """Check SpotDL installation status"""
        try:
            result = subprocess.run(
                ["spotdl", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.spotdl_status_label.configure(
                    text=f"✅ SpotDL is installed: {version}",
                    text_color="#4CAF50"
                )
                self.logo_label.configure(text=f"🎵 SpotDL GUI\n{version}")
                return True
            else:
                self.spotdl_status_label.configure(
                    text="❌ SpotDL is not working correctly",
                    text_color="#f44336"
                )
                return False
        except FileNotFoundError:
            self.spotdl_status_label.configure(
                text="❌ SpotDL is not installed",
                text_color="#f44336"
            )
            return False
        except Exception as e:
            self.spotdl_status_label.configure(
                text=f"❌ Error checking SpotDL: {str(e)}",
                text_color="#f44336"
            )
            return False

    def install_spotdl(self):
        """Install SpotDL using pip"""
        def install_thread():
            try:
                self.spotdl_status_label.configure(
                    text="⏳ Installing SpotDL...",
                    text_color="#FF9800"
                )

                # Run pip install
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "spotdl"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    self.spotdl_status_label.configure(
                        text="✅ SpotDL installed successfully!",
                        text_color="#4CAF50"
                    )
                    # Recheck installation
                    self.after(1000, self.check_spotdl_installation)
                else:
                    self.spotdl_status_label.configure(
                        text=f"❌ Installation failed: {result.stderr[:100]}",
                        text_color="#f44336"
                    )
            except subprocess.TimeoutExpired:
                self.spotdl_status_label.configure(
                    text="❌ Installation timed out",
                    text_color="#f44336"
                )
            except Exception as e:
                self.spotdl_status_label.configure(
                    text=f"❌ Installation error: {str(e)}",
                    text_color="#f44336"
                )

        # Run installation in a thread
        threading.Thread(target=install_thread, daemon=True).start()

    def is_playlist(self, url_or_query):
        """Detect if the URL/query is a playlist"""
        url_lower = url_or_query.lower()

        # Spotify playlists (handle international URLs like intl-de)
        if "spotify.com" in url_lower and "/playlist/" in url_lower:
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

        # Spotify albums (handle international URLs like intl-de)
        if "spotify.com" in url_lower and "/album/" in url_lower:
            return True

        # Special Spotify query for saved albums
        if url_or_query.strip() == "all-user-saved-albums":
            return True

        return False

    def get_content_type(self, url_or_query):
        """Determine the content type (playlist, album, track, etc.)"""
        url_lower = url_or_query.lower()

        if self.is_playlist(url_or_query):
            return "playlist"
        elif self.is_album(url_or_query):
            return "album"
        elif "spotify.com" in url_lower and "/track/" in url_lower:
            return "track"
        elif "spotify.com" in url_lower and "/artist/" in url_lower:
            return "artist"
        elif "all-user-followed-artists" in url_or_query:
            return "artists"
        elif url_or_query.strip() == "saved":
            return "liked_songs"
        elif "youtube.com/watch" in url_or_query.lower() or "youtu.be" in url_or_query.lower():
            return "video"
        else:
            return "unknown"

    def generate_example_output(self, template):
        """Generate example output from template using consistent example data"""
        # Consistent example data (always the same)
        example_data = {
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "artists": "The Weeknd",
            "album": "After Hours",
            "album-artist": "The Weeknd",
            "genre": "Synth-pop",
            "year": "2020",
            "track-number": "03",
            "disc-number": "1",
            "isrc": "USUG11902768",
            "publisher": "Republic Records",
            "output-ext": "mp3"
        }

        try:
            # Replace all variables with example data
            result = template
            for key, value in example_data.items():
                result = result.replace(f"{{{key}}}", value)
            return result
        except:
            return template

    def update_template_example(self, *args):
        """Update the example output when template changes"""
        template = self.template_entry.get()
        example = self.generate_example_output(template)
        self.example_output_label.configure(text=f"Preview: {example}")

    def generate_playlist_example_output(self, template):
        """Generate example output for playlist template using consistent example data"""
        # Consistent playlist example data
        example_data = {
            "list-name": "My Awesome Playlist",
            "list-position": "05",
            "list-length": "50",
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "artists": "The Weeknd",
            "album": "After Hours",
            "album-artist": "The Weeknd",
            "genre": "Synth-pop",
            "year": "2020",
            "track-number": "03",
            "disc-number": "1",
            "output-ext": "mp3"
        }

        try:
            # Replace all variables with example data
            result = template
            for key, value in example_data.items():
                result = result.replace(f"{{{key}}}", value)
            return result
        except:
            return template

    def update_playlist_template_example(self, *args):
        """Update the playlist template example output when template changes"""
        template = self.playlist_template_entry.get()
        example = self.generate_playlist_example_output(template)
        self.playlist_example_output_label.configure(text=f"Preview: {example}")

    def insert_tag_template(self, tag):
        """Insert tag at cursor position in template entry"""
        import tkinter as tk
        current_pos = self.template_entry.index(tk.INSERT)
        current_text = self.template_entry.get()
        new_text = current_text[:current_pos] + tag + current_text[current_pos:]
        self.template_entry.delete(0, tk.END)
        self.template_entry.insert(0, new_text)
        self.template_entry.icursor(current_pos + len(tag))
        self.update_template_example()

    def insert_tag_playlist_template(self, tag):
        """Insert tag at cursor position in playlist template entry"""
        import tkinter as tk
        current_pos = self.playlist_template_entry.index(tk.INSERT)
        current_text = self.playlist_template_entry.get()
        new_text = current_text[:current_pos] + tag + current_text[current_pos:]
        self.playlist_template_entry.delete(0, tk.END)
        self.playlist_template_entry.insert(0, new_text)
        self.playlist_template_entry.icursor(current_pos + len(tag))
        self.update_playlist_template_example()

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

        # URL input frame with paste button
        url_input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        url_input_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        url_input_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            url_input_frame,
            placeholder_text="https://open.spotify.com/track/...",
            height=40
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Paste button
        paste_btn = ctk.CTkButton(
            url_input_frame,
            text="📋",
            width=40,
            height=40,
            command=self.paste_url,
            font=ctk.CTkFont(size=16)
        )
        paste_btn.grid(row=0, column=1)

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
            value=self.settings.get("create_folder_per_url", True)
        )
        folder_per_url_check = ctk.CTkCheckBox(
            advanced_frame,
            text="Create Folder per URL",
            variable=self.folder_per_url_var
        )
        folder_per_url_check.grid(row=2, column=2, sticky="w", padx=10, pady=(5, 10))

        # Buttons frame
        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.grid(row=8, column=0, sticky="ew", pady=(0, 15))
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

        # Command preview section
        command_preview_label = ctk.CTkLabel(
            frame,
            text="Command Preview:",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        command_preview_label.grid(row=9, column=0, sticky="w", pady=(0, 5))

        # Command preview frame with copy button
        command_frame = ctk.CTkFrame(frame, fg_color="transparent")
        command_frame.grid(row=10, column=0, sticky="ew")
        command_frame.grid_columnconfigure(0, weight=1)

        self.command_entry = ctk.CTkEntry(
            command_frame,
            placeholder_text="Command will appear here...",
            height=35,
            state="readonly",
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        self.command_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Copy button
        copy_btn = ctk.CTkButton(
            command_frame,
            text="📄",
            width=35,
            height=35,
            command=self.copy_command,
            font=ctk.CTkFont(size=14)
        )
        copy_btn.grid(row=0, column=1)

        # Update command preview when URL changes
        self.url_entry.bind("<KeyRelease>", lambda e: self.update_command_preview())

        # Bind download frame variables
        self.format_var.trace_add("write", lambda *args: self.update_command_preview())
        self.bitrate_var.trace_add("write", lambda *args: self.update_command_preview())
        self.preload_var.trace_add("write", lambda *args: self.update_command_preview())
        self.sponsor_block_var.trace_add("write", lambda *args: self.update_command_preview())
        self.skip_explicit_var.trace_add("write", lambda *args: self.update_command_preview())
        self.generate_lrc_var.trace_add("write", lambda *args: self.update_command_preview())
        self.playlist_numbering_var.trace_add("write", lambda *args: self.update_command_preview())
        self.folder_per_url_var.trace_add("write", lambda *args: self.update_command_preview())

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

        # Output template (Song File Template)
        template_frame = ctk.CTkFrame(frame)
        template_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        template_frame.grid_columnconfigure(0, weight=1)

        template_label = ctk.CTkLabel(
            template_frame,
            text="Song File Template (folders + filename):",
            font=ctk.CTkFont(weight="bold")
        )
        template_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        template_help = ctk.CTkLabel(
            template_frame,
            text="Controls the folder structure AND song filenames. Use / to create folders.",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        template_help.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))

        self.template_entry = ctk.CTkEntry(template_frame)
        self.template_entry.insert(0, self.settings.get("output", "{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}"))
        self.template_entry.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))

        # Bind the entry to update preview in real-time
        def update_both_previews(event):
            self.update_template_example(event)
            self.update_command_preview()

        self.template_entry.bind("<KeyRelease>", update_both_previews)

        # Dynamic example output label
        initial_example = self.generate_example_output(self.template_entry.get())
        self.example_output_label = ctk.CTkLabel(
            template_frame,
            text=f"Preview: {initial_example}",
            text_color="#4CAF50",
            font=ctk.CTkFont(size=10)
        )
        self.example_output_label.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 5))

        # Clickable tags for song template
        template_tags_label = ctk.CTkLabel(
            template_frame,
            text="Click to insert:",
            font=ctk.CTkFont(size=9),
            text_color="gray"
        )
        template_tags_label.grid(row=4, column=0, padx=10, pady=(5, 2), sticky="w")

        template_tags_frame = ctk.CTkFrame(template_frame, fg_color="transparent")
        template_tags_frame.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="w")

        song_tags = [
            "{title}", "{artist}", "{artists}", "{album}",
            "{album-artist}", "{year}", "{track-number}", "{disc-number}",
            "{genre}", "{isrc}", "{publisher}", "{output-ext}"
        ]

        for i, tag in enumerate(song_tags):
            tag_btn = ctk.CTkButton(
                template_tags_frame,
                text=tag,
                width=90,
                height=24,
                font=ctk.CTkFont(size=9),
                fg_color="gray30",
                hover_color="gray20",
                command=lambda t=tag: self.insert_tag_template(t)
            )
            tag_btn.grid(row=i//4, column=i%4, padx=2, pady=2)

        # Playlist template
        playlist_template_frame = ctk.CTkFrame(frame)
        playlist_template_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        playlist_template_frame.grid_columnconfigure(0, weight=1)

        playlist_template_label = ctk.CTkLabel(
            playlist_template_frame,
            text="Playlist Template (for playlists only):",
            font=ctk.CTkFont(weight="bold")
        )
        playlist_template_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        playlist_template_help = ctk.CTkLabel(
            playlist_template_frame,
            text="Used automatically when downloading playlists. Use {list-name}, {list-position} for playlist-specific variables.",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        playlist_template_help.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))

        self.playlist_template_entry = ctk.CTkEntry(playlist_template_frame)
        self.playlist_template_entry.insert(0, self.settings.get("playlist_output", "{list-name}/{list-position} - {artists} - {title}.{output-ext}"))
        self.playlist_template_entry.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))

        # Bind the entry to update preview in real-time
        def update_playlist_previews(event):
            self.update_playlist_template_example(event)
            self.update_command_preview()

        self.playlist_template_entry.bind("<KeyRelease>", update_playlist_previews)

        # Dynamic example output label for playlist
        initial_playlist_example = self.generate_playlist_example_output(self.playlist_template_entry.get())
        self.playlist_example_output_label = ctk.CTkLabel(
            playlist_template_frame,
            text=f"Preview: {initial_playlist_example}",
            text_color="#4CAF50",
            font=ctk.CTkFont(size=10)
        )
        self.playlist_example_output_label.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 5))

        # Clickable tags for playlist template
        playlist_tags_label = ctk.CTkLabel(
            playlist_template_frame,
            text="Click to insert:",
            font=ctk.CTkFont(size=9),
            text_color="gray"
        )
        playlist_tags_label.grid(row=4, column=0, padx=10, pady=(5, 2), sticky="w")

        playlist_tags_frame = ctk.CTkFrame(playlist_template_frame, fg_color="transparent")
        playlist_tags_frame.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="w")

        playlist_tags = [
            "{list-name}", "{list-position}", "{list-length}",
            "{title}", "{artists}", "{artist}", "{album}",
            "{year}", "{genre}", "{output-ext}"
        ]

        for i, tag in enumerate(playlist_tags):
            tag_btn = ctk.CTkButton(
                playlist_tags_frame,
                text=tag,
                width=100,
                height=24,
                font=ctk.CTkFont(size=9),
                fg_color="gray30",
                hover_color="gray20",
                command=lambda t=tag: self.insert_tag_playlist_template(t)
            )
            tag_btn.grid(row=i//4, column=i%4, padx=2, pady=2)

        # Threads
        threads_frame = ctk.CTkFrame(frame)
        threads_frame.grid(row=4, column=0, sticky="ew", pady=(0, 20))

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

        # Bind threads_var to update command preview
        self.threads_var.trace_add("write", lambda *args: self.update_command_preview())

        # Save settings button
        save_btn = ctk.CTkButton(
            frame,
            text="💾 Save Settings",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.save_settings
        )
        save_btn.grid(row=5, column=0, sticky="ew", pady=(0, 10))

        # Config file location
        config_label = ctk.CTkLabel(
            frame,
            text=f"Config saved to: {self.config_file}",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        )
        config_label.grid(row=6, column=0, sticky="w")

        # Theme settings
        theme_frame = ctk.CTkFrame(frame)
        theme_frame.grid(row=7, column=0, sticky="ew", pady=(20, 0))
        theme_frame.grid_columnconfigure(0, weight=1)

        theme_label = ctk.CTkLabel(
            theme_frame,
            text="Appearance:",
            font=ctk.CTkFont(weight="bold")
        )
        theme_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="Dark Mode",
            command=self.toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

        # Set initial state based on settings
        if self.settings.get("theme", "dark") == "dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

        # SpotDL installation check
        spotdl_frame = ctk.CTkFrame(frame)
        spotdl_frame.grid(row=8, column=0, sticky="ew", pady=(20, 0))
        spotdl_frame.grid_columnconfigure(0, weight=1)

        spotdl_label = ctk.CTkLabel(
            spotdl_frame,
            text="SpotDL Installation:",
            font=ctk.CTkFont(weight="bold")
        )
        spotdl_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        # Status label
        self.spotdl_status_label = ctk.CTkLabel(
            spotdl_frame,
            text="Checking...",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        self.spotdl_status_label.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="w")

        # Buttons frame
        spotdl_buttons_frame = ctk.CTkFrame(spotdl_frame, fg_color="transparent")
        spotdl_buttons_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        check_spotdl_btn = ctk.CTkButton(
            spotdl_buttons_frame,
            text="Check Installation",
            width=150,
            command=self.check_spotdl_installation
        )
        check_spotdl_btn.grid(row=0, column=0, padx=(0, 5))

        install_spotdl_btn = ctk.CTkButton(
            spotdl_buttons_frame,
            text="Install SpotDL",
            width=150,
            command=self.install_spotdl,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        install_spotdl_btn.grid(row=0, column=1, padx=5)

        # Initial check
        self.check_spotdl_installation()

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

    def paste_url(self):
        """Paste from clipboard into URL entry"""
        try:
            clipboard_text = self.clipboard_get()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, clipboard_text)
            self.update_command_preview()
        except:
            pass  # Clipboard empty or inaccessible

    def copy_command(self):
        """Copy command preview to clipboard"""
        command = self.command_entry.get()
        if command and command != "Command will appear here...":
            try:
                self.clipboard_clear()
                self.clipboard_append(command)
                # Visual feedback
                self.command_entry.configure(state="normal")
                temp_value = self.command_entry.get()
                self.command_entry.delete(0, "end")
                self.command_entry.insert(0, temp_value + " ✓")
                self.command_entry.configure(state="readonly")

                # Reset after 1 second
                def reset():
                    self.command_entry.configure(state="normal")
                    self.command_entry.delete(0, "end")
                    self.command_entry.insert(0, temp_value)
                    self.command_entry.configure(state="readonly")

                self.after(1000, reset)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy to clipboard:\n{str(e)}")

    def update_command_preview(self):
        """Update the command preview field with current settings"""
        query = self.url_entry.get().strip()

        if not query:
            self.command_entry.configure(state="normal")
            self.command_entry.delete(0, "end")
            self.command_entry.configure(placeholder_text="Command will appear here...")
            self.command_entry.configure(state="readonly")
            return

        # Build command exactly as it will be executed
        cmd_parts = ["spotdl", query]

        # Add options
        cmd_parts.extend(["--format", self.format_var.get()])
        cmd_parts.extend(["--bitrate", self.bitrate_var.get()])
        cmd_parts.extend(["--threads", self.threads_var.get()])

        # Automatically select the correct template based on URL type
        is_playlist_url = self.is_playlist(query)
        if is_playlist_url:
            template = self.settings.get("playlist_output", "{list-name}/{list-position} - {artists} - {title}.{output-ext}")
        else:
            template = self.settings.get("output", "{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}")

        cmd_parts.extend(["--output", template])

        # Add flags
        if self.preload_var.get():
            cmd_parts.append("--preload")
        if self.sponsor_block_var.get():
            cmd_parts.append("--sponsor-block")
        if self.skip_explicit_var.get():
            cmd_parts.append("--skip-explicit")
        if self.generate_lrc_var.get():
            cmd_parts.append("--generate-lrc")
        if self.playlist_numbering_var.get():
            cmd_parts.append("--playlist-numbering")

        # Build command string
        command = " ".join(cmd_parts)

        # Update entry
        self.command_entry.configure(state="normal")
        self.command_entry.delete(0, "end")
        self.command_entry.insert(0, command)
        self.command_entry.configure(state="readonly")

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

        # Get settings (before switching to queue tab)
        format_val = self.format_var.get()
        bitrate_val = self.bitrate_var.get()
        threads_val = self.threads_var.get()
        download_folder = self.folder_entry.get()
        folder_per_url = self.folder_per_url_var.get()

        # Get flags
        preload = self.preload_var.get()
        sponsor_block = self.sponsor_block_var.get()
        skip_explicit = self.skip_explicit_var.get()
        generate_lrc = self.generate_lrc_var.get()
        playlist_numbering = self.playlist_numbering_var.get()

        # Check content type quickly (doesn't require network)
        is_playlist_url = self.is_playlist(query)
        is_album_url = self.is_album(query)
        content_type = self.get_content_type(query)

        # Automatically select the correct template based on URL type
        if is_playlist_url:
            template_val = self.playlist_template_entry.get()
            self.log_to_queue(f"🎼 Using playlist template\n")
        else:
            template_val = self.template_entry.get()
            if is_album_url:
                self.log_to_queue(f"💿 Using album/track template\n")

        # Log initial message
        timestamp = datetime.now().strftime("%H:%M:%S")
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

        # Clear URL input
        self.url_entry.delete(0, "end")

        # Switch to queue tab immediately (no UI freeze!)
        self.show_frame("queue")

        # Start download preparation and execution in background thread
        threading.Thread(
            target=self.prepare_and_download,
            args=(query, format_val, bitrate_val, threads_val, template_val,
                  download_folder, folder_per_url,
                  is_playlist_url, is_album_url,
                  preload, sponsor_block, skip_explicit, generate_lrc, playlist_numbering),
            daemon=True
        ).start()

    def prepare_and_download(self, query, format_val, bitrate_val, threads_val,
                            template_val, download_folder, folder_per_url,
                            is_playlist_url, is_album_url,
                            preload, sponsor_block, skip_explicit, generate_lrc,
                            playlist_numbering):
        """Prepare download folder (fetch metadata if needed) and start download - runs in background thread"""

        # Handle folder per URL organization
        if folder_per_url:
            # For albums and playlists, try to get real names
            if is_playlist_url or is_album_url:
                content_type_name = "album" if is_album_url else "playlist"

                # Fetch metadata from Spotify (this is the slow part, now in background thread)
                self.log_to_queue(f"🔍 Fetching {content_type_name} metadata from Spotify...\n")
                metadata = self.get_spotify_metadata(query)

                if metadata:
                    self.log_to_queue(f"✅ Found {content_type_name}: {metadata.get('name', 'Unknown')}\n")
                    # Use the auto-detected name
                    folder_name = self.sanitize_folder_name(metadata['name'])
                else:
                    # Metadata fetch failed, fallback to URL-based naming
                    self.log_to_queue(f"⚠️ Could not fetch metadata, using URL-based name\n")
                    folder_name = self.sanitize_folder_name(query)
            else:
                # For other types (tracks, etc.), create folder from URL
                folder_name = self.sanitize_folder_name(query)

            # Create folder directly in output folder (no "Playlists" parent)
            download_folder = os.path.join(download_folder, folder_name)

        # Log folder path
        self.log_to_queue(f"Folder: {download_folder}\n")

        # Build command
        cmd = ["spotdl", query]
        cmd.extend(["--format", format_val])
        cmd.extend(["--bitrate", bitrate_val])
        cmd.extend(["--threads", threads_val])
        cmd.extend(["--output", template_val])

        # Add flags
        if preload:
            cmd.append("--preload")
        if sponsor_block:
            cmd.append("--sponsor-block")
        if skip_explicit:
            cmd.append("--skip-explicit")
        if generate_lrc:
            cmd.append("--generate-lrc")
        if playlist_numbering:
            cmd.append("--playlist-numbering")

        self.log_to_queue(f"Command: {' '.join(cmd)}\n")
        self.log_to_queue(f"{'='*60}\n\n")

        # Now run the actual download
        self.run_download(cmd, download_folder, query)

    def get_spotify_metadata(self, url_or_query):
        """Get comprehensive metadata from Spotify using enhanced metadata handler

        Returns:
            dict or None: Metadata dictionary with rich fields including:
                         'name', 'type', 'artist', 'artists', 'album', 'album-artist',
                         'year', 'date', 'genre', 'genres', 'url', 'cover_url',
                         'duration', 'explicit', 'popularity', 'track_count', etc.
                         or None if fetching fails
        """
        try:
            # Use the enhanced metadata handler
            metadata = self.metadata_handler.get_metadata(url_or_query)

            if metadata:
                # Ensure 'album-artist' key exists (with dash) for template compatibility
                if 'album_artist' in metadata and 'album-artist' not in metadata:
                    metadata['album-artist'] = metadata['album_artist']

                # Ensure year is a string for template formatting
                if 'year' in metadata:
                    metadata['year'] = str(metadata['year'])

            return metadata

        except Exception as e:
            # If metadata fetch fails, return None to fallback to URL-based naming
            return None

    def apply_folder_template(self, template, metadata):
        """Apply metadata to folder name template using enhanced formatter

        Args:
            template: Template string like "{artist} - {album} ({year})"
                     Supports: {name}, {artist}, {artists}, {album}, {album-artist},
                              {year}, {date}, {genre}, {type}
            metadata: Dictionary with metadata fields

        Returns:
            str: Folder name with variables replaced, or None if template/metadata invalid
        """
        if not template or not metadata:
            return None

        # Use the metadata handler's format_template method
        return self.metadata_handler.format_template(template, metadata)

    def sanitize_folder_name(self, url_or_query):
        """Create a safe folder name from URL or query using enhanced sanitizer"""
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
        if "spotify.com" in url_or_query and "/playlist/" in url_or_query:
            # For Spotify playlists, use the playlist ID
            parts = url_or_query.split("/")
            if len(parts) >= 2:
                playlist_id = parts[-1].split("?")[0][:12]  # Get ID, remove query params
                return f"Spotify_Playlist_{playlist_id}"

        elif "spotify.com" in url_or_query:
            # For other Spotify URLs
            parts = url_or_query.split("/")
            if len(parts) >= 2:
                # Get the type and ID
                content_type = parts[-2] if "/" in url_or_query else "item"
                content_id = parts[-1].split("?")[0][:12]
                return f"Spotify_{content_type}_{content_id}"

        elif "youtube.com/playlist" in url_or_query:
            # YouTube playlist
            list_id = url_or_query.split("list=")[-1].split("&")[0][:12]
            return f"YouTube_Playlist_{list_id}"

        elif "youtube.com" in url_or_query or "youtu.be" in url_or_query:
            # YouTube video
            return f"YouTube_{url_or_query.split('=')[-1][:8]}"

        # For other queries, use the enhanced sanitizer
        return self.metadata_handler.sanitize_folder_name(url_or_query, max_length=100)

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
