import customtkinter as ctk
from ui_components import (
    WaveformView, 
    ModernButton, 
    ModernSlider, 
    SidebarButton,
    ModernTable
)
from visualizer import AudioVisualizer, TurellVisualizer
from audio_analyzer import AdvancedAudioAnalyzer
from cloud_streaming import CloudStreamingManager
from rekordbox_integration import RekordboxManager
from playlist_manager import PlaylistManager
from playlist_view import PlaylistView
from music_scanner import MusicScanner
import tkinter as tk
from PIL import Image, ImageTk
import os
from tkinter import filedialog, messagebox
import time
import json
import pygame
from typing import Dict, List, Optional
import threading
import logging

class ModernMusicGUI:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_managers()
        self.create_layout()
        self.bind_shortcuts()

    def setup_window(self):
        # Configure window style
        self.root.configure(fg_color=("white", "gray14"))
        
        # Create main container with padding
        self.container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def setup_managers(self):
        self.scanner = MusicScanner()
        self.visualizer = AudioVisualizer()
        self.analyzer = AdvancedAudioAnalyzer()
        self.cloud_manager = CloudStreamingManager(None)
        self.rekordbox = RekordboxManager()
        
        # Initialize pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)

    def create_layout(self):
        """Create the main layout of the application"""
        # Create sidebar
        self.create_sidebar()
        
        # Create main content area
        self.create_main_content()
        
        # Create player section
        self.create_player()

    def create_sidebar(self):
        """Create the sidebar with navigation buttons"""
        sidebar = ctk.CTkFrame(self.container, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        
        # Logo/Title
        title = ctk.CTkLabel(
            sidebar,
            text="Music Organizer",
            font=("SF Pro Display", 20, "bold")
        )
        title.pack(pady=20)
        
        # Navigation buttons
        nav_buttons = [
            ("Library", "library"),
            ("Playlists", "playlists"),
            ("Analysis", "analysis"),
            ("Cloud", "cloud"),
            ("Settings", "settings")
        ]
        
        for text, command in nav_buttons:
            SidebarButton(
                sidebar,
                text=text,
                command=lambda cmd=command: self.navigate(cmd)
            ).pack(fill=tk.X)

    def create_main_content(self):
        """Create the main content area with different views"""
        self.main_content = ctk.CTkFrame(self.container)
        self.main_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create different views
        self.views = {
            'library': self.create_library_view(),
            'playlists': self.create_playlists_view(),
            'analysis': self.create_analysis_view(),
            'cloud': self.create_cloud_view(),
            'settings': self.create_settings_view()
        }
        
        # Show default view
        self.current_view = 'library'
        self.views[self.current_view].pack(fill=tk.BOTH, expand=True)

    def create_player(self):
        """Create the player section with visualizer"""
        player = ctk.CTkFrame(self.root, height=200)  # Increased height for visualizer
        player.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Turrell-inspired visualizer
        self.visualizer = TurellVisualizer(player, height=120)
        self.visualizer.pack(fill=tk.X, padx=20, pady=(10, 0))
        
        # Track info
        info_frame = ctk.CTkFrame(player)
        info_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.track_title = ctk.CTkLabel(
            info_frame,
            text="No track playing",
            font=("SF Pro Display", 14, "bold")
        )
        self.track_title.pack(side=tk.LEFT)
        
        # Controls
        controls = ctk.CTkFrame(player)
        controls.pack(fill=tk.X, padx=20, pady=5)
        
        # Transport buttons with modern styling
        self.prev_btn = ModernButton(controls, text="⏮", width=40)
        self.play_btn = ModernButton(controls, text="▶", width=40)
        self.next_btn = ModernButton(controls, text="⏭", width=40)
        
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress slider
        self.progress = ModernSlider(controls)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)
        
        # Volume control
        volume_frame = ctk.CTkFrame(controls)
        volume_frame.pack(side=tk.RIGHT, padx=5)
        
        ctk.CTkLabel(volume_frame, text="🔈").pack(side=tk.LEFT, padx=2)
        self.volume = ModernSlider(volume_frame, width=100)
        self.volume.pack(side=tk.LEFT, padx=2)
        ctk.CTkLabel(volume_frame, text="🔊").pack(side=tk.LEFT, padx=2)

    def navigate(self, view_name: str):
        """Switch between views"""
        if view_name in self.views:
            # Hide current view
            self.views[self.current_view].pack_forget()
            
            # Show new view
            self.current_view = view_name
            self.views[view_name].pack(fill=tk.BOTH, expand=True)

    def create_library_view(self):
        """Create the library view"""
        view = ctk.CTkFrame(self.main_content)
        
        # Toolbar
        toolbar = ctk.CTkFrame(view)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # Left side buttons
        left_buttons = ctk.CTkFrame(toolbar)
        left_buttons.pack(side=tk.LEFT)
        
        ModernButton(
            left_buttons,
            text="Scan Directory",
            command=self.scan_directory
        ).pack(side=tk.LEFT, padx=5)
        
        ModernButton(
            left_buttons,
            text="Import Rekordbox",
            command=self.import_rekordbox
        ).pack(side=tk.LEFT, padx=5)
        
        # Right side controls
        right_controls = ctk.CTkFrame(toolbar)
        right_controls.pack(side=tk.RIGHT)
        
        # View options
        view_var = ctk.StringVar(value="list")
        ctk.CTkSegmentedButton(
            right_controls,
            values=["list", "grid"],
            variable=view_var,
            command=self.change_view
        ).pack(side=tk.LEFT, padx=10)
        
        # Search
        search_frame = ctk.CTkFrame(right_controls)
        search_frame.pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_library)
        
        search = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search...",
            textvariable=self.search_var,
            width=200
        )
        search.pack(side=tk.LEFT)
        
        # Create library table
        self.library_table = ModernTable(
            view,
            columns=[
                {'key': 'title', 'title': 'Title', 'weight': 3},
                {'key': 'artist', 'title': 'Artist', 'weight': 2},
                {'key': 'album', 'title': 'Album', 'weight': 2},
                {'key': 'duration', 'title': 'Duration', 'weight': 1},
                {'key': 'bpm', 'title': 'BPM', 'weight': 1},
                {'key': 'key', 'title': 'Key', 'weight': 1},
                {'key': 'tags', 'title': 'Tags', 'weight': 2}
            ]
        )
        self.library_table.pack(fill=tk.BOTH, expand=True)
        
        return view

    def create_playlists_view(self):
        """Create the playlists view"""
        view = ctk.CTkFrame(self.main_content)
        
        # Initialize playlist manager
        storage_dir = os.path.expanduser("~/.music_organizer/playlists")
        self.playlist_manager = PlaylistManager(storage_dir)
        
        # Create playlist view
        self.playlist_view = PlaylistView(view, self.playlist_manager)
        self.playlist_view.pack(fill=tk.BOTH, expand=True)
        
        return view

    def create_analysis_view(self):
        """Create the analysis view"""
        view = ctk.CTkFrame(self.main_content)
        
        # Top controls
        controls = ctk.CTkFrame(view)
        controls.pack(fill=tk.X, pady=10)
        
        # Analysis type selector
        ctk.CTkLabel(controls, text="Analysis Type:").pack(side=tk.LEFT, padx=5)
        analysis_types = ["Audio Features", "Key Detection", "BPM Analysis", "Energy/Mood"]
        analysis_var = ctk.StringVar(value=analysis_types[0])
        
        ctk.CTkOptionMenu(
            controls,
            values=analysis_types,
            variable=analysis_var,
            command=self.change_analysis
        ).pack(side=tk.LEFT, padx=5)
        
        ModernButton(
            controls,
            text="Analyze Selected",
            command=self.analyze_tracks
        ).pack(side=tk.RIGHT, padx=5)
        
        # Analysis content
        content = ctk.CTkFrame(view)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Results view
        self.analysis_table = ModernTable(
            content,
            columns=[
                {'key': 'title', 'title': 'Title', 'weight': 3},
                {'key': 'bpm', 'title': 'BPM', 'weight': 1},
                {'key': 'key', 'title': 'Key', 'weight': 1},
                {'key': 'energy', 'title': 'Energy', 'weight': 1},
                {'key': 'mood', 'title': 'Mood', 'weight': 1}
            ]
        )
        self.analysis_table.pack(fill=tk.BOTH, expand=True)
        
        return view

    def create_cloud_view(self):
        """Create the cloud view"""
        view = ctk.CTkFrame(self.main_content)
        
        # Cloud status bar
        status = ctk.CTkFrame(view)
        status.pack(fill=tk.X, pady=10)
        
        self.cloud_status = ctk.CTkLabel(
            status,
            text="Not connected to cloud storage"
        )
        self.cloud_status.pack(side=tk.LEFT, padx=10)
        
        ModernButton(
            status,
            text="Connect to Dropbox",
            command=self.connect_cloud
        ).pack(side=tk.RIGHT, padx=5)
        
        # Cloud content
        content = ctk.CTkFrame(view)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Cloud files table
        self.cloud_table = ModernTable(
            content,
            columns=[
                {'key': 'name', 'title': 'Name', 'weight': 3},
                {'key': 'size', 'title': 'Size', 'weight': 1},
                {'key': 'modified', 'title': 'Modified', 'weight': 2},
                {'key': 'status', 'title': 'Status', 'weight': 1}
            ]
        )
        self.cloud_table.pack(fill=tk.BOTH, expand=True)
        
        return view

    def create_settings_view(self):
        """Create the settings view"""
        view = ctk.CTkFrame(self.main_content)
        
        # Settings categories
        categories = {
            'General': [
                {
                    'name': 'Default Directory',
                    'type': 'path',
                    'key': 'default_dir'
                },
                {
                    'name': 'Auto-analyze new files',
                    'type': 'bool',
                    'key': 'auto_analyze'
                }
            ],
            'Playback': [
                {
                    'name': 'Crossfade Duration',
                    'type': 'slider',
                    'key': 'crossfade',
                    'range': (0, 12)
                },
                {
                    'name': 'Visualizer Style',
                    'type': 'option',
                    'key': 'viz_style',
                    'options': ['dawn', 'dusk', 'ganzfeld', 'skyspace']
                }
            ],
            'Cloud': [
                {
                    'name': 'Auto-sync Library',
                    'type': 'bool',
                    'key': 'auto_sync'
                },
                {
                    'name': 'Cache Size (GB)',
                    'type': 'number',
                    'key': 'cache_size'
                }
            ]
        }
        
        # Create settings UI
        notebook = ctk.CTkTabview(view)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.settings_widgets = {}
        
        for category, settings in categories.items():
            page = notebook.add(category)
            
            for setting in settings:
                frame = ctk.CTkFrame(page)
                frame.pack(fill=tk.X, pady=5)
                
                ctk.CTkLabel(
                    frame,
                    text=setting['name']
                ).pack(side=tk.LEFT, padx=10)
                
                if setting['type'] == 'path':
                    entry = ctk.CTkEntry(frame, width=300)
                    entry.pack(side=tk.LEFT, padx=5)
                    btn = ModernButton(
                        frame,
                        text="Browse",
                        command=lambda e=entry: self.browse_path(e)
                    )
                    btn.pack(side=tk.LEFT, padx=5)
                    self.settings_widgets[setting['key']] = entry
                    
                elif setting['type'] == 'bool':
                    var = tk.BooleanVar()
                    switch = ctk.CTkSwitch(
                        frame,
                        text="",
                        variable=var
                    )
                    switch.pack(side=tk.RIGHT, padx=10)
                    self.settings_widgets[setting['key']] = var
                    
                elif setting['type'] == 'slider':
                    var = tk.DoubleVar()
                    slider = ModernSlider(
                        frame,
                        from_=setting['range'][0],
                        to=setting['range'][1],
                        variable=var,
                        width=200
                    )
                    slider.pack(side=tk.RIGHT, padx=10)
                    self.settings_widgets[setting['key']] = var
                    
                elif setting['type'] == 'option':
                    var = tk.StringVar()
                    menu = ctk.CTkOptionMenu(
                        frame,
                        values=setting['options'],
                        variable=var
                    )
                    menu.pack(side=tk.RIGHT, padx=10)
                    self.settings_widgets[setting['key']] = var
                    
                elif setting['type'] == 'number':
                    entry = ctk.CTkEntry(frame, width=100)
                    entry.pack(side=tk.RIGHT, padx=10)
                    self.settings_widgets[setting['key']] = entry
        
        return view

    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<space>', lambda e: self.toggle_playback())
        self.root.bind('<Left>', lambda e: self.prev_track())
        self.root.bind('<Right>', lambda e: self.next_track())
        self.root.bind('<Control-f>', lambda e: self.focus_search())

    def scan_directory(self):
        """Scan directory for music files"""
        directory = filedialog.askdirectory(
            title="Select Music Directory"
        )
        
        if not directory:
            return
        
        # Show progress dialog
        progress = ctk.CTkProgressBar(self.root)
        progress.pack(pady=20)
        
        def update_progress(current, total):
            progress.set(current / total)
            self.root.update()
        
        try:
            # Scan directory
            files = self.scanner.scan_directory(directory, update_progress)
            
            # Update library table
            self.library_table.clear()
            for file_path, audio_file in files.items():
                self.library_table.add_row({
                    'title': audio_file.metadata.title or os.path.basename(file_path),
                    'artist': audio_file.metadata.artist,
                    'album': audio_file.metadata.album,
                    'duration': self._format_duration(audio_file.metadata.duration),
                    'bpm': f"{audio_file.metadata.bpm:.0f}" if audio_file.metadata.bpm else "",
                    'key': audio_file.metadata.key,
                    'tags': ", ".join(audio_file.tags) if audio_file.tags else ""
                })
                
            messagebox.showinfo(
                "Scan Complete",
                f"Found {len(files)} audio files"
            )
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            progress.destroy()

    def import_rekordbox(self):
        """Import Rekordbox XML library"""
        file_path = filedialog.askopenfilename(
            title="Select Rekordbox XML",
            filetypes=[("XML files", "*.xml")]
        )
        
        if not file_path:
            return
        
        try:
            self.rekordbox.import_library(file_path)
            
            # Update library with imported tracks
            for track in self.rekordbox.library.values():
                self.library_table.add_row({
                    'title': track.name,
                    'artist': track.artist,
                    'album': track.album,
                    'duration': self._format_duration(track.duration),
                    'bpm': f"{track.bpm:.0f}" if track.bpm else "",
                    'key': track.key,
                    'tags': ""
                })
                
            messagebox.showinfo(
                "Import Complete",
                f"Imported {len(self.rekordbox.library)} tracks"
            )
            
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def change_view(self, view_type: str):
        """Change library view type"""
        # Implement grid view later
        pass

    def filter_library(self, *args):
        """Filter library based on search text"""
        search_text = self.search_var.get().lower()
        
        for row in self.library_table.get_children():
            data = self.library_table.get_row_data(row)
            visible = any(
                search_text in str(value).lower()
                for value in data.values()
            )
            if visible:
                self.library_table.show_row(row)
            else:
                self.library_table.hide_row(row)

    def change_analysis(self, analysis_type: str):
        """Change analysis type"""
        # Clear previous results
        self.analysis_table.clear()
        
        # Get selected tracks
        selected = self.library_table.get_selected_data()
        if not selected:
            return
        
        # Analyze based on type
        for track in selected:
            if analysis_type == "Audio Features":
                results = self.analyzer.analyze_file(track['path'])
            elif analysis_type == "Key Detection":
                results = {'key': self.analyzer._analyze_key(track['path'])}
            elif analysis_type == "BPM Analysis":
                results = {'bpm': self.analyzer._analyze_rhythm(track['path'])}
            elif analysis_type == "Energy/Mood":
                results = self.analyzer._analyze_mood(track['path'])
            
            # Update results table
            self.analysis_table.add_row({
                'title': track['title'],
                'bpm': f"{results.get('bpm', '')}",
                'key': results.get('key', ''),
                'energy': f"{results.get('energy', 0):.2f}",
                'mood': results.get('mood', '')
            })

    def analyze_tracks(self):
        """Analyze selected tracks"""
        selected = self.library_table.get_selected_data()
        if not selected:
            messagebox.showwarning(
                "No Selection",
                "Please select tracks to analyze"
            )
            return
        
        # Show progress dialog
        progress = ctk.CTkProgressBar(self.root)
        progress.pack(pady=20)
        
        try:
            total = len(selected)
            for i, track in enumerate(selected):
                # Analyze track
                results = self.analyzer.analyze_file(track['path'])
                
                # Update progress
                progress.set((i + 1) / total)
                self.root.update()
                
                # Update library with results
                self.library_table.update_row(track, {
                    'bpm': f"{results.get('bpm', '')}",
                    'key': results.get('key', '')}
                )
                
            messagebox.showinfo(
                "Analysis Complete",
                f"Analyzed {total} tracks"
            )
            
        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))
        finally:
            progress.destroy()

    def connect_cloud(self):
        """Connect to cloud storage"""
        token = self.get_dropbox_token()
        if not token:
            return
        
        try:
            self.cloud_manager.connect(token)
            self.cloud_status.configure(text="Connected to Dropbox")
            
            # List files
            files = self.cloud_manager.list_files()
            
            # Update cloud table
            self.cloud_table.clear()
            for file in files:
                self.cloud_table.add_row({
                    'name': file['name'],
                    'size': self._format_size(file['size']),
                    'modified': file['modified'].strftime('%Y-%m-%d %H:%M'),
                    'status': "Synced" if file['synced'] else "Not Synced"
                })
                
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def get_dropbox_token(self) -> Optional[str]:
        """Get Dropbox access token"""
        dialog = ctk.CTkInputDialog(
            text="Enter Dropbox Access Token:",
            title="Connect to Dropbox"
        )
        return dialog.get_input()

    def _format_duration(self, seconds: float) -> str:
        """Format duration as MM:SS"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def _format_size(self, size: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    # ... [rest of the class implementation] ...

if __name__ == "__main__":
    root = ctk.CTk()
    app = ModernMusicGUI(root)
    root.mainloop() 