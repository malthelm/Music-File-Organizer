import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Callable
import json
from mutagen import File
from mutagen.easyid3 import EasyID3
import mutagen.flac
import threading
from queue import Queue

@dataclass
class AudioMetadata:
    title: str = ""
    artist: str = ""
    album: str = ""
    year: str = ""
    genre: str = ""
    duration: float = 0.0
    bpm: float = 0.0
    key: str = ""
    analysis: Dict = None

    def __post_init__(self):
        if self.analysis is None:
            self.analysis = {}

    def update(self, data: Dict):
        """Update metadata from analysis results"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

@dataclass
class AudioFile:
    path: str
    filename: str
    extension: str
    size: int
    metadata: AudioMetadata
    tags: List[str] = None
    notes: str = ""
    waveform_data: Optional[List[float]] = None

    def to_dict(self):
        return {
            'path': self.path,
            'filename': self.filename,
            'extension': self.extension,
            'size': self.size,
            'metadata': {
                'title': self.metadata.title,
                'artist': self.metadata.artist,
                'album': self.metadata.album,
                'year': self.metadata.year,
                'genre': self.metadata.genre,
                'duration': self.metadata.duration,
                'bpm': self.metadata.bpm,
                'key': self.metadata.key,
                'analysis': self.metadata.analysis
            },
            'tags': self.tags or [],
            'notes': self.notes
        }

class MusicScanner:
    SUPPORTED_FORMATS = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aiff'}
    
    def __init__(self, metadata_file='music_metadata.json'):
        self.metadata_file = metadata_file
        self.audio_files: Dict[str, AudioFile] = {}
        self.scan_queue = Queue()
        self.scan_thread = None
        self._load_metadata()

    def scan_directory(self, directory: str, progress_callback: Callable = None) -> Dict[str, AudioFile]:
        """Scan directory for audio files with progress updates"""
        total_files = sum(1 for root, _, files in os.walk(directory) 
                         for file in files 
                         if os.path.splitext(file)[1].lower() in self.SUPPORTED_FORMATS)
        
        processed = 0
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                extension = os.path.splitext(file)[1].lower()
                
                if extension in self.SUPPORTED_FORMATS:
                    abs_path = str(Path(file_path).absolute())
                    if abs_path not in self.audio_files:
                        metadata = self._extract_metadata(file_path)
                        self.audio_files[abs_path] = AudioFile(
                            path=abs_path,
                            filename=file,
                            extension=extension,
                            size=os.path.getsize(file_path),
                            metadata=metadata,
                            tags=[],
                            notes=""
                        )
                        
                        # Queue file for waveform generation
                        self.scan_queue.put(abs_path)
                        
                    processed += 1
                    if progress_callback:
                        progress_callback(processed, total_files)
        
        # Start background processing if not already running
        if not self.scan_thread or not self.scan_thread.is_alive():
            self.scan_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.scan_thread.start()
        
        self._save_metadata()
        return self.audio_files

    def _process_queue(self):
        """Process queued files for waveform generation"""
        while True:
            try:
                file_path = self.scan_queue.get(timeout=1)
                self._generate_waveform(file_path)
                self.scan_queue.task_done()
            except Queue.Empty:
                break

    def _generate_waveform(self, file_path: str):
        """Generate and store waveform data"""
        try:
            import numpy as np
            import librosa
            
            y, sr = librosa.load(file_path, duration=30)  # Load first 30 seconds
            waveform = librosa.feature.rms(y=y)[0]
            self.audio_files[file_path].waveform_data = waveform.tolist()
            self._save_metadata()
        except Exception as e:
            print(f"Error generating waveform for {file_path}: {e}")

    def _extract_metadata(self, file_path: str) -> AudioMetadata:
        """Extract metadata from audio file"""
        try:
            audio = File(file_path)
            if audio is None:
                return AudioMetadata()

            metadata = AudioMetadata()
            
            if isinstance(audio, mutagen.flac.FLAC):
                metadata.title = str(audio.get('title', [''])[0])
                metadata.artist = str(audio.get('artist', [''])[0])
                metadata.album = str(audio.get('album', [''])[0])
                metadata.year = str(audio.get('date', [''])[0])
                metadata.genre = str(audio.get('genre', [''])[0])
            else:
                try:
                    audio = EasyID3(file_path)
                    metadata.title = str(audio.get('title', [''])[0])
                    metadata.artist = str(audio.get('artist', [''])[0])
                    metadata.album = str(audio.get('album', [''])[0])
                    metadata.year = str(audio.get('date', [''])[0])
                    metadata.genre = str(audio.get('genre', [''])[0])
                except:
                    pass

            metadata.duration = audio.info.length
            return metadata
        except:
            return AudioMetadata()

    def add_tag(self, file_path: str, tag: str):
        """Add a tag to a file"""
        if file_path in self.audio_files:
            if self.audio_files[file_path].tags is None:
                self.audio_files[file_path].tags = []
            if tag not in self.audio_files[file_path].tags:
                self.audio_files[file_path].tags.append(tag)
                self._save_metadata()

    def add_note(self, file_path: str, note: str):
        """Add a note to a file"""
        if file_path in self.audio_files:
            self.audio_files[file_path].notes = note
            self._save_metadata()

    def remove_tag(self, file_path: str, tag: str):
        """Remove a tag from a file"""
        if file_path in self.audio_files:
            if tag in self.audio_files[file_path].tags:
                self.audio_files[file_path].tags.remove(tag)
                self._save_metadata()

    def get_all_tags(self) -> Set[str]:
        """Get all unique tags used across all files"""
        tags = set()
        for audio_file in self.audio_files.values():
            if audio_file.tags:
                tags.update(audio_file.tags)
        return tags

    def _save_metadata(self):
        """Save metadata to JSON file"""
        metadata = {
            path: audio_file.to_dict() 
            for path, audio_file in self.audio_files.items()
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)

    def _load_metadata(self):
        """Load metadata from JSON file"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
                self.audio_files = {}
                for path, data in metadata.items():
                    # Get metadata with default values for missing fields
                    metadata_obj = AudioMetadata(
                        title=data['metadata'].get('title', ''),
                        artist=data['metadata'].get('artist', ''),
                        album=data['metadata'].get('album', ''),
                        year=data['metadata'].get('year', ''),
                        genre=data['metadata'].get('genre', ''),
                        duration=data['metadata'].get('duration', 0.0),
                        bpm=data['metadata'].get('bpm', 0.0),
                        key=data['metadata'].get('key', ''),
                        analysis=data['metadata'].get('analysis', {})
                    )
                    
                    # Create AudioFile object with the proper metadata object
                    self.audio_files[path] = AudioFile(
                        path=data['path'],
                        filename=data['filename'],
                        extension=data['extension'],
                        size=data['size'],
                        metadata=metadata_obj,
                        tags=data.get('tags', []),
                        notes=data.get('notes', '')
                    )