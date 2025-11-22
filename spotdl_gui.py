#!/usr/bin/env python3
"""
SpotDL Desktop GUI
A modern desktop interface for SpotDL
"""

import customtkinter as ctk
import subprocess
import threading
import os
from pathlib import Path
from tkinter import filedialog, messagebox
import queue
import sys

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class SpotDLGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("SpotDL GUI")
        self.geometry("1000x700")

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

        # Initialize frames
        self.frames = {}
        self.create_download_frame()
        self.create_queue_frame()
        self.create_settings_frame()

        # Download queue
        self.download_queue = []
        self.current_process = None

        # Default settings
        self.settings = {
            "format": "mp3",
            "bitrate": "320k",
            "threads": "4",
            "output": "{artists} - {title}.{output-ext}",
            "audio_providers": ["youtube-music", "youtube"],
            "lyrics_providers": ["genius", "musixmatch"],
            "download_folder": str(Path.home() / "Music")
        }

        # Show download frame by default
        self.show_frame("download")

        # Check SpotDL
        self.check_spotdl()

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

        # Quick buttons
        quick_frame = ctk.CTkFrame(frame, fg_color="transparent")
        quick_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))

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
        options_frame.grid(row=4, column=0, sticky="ew", pady=(0, 20))
        options_frame.grid_columnconfigure((0, 1), weight=1)

        # Format
        format_label = ctk.CTkLabel(options_frame, text="Format:")
        format_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.format_var = ctk.StringVar(value="mp3")
        format_menu = ctk.CTkOptionMenu(
            options_frame,
            variable=self.format_var,
            values=["mp3", "flac", "ogg", "opus", "m4a", "wav"]
        )
        format_menu.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # Bitrate
        bitrate_label = ctk.CTkLabel(options_frame, text="Bitrate:")
        bitrate_label.grid(row=0, column=1, sticky="w", padx=10, pady=(10, 5))

        self.bitrate_var = ctk.StringVar(value="320k")
        bitrate_menu = ctk.CTkOptionMenu(
            options_frame,
            variable=self.bitrate_var,
            values=["auto", "320k", "256k", "192k", "128k", "96k"]
        )
        bitrate_menu.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 10))

        # Advanced options
        advanced_frame = ctk.CTkFrame(frame)
        advanced_frame.grid(row=5, column=0, sticky="ew", pady=(0, 20))
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
        lrc_check.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 10))

        self.playlist_numbering_var = ctk.BooleanVar()
        numbering_check = ctk.CTkCheckBox(
            advanced_frame,
            text="Playlist Numbering",
            variable=self.playlist_numbering_var
        )
        numbering_check.grid(row=2, column=1, sticky="w", padx=10, pady=(0, 10))

        # Download button
        self.download_btn = ctk.CTkButton(
            frame,
            text="⬇️ Download",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_download
        )
        self.download_btn.grid(row=6, column=0, sticky="ew")

    def create_queue_frame(self):
        """Create the queue tab"""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        self.frames["queue"] = frame

        # Title
        title = ctk.CTkLabel(
            frame,
            text="Download Queue",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Queue list
        self.queue_textbox = ctk.CTkTextbox(frame, state="disabled")
        self.queue_textbox.grid(row=1, column=0, sticky="nsew")

        # Clear button
        clear_btn = ctk.CTkButton(
            frame,
            text="Clear Queue",
            command=self.clear_queue
        )
        clear_btn.grid(row=2, column=0, pady=(10, 0))

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

        folder_label = ctk.CTkLabel(folder_frame, text="Download Folder:")
        folder_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.folder_entry = ctk.CTkEntry(folder_frame)
        self.folder_entry.insert(0, str(Path.home() / "Music"))
        self.folder_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        browse_btn = ctk.CTkButton(
            folder_frame,
            text="Browse",
            width=100,
            command=self.browse_folder
        )
        browse_btn.grid(row=0, column=2, padx=10, pady=10)

        # Output template
        template_frame = ctk.CTkFrame(frame)
        template_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        template_frame.grid_columnconfigure(0, weight=1)

        template_label = ctk.CTkLabel(
            template_frame,
            text="Output Template:",
            font=ctk.CTkFont(weight="bold")
        )
        template_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.template_entry = ctk.CTkEntry(template_frame)
        self.template_entry.insert(0, "{artists} - {title}.{output-ext}")
        self.template_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # Template help
        help_text = ctk.CTkLabel(
            template_frame,
            text="Variables: {title}, {artist}, {artists}, {album}, {year}, {track-number}, etc.",
            text_color="gray"
        )
        help_text.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 10))

        # Threads
        threads_frame = ctk.CTkFrame(frame)
        threads_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))

        threads_label = ctk.CTkLabel(threads_frame, text="Concurrent Downloads:")
        threads_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.threads_var = ctk.StringVar(value="4")
        threads_slider = ctk.CTkSlider(
            threads_frame,
            from_=1,
            to=16,
            number_of_steps=15,
            command=lambda v: self.threads_var.set(str(int(v)))
        )
        threads_slider.set(4)
        threads_slider.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        threads_value = ctk.CTkLabel(threads_frame, textvariable=self.threads_var)
        threads_value.grid(row=0, column=2, padx=10, pady=10)

    def browse_folder(self):
        """Browse for download folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)

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

        # Add to queue
        self.add_to_queue(query, cmd)

        # Clear input
        self.url_entry.delete(0, "end")

        # Start download in thread
        threading.Thread(target=self.run_download, args=(cmd,), daemon=True).start()

    def add_to_queue(self, query, cmd):
        """Add item to download queue display"""
        self.queue_textbox.configure(state="normal")
        self.queue_textbox.insert("end", f"📥 {query}\n")
        self.queue_textbox.insert("end", f"   Command: {' '.join(cmd)}\n")
        self.queue_textbox.insert("end", f"   Status: Downloading...\n\n")
        self.queue_textbox.configure(state="disabled")
        self.queue_textbox.see("end")

    def run_download(self, cmd):
        """Run spotdl command in background"""
        try:
            # Change to download folder
            download_folder = self.folder_entry.get()
            os.makedirs(download_folder, exist_ok=True)

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=download_folder
            )

            stdout, stderr = process.communicate()

            # Update queue
            self.queue_textbox.configure(state="normal")
            if process.returncode == 0:
                self.queue_textbox.insert("end", "✅ Download completed!\n\n")
            else:
                self.queue_textbox.insert("end", f"❌ Download failed: {stderr}\n\n")
            self.queue_textbox.configure(state="disabled")
            self.queue_textbox.see("end")

        except Exception as e:
            self.queue_textbox.configure(state="normal")
            self.queue_textbox.insert("end", f"❌ Error: {str(e)}\n\n")
            self.queue_textbox.configure(state="disabled")
            self.queue_textbox.see("end")

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
