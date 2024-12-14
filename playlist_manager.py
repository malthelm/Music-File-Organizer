from typing import Dict, List, Optional
import json
import time
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
import shutil

@dataclass
class PlaylistTrack:
    path: str
    added_at: float
    position: int
    metadata: Dict

@dataclass
class Playlist:
    name: str
    created_at: float
    modified_at: float
    tracks: List[PlaylistTrack]
    description: str = ""
    tags: List[str] = None
    image_path: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        tracks = [PlaylistTrack(**t) for t in data.pop('tracks', [])]
        return cls(tracks=tracks, **data)

class PlaylistManager:
    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.playlists: Dict[str, Playlist] = {}
        self.load_playlists()
        
    def create_playlist(self, name: str, description: str = "", tags: List[str] = None) -> Playlist:
        """Create a new playlist"""
        if name in self.playlists:
            raise ValueError(f"Playlist '{name}' already exists")
            
        now = time.time()
        playlist = Playlist(
            name=name,
            created_at=now,
            modified_at=now,
            tracks=[],
            description=description,
            tags=tags or []
        )
        
        self.playlists[name] = playlist
        self.save_playlists()
        return playlist
        
    def add_tracks(self, playlist_name: str, tracks: List[Dict]) -> None:
        """Add tracks to playlist"""
        if playlist_name not in self.playlists:
            raise ValueError(f"Playlist '{playlist_name}' not found")
            
        playlist = self.playlists[playlist_name]
        position = len(playlist.tracks)
        
        for track in tracks:
            playlist_track = PlaylistTrack(
                path=track['path'],
                added_at=time.time(),
                position=position,
                metadata=track.get('metadata', {})
            )
            playlist.tracks.append(playlist_track)
            position += 1
            
        playlist.modified_at = time.time()
        self.save_playlists()
        
    def remove_tracks(self, playlist_name: str, positions: List[int]) -> None:
        """Remove tracks from playlist"""
        if playlist_name not in self.playlists:
            raise ValueError(f"Playlist '{playlist_name}' not found")
            
        playlist = self.playlists[playlist_name]
        positions = sorted(positions, reverse=True)
        
        for pos in positions:
            if 0 <= pos < len(playlist.tracks):
                playlist.tracks.pop(pos)
                
        # Reorder remaining tracks
        for i, track in enumerate(playlist.tracks):
            track.position = i
            
        playlist.modified_at = time.time()
        self.save_playlists()
        
    def reorder_tracks(self, playlist_name: str, new_order: List[int]) -> None:
        """Reorder tracks in playlist"""
        if playlist_name not in self.playlists:
            raise ValueError(f"Playlist '{playlist_name}' not found")
            
        playlist = self.playlists[playlist_name]
        if len(new_order) != len(playlist.tracks):
            raise ValueError("New order must contain all track positions")
            
        # Create new track list
        new_tracks = []
        for i, pos in enumerate(new_order):
            track = playlist.tracks[pos]
            track.position = i
            new_tracks.append(track)
            
        playlist.tracks = new_tracks
        playlist.modified_at = time.time()
        self.save_playlists()
        
    def set_playlist_image(self, playlist_name: str, image_path: str) -> None:
        """Set playlist cover image"""
        if playlist_name not in self.playlists:
            raise ValueError(f"Playlist '{playlist_name}' not found")
            
        playlist = self.playlists[playlist_name]
        
        # Copy image to storage directory
        dest_path = self.storage_dir / f"covers/{playlist_name}{Path(image_path).suffix}"
        dest_path.parent.mkdir(exist_ok=True)
        shutil.copy2(image_path, dest_path)
        
        playlist.image_path = str(dest_path)
        playlist.modified_at = time.time()
        self.save_playlists()
        
    def export_playlist(self, playlist_name: str, format: str = 'm3u') -> str:
        """Export playlist to file"""
        if playlist_name not in self.playlists:
            raise ValueError(f"Playlist '{playlist_name}' not found")
            
        playlist = self.playlists[playlist_name]
        export_path = self.storage_dir / f"exports/{playlist_name}.{format}"
        export_path.parent.mkdir(exist_ok=True)
        
        if format == 'm3u':
            self._export_m3u(playlist, export_path)
        elif format == 'pls':
            self._export_pls(playlist, export_path)
        elif format == 'json':
            self._export_json(playlist, export_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        return str(export_path)
        
    def _export_m3u(self, playlist: Playlist, path: Path) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for track in playlist.tracks:
                duration = track.metadata.get('duration', 0)
                title = track.metadata.get('title', Path(track.path).stem)
                artist = track.metadata.get('artist', 'Unknown Artist')
                f.write(f"#EXTINF:{int(duration)},{artist} - {title}\n")
                f.write(f"{track.path}\n")
                
    def _export_pls(self, playlist: Playlist, path: Path) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            f.write("[playlist]\n")
            for i, track in enumerate(playlist.tracks, 1):
                f.write(f"File{i}={track.path}\n")
                f.write(f"Title{i}={track.metadata.get('title', Path(track.path).stem)}\n")
                f.write(f"Length{i}={int(track.metadata.get('duration', 0))}\n")
            f.write(f"NumberOfEntries={len(playlist.tracks)}\n")
            f.write("Version=2\n")
                
    def _export_json(self, playlist: Playlist, path: Path) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(playlist.to_dict(), f, indent=2)
            
    def save_playlists(self) -> None:
        """Save all playlists to storage"""
        try:
            data = {
                name: playlist.to_dict()
                for name, playlist in self.playlists.items()
            }
            with open(self.storage_dir / "playlists.json", 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving playlists: {e}")
            
    def load_playlists(self) -> None:
        """Load playlists from storage"""
        try:
            path = self.storage_dir / "playlists.json"
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.playlists = {
                        name: Playlist.from_dict(pdata)
                        for name, pdata in data.items()
                    }
        except Exception as e:
            logging.error(f"Error loading playlists: {e}") 