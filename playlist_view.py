import customtkinter as ctk
import tkinter as tk
from typing import Dict, List, Optional, Callable
from PIL import Image, ImageTk
import os
from pathlib import Path
from playlist_manager import PlaylistManager, Playlist
from ui_components import ModernButton, ModernTable
import time
import json
import logging
from tkinter import filedialog, messagebox

class PlaylistView(ctk.CTkFrame):
    def __init__(self, master, playlist_manager: PlaylistManager, **kwargs):
        super().__init__(master, **kwargs)
        self.playlist_manager = playlist_manager
        self.current_playlist: Optional[str] = None
        self.setup_gui()
        
    def setup_gui(self):
        # Split view
        self.paned = ctk.CTkPanedWindow(self)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Playlists
        self.playlists_panel = self.create_playlists_panel()
        self.paned.add(self.playlists_panel)
        
        # Right panel - Tracks
        self.tracks_panel = self.create_tracks_panel()
        self.paned.add(self.tracks_panel)
        
        # Load playlists
        self.refresh_playlists()
        
    def create_playlists_panel(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self.paned)
        
        # Toolbar
        toolbar = ctk.CTkFrame(panel)
        toolbar.pack(fill=tk.X, pady=5)
        
        ModernButton(
            toolbar,
            text="New Playlist",
            command=self.create_playlist_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        ModernButton(
            toolbar,
            text="Import",
            command=self.import_playlist
        ).pack(side=tk.LEFT, padx=5)
        
        # Playlists container
        self.playlists_container = ctk.CTkScrollableFrame(panel)
        self.playlists_container.pack(fill=tk.BOTH, expand=True)
        
        return panel
        
    def create_tracks_panel(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self.paned)
        
        # Playlist info
        self.info_frame = ctk.CTkFrame(panel)
        self.info_frame.pack(fill=tk.X, pady=10)
        
        # Playlist image
        self.playlist_image = ctk.CTkLabel(
            self.info_frame,
            text="",
            width=100,
            height=100
        )
        self.playlist_image.pack(side=tk.LEFT, padx=10)
        
        # Playlist details
        details = ctk.CTkFrame(self.info_frame)
        details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        self.playlist_name = ctk.CTkLabel(
            details,
            text="No Playlist Selected",
            font=("SF Pro Display", 20, "bold")
        )
        self.playlist_name.pack(anchor='w')
        
        self.playlist_info = ctk.CTkLabel(
            details,
            text="",
            font=("SF Pro Display", 12)
        )
        self.playlist_info.pack(anchor='w')
        
        # Tracks toolbar
        tracks_toolbar = ctk.CTkFrame(panel)
        tracks_toolbar.pack(fill=tk.X, pady=5)
        
        ModernButton(
            tracks_toolbar,
            text="Add Tracks",
            command=self.add_tracks
        ).pack(side=tk.LEFT, padx=5)
        
        ModernButton(
            tracks_toolbar,
            text="Remove Selected",
            command=self.remove_selected
        ).pack(side=tk.LEFT, padx=5)
        
        ModernButton(
            tracks_toolbar,
            text="Export",
            command=self.export_playlist
        ).pack(side=tk.RIGHT, padx=5)
        
        # Tracks table
        self.tracks_table = ModernTable(
            panel,
            columns=[
                {'key': 'title', 'title': 'Title', 'weight': 3},
                {'key': 'artist', 'title': 'Artist', 'weight': 2},
                {'key': 'duration', 'title': 'Duration', 'weight': 1},
                {'key': 'added', 'title': 'Date Added', 'weight': 2}
            ]
        )
        self.tracks_table.pack(fill=tk.BOTH, expand=True)
        
        # Enable drag and drop reordering
        self.tracks_table.enable_drag_drop()
        self.tracks_table.on_reorder = self.handle_reorder
        
        return panel
        
    def create_playlist_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create Playlist")
        dialog.geometry("400x300")
        
        # Center dialog
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 50,
            self.winfo_rooty() + 50
        ))
        
        # Name
        ctk.CTkLabel(dialog, text="Name:").pack(pady=5)
        name_var = tk.StringVar()
        name_entry = ctk.CTkEntry(dialog, textvariable=name_var)
        name_entry.pack(fill=tk.X, padx=20)
        
        # Description
        ctk.CTkLabel(dialog, text="Description:").pack(pady=5)
        desc_var = tk.StringVar()
        desc_entry = ctk.CTkEntry(dialog, textvariable=desc_var)
        desc_entry.pack(fill=tk.X, padx=20)
        
        # Tags
        ctk.CTkLabel(dialog, text="Tags (comma separated):").pack(pady=5)
        tags_var = tk.StringVar()
        tags_entry = ctk.CTkEntry(dialog, textvariable=tags_var)
        tags_entry.pack(fill=tk.X, padx=20)
        
        # Image
        ctk.CTkLabel(dialog, text="Cover Image:").pack(pady=5)
        image_var = tk.StringVar()
        
        def browse_image():
            path = filedialog.askopenfilename(
                filetypes=[("Image files", "*.jpg *.jpeg *.png")]
            )
            if path:
                image_var.set(path)
                
        image_frame = ctk.CTkFrame(dialog)
        image_frame.pack(fill=tk.X, padx=20)
        
        ctk.CTkEntry(
            image_frame,
            textvariable=image_var,
            state='readonly'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ModernButton(
            image_frame,
            text="Browse",
            command=browse_image
        ).pack(side=tk.RIGHT, padx=5)
        
        def create():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Name is required")
                return
                
            try:
                playlist = self.playlist_manager.create_playlist(
                    name=name,
                    description=desc_var.get().strip(),
                    tags=[t.strip() for t in tags_var.get().split(',') if t.strip()]
                )
                
                if image_var.get():
                    self.playlist_manager.set_playlist_image(name, image_var.get())
                    
                self.refresh_playlists()
                self.load_playlist(name)
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        ModernButton(
            dialog,
            text="Create",
            command=create
        ).pack(pady=20)
        
    def refresh_playlists(self):
        # Clear current playlists
        for widget in self.playlists_container.winfo_children():
            widget.destroy()
            
        # Add playlists
        for name, playlist in self.playlist_manager.playlists.items():
            self.add_playlist_item(playlist)
            
    def add_playlist_item(self, playlist: Playlist):
        frame = ctk.CTkFrame(self.playlists_container)
        frame.pack(fill=tk.X, pady=1)
        
        # Playlist image
        if playlist.image_path and os.path.exists(playlist.image_path):
            try:
                img = Image.open(playlist.image_path)
                img.thumbnail((40, 40))
                photo = ImageTk.PhotoImage(img)
                label = ctk.CTkLabel(frame, image=photo, text="")
                label.image = photo  # Keep reference
                label.pack(side=tk.LEFT, padx=5)
            except Exception as e:
                logging.error(f"Error loading playlist image: {e}")
                
        # Playlist info
        info = ctk.CTkFrame(frame)
        info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ctk.CTkLabel(
            info,
            text=playlist.name,
            anchor='w'
        ).pack(fill=tk.X)
        
        ctk.CTkLabel(
            info,
            text=f"{len(playlist.tracks)} tracks",
            anchor='w',
            text_color=("gray50", "gray70")
        ).pack(fill=tk.X)
        
        # Make clickable
        frame.bind('<Button-1>', lambda e, n=playlist.name: self.load_playlist(n))
        
    def load_playlist(self, name: str):
        """Load playlist into tracks view"""
        self.current_playlist = name
        playlist = self.playlist_manager.playlists[name]
        
        # Update info
        self.playlist_name.configure(text=playlist.name)
        self.playlist_info.configure(
            text=f"{len(playlist.tracks)} tracks • {playlist.description}"
        )
        
        # Update image
        if playlist.image_path and os.path.exists(playlist.image_path):
            try:
                img = Image.open(playlist.image_path)
                img.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(img)
                self.playlist_image.configure(image=photo)
                self.playlist_image.image = photo
            except Exception as e:
                logging.error(f"Error loading playlist image: {e}")
                
        # Update tracks
        self.tracks_table.clear()
        for track in playlist.tracks:
            self.tracks_table.add_row({
                'title': track.metadata.get('title', Path(track.path).stem),
                'artist': track.metadata.get('artist', 'Unknown Artist'),
                'duration': self._format_duration(track.metadata.get('duration', 0)),
                'added': time.strftime('%Y-%m-%d', time.localtime(track.added_at))
            })
            
    def _format_duration(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}" 

    def add_tracks(self):
        """Add tracks to current playlist"""
        if not self.current_playlist:
            messagebox.showwarning("No Playlist", "Please select a playlist first")
            return
        
        # Show file selection dialog
        files = filedialog.askopenfilenames(
            title="Add Tracks",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.flac *.m4a *.ogg"),
                ("All Files", "*.*")
            ]
        )
        
        if not files:
            return
        
        # Prepare tracks data
        tracks = []
        for file_path in files:
            metadata = self._extract_metadata(file_path)
            tracks.append({
                'path': file_path,
                'metadata': metadata
            })
        
        # Add to playlist
        try:
            self.playlist_manager.add_tracks(self.current_playlist, tracks)
            self.load_playlist(self.current_playlist)  # Refresh view
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add tracks: {str(e)}")

    def remove_selected(self):
        """Remove selected tracks from playlist"""
        if not self.current_playlist:
            return
        
        selected = self.tracks_table.get_selected_indices()
        if not selected:
            return
        
        if messagebox.askyesno(
            "Remove Tracks",
            f"Remove {len(selected)} track(s) from playlist?"
        ):
            try:
                self.playlist_manager.remove_tracks(self.current_playlist, selected)
                self.load_playlist(self.current_playlist)  # Refresh view
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove tracks: {str(e)}")

    def handle_reorder(self, new_order: List[int]):
        """Handle track reordering from drag and drop"""
        if not self.current_playlist:
            return
        
        try:
            self.playlist_manager.reorder_tracks(self.current_playlist, new_order)
            self.load_playlist(self.current_playlist)  # Refresh view
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reorder tracks: {str(e)}")

    def import_playlist(self):
        """Import playlist from file"""
        file_path = filedialog.askopenfilename(
            title="Import Playlist",
            filetypes=[
                ("M3U Playlists", "*.m3u"),
                ("PLS Playlists", "*.pls"),
                ("Rekordbox XML", "*.xml"),
                ("JSON Playlists", "*.json"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Show progress dialog
            progress = ctk.CTkProgressBar(self)
            progress.pack(pady=20)
            
            def update_progress(current: int, total: int):
                progress.set(current / total)
                self.update()
            
            # Import based on file type
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.xml':
                self._import_rekordbox(file_path, update_progress)
            elif ext == '.m3u':
                self._import_m3u(file_path, update_progress)
            elif ext == '.pls':
                self._import_pls(file_path, update_progress)
            elif ext == '.json':
                self._import_json(file_path, update_progress)
            
            self.refresh_playlists()
            
        except Exception as e:
            messagebox.showerror("Import Error", str(e))
        finally:
            progress.destroy()

    def export_playlist(self):
        """Export current playlist"""
        if not self.current_playlist:
            messagebox.showwarning("No Playlist", "Please select a playlist first")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export Playlist",
            defaultextension=".m3u",
            filetypes=[
                ("M3U Playlist", "*.m3u"),
                ("PLS Playlist", "*.pls"),
                ("JSON Playlist", "*.json")
            ]
        )
        
        if not file_path:
            return
        
        try:
            export_path = self.playlist_manager.export_playlist(
                self.current_playlist,
                format=os.path.splitext(file_path)[1][1:]
            )
            # Copy to selected location
            shutil.copy2(export_path, file_path)
            messagebox.showinfo("Success", "Playlist exported successfully")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _extract_metadata(self, file_path: str) -> Dict:
        """Extract basic metadata from audio file"""
        try:
            from mutagen import File
            audio = File(file_path)
            if audio is None:
                return {}
            
            metadata = {}
            if hasattr(audio, 'tags'):
                tags = audio.tags
                metadata.update({
                    'title': str(tags.get('title', [''])[0]),
                    'artist': str(tags.get('artist', [''])[0]),
                    'album': str(tags.get('album', [''])[0])
                })
            
            if hasattr(audio.info, 'length'):
                metadata['duration'] = float(audio.info.length)
            
            return metadata
        except Exception as e:
            logging.error(f"Error extracting metadata: {e}")
            return {}

    def _import_rekordbox(self, file_path: str, progress_callback: Callable):
        """Import Rekordbox XML library"""
        from rekordbox_integration import RekordboxManager
        rb = RekordboxManager()
        rb.import_library(file_path)
        
        # Convert playlists
        total = len(rb.playlists)
        for i, (name, tracks) in enumerate(rb.playlists.items()):
            self.playlist_manager.create_playlist(name)
            self.playlist_manager.add_tracks(name, [
                {'path': t, 'metadata': self._extract_metadata(t)}
                for t in tracks
            ])
            progress_callback(i + 1, total)

    def _import_m3u(self, file_path: str, progress_callback: Callable):
        """Import M3U playlist"""
        name = os.path.splitext(os.path.basename(file_path))[0]
        tracks = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total = len(lines)
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line.startswith('#'):
                    tracks.append({
                        'path': line,
                        'metadata': self._extract_metadata(line)
                    })
                progress_callback(i + 1, total)
        
        if tracks:
            self.playlist_manager.create_playlist(name)
            self.playlist_manager.add_tracks(name, tracks)

    def _import_pls(self, file_path: str, progress_callback: Callable):
        """Import PLS playlist"""
        name = os.path.splitext(os.path.basename(file_path))[0]
        tracks = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total = len(lines)
            current = 0
            
            file_paths = {}
            for line in lines:
                if line.startswith('File'):
                    try:
                        idx = int(line.split('File')[1].split('=')[0])
                        path = line.split('=')[1].strip()
                        file_paths[idx] = path
                    except:
                        continue
                        
                current += 1
                progress_callback(current, total)
            
            # Add tracks in order
            for idx in sorted(file_paths.keys()):
                path = file_paths[idx]
                tracks.append({
                    'path': path,
                    'metadata': self._extract_metadata(path)
                })
            
        if tracks:
            self.playlist_manager.create_playlist(name)
            self.playlist_manager.add_tracks(name, tracks)

    def _import_json(self, file_path: str, progress_callback: Callable):
        """Import JSON playlist"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, dict):
                # Single playlist
                playlists = {data.get('name', 'Imported Playlist'): data.get('tracks', [])}
            elif isinstance(data, list):
                # Multiple playlists
                playlists = {
                    p.get('name', f'Playlist {i}'): p.get('tracks', [])
                    for i, p in enumerate(data)
                }
            else:
                raise ValueError("Invalid JSON format")
                
            total = sum(len(tracks) for tracks in playlists.values())
            current = 0
            
            for name, track_list in playlists.items():
                tracks = []
                for track_data in track_list:
                    if isinstance(track_data, str):
                        # Simple path
                        path = track_data
                        metadata = self._extract_metadata(path)
                    else:
                        # Full track data
                        path = track_data.get('path')
                        metadata = track_data.get('metadata', {})
                        if not metadata:
                            metadata = self._extract_metadata(path)
                            
                    tracks.append({
                        'path': path,
                        'metadata': metadata
                    })
                    current += 1
                    progress_callback(current, total)
                    
                if tracks:
                    self.playlist_manager.create_playlist(name)
                    self.playlist_manager.add_tracks(name, tracks)
                    
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON file")

    def enable_drag_drop(self):
        """Enable drag and drop for tracks table"""
        self.tracks_table.bind('<Button-1>', self.start_drag)
        self.tracks_table.bind('<B1-Motion>', self.drag)
        self.tracks_table.bind('<ButtonRelease-1>', self.drop)
        
        self.drag_data = {
            'item': None,
            'x': 0,
            'y': 0
        }

    def start_drag(self, event):
        """Start track drag operation"""
        item = self.tracks_table.identify_row(event.y)
        if item:
            self.drag_data['item'] = item
            self.drag_data['x'] = event.x
            self.drag_data['y'] = event.y

    def drag(self, event):
        """Handle track dragging"""
        if self.drag_data['item']:
            # Calculate new position
            move_to = self.tracks_table.index(
                self.tracks_table.identify_row(event.y)
            )
            if move_to >= 0:
                self.tracks_table.move(
                    self.drag_data['item'],
                    '',
                    move_to
                )

    def drop(self, event):
        """Handle track drop"""
        if self.drag_data['item']:
            # Get new order
            items = self.tracks_table.get_children()
            new_order = [items.index(self.drag_data['item'])]
            
            # Update playlist
            self.handle_reorder(new_order)
            
            # Reset drag data
            self.drag_data['item'] = None

    def handle_playlist_drop(self, event):
        """Handle files dropped onto playlist"""
        if not self.current_playlist:
            return
        
        # Get dropped files
        files = self.parse_drop_data(event.data)
        if not files:
            return
        
        # Add tracks
        tracks = []
        for file_path in files:
            if os.path.splitext(file_path)[1].lower() in {'.mp3', '.wav', '.flac', '.m4a', '.ogg'}:
                metadata = self._extract_metadata(file_path)
                tracks.append({
                    'path': file_path,
                    'metadata': metadata
                })
        
        if tracks:
            try:
                self.playlist_manager.add_tracks(self.current_playlist, tracks)
                self.load_playlist(self.current_playlist)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add tracks: {str(e)}")

    def parse_drop_data(self, data: str) -> List[str]:
        """Parse drag and drop data"""
        if not data:
            return []
        
        # Handle different data formats
        if data.startswith('{'):
            # Windows format
            try:
                files = json.loads(data)['files']
                return [f.replace('\\', '/') for f in files]
            except:
                pass
                
        # Unix format
        return [f.strip() for f in data.split('\n') if f.strip()]