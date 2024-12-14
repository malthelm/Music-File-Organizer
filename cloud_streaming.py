import dropbox
from dropbox.files import DownloadError, FileMetadata
from typing import BinaryIO, Optional, Dict, List, Callable
import io
import pygame
import threading
import time
import os
from pathlib import Path
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor

class CloudCache:
    def __init__(self, cache_dir: str, max_size_gb: float = 10):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size_gb * 1024 * 1024 * 1024  # Convert to bytes
        self.cache_index: Dict[str, Dict] = {}
        self._load_index()
        
    def _load_index(self):
        try:
            index_path = self.cache_dir / "cache_index.json"
            if index_path.exists():
                with open(index_path, 'r') as f:
                    self.cache_index = json.load(f)
        except Exception as e:
            logging.error(f"Error loading cache index: {e}")
            self.cache_index = {}
            
    def _save_index(self):
        try:
            with open(self.cache_dir / "cache_index.json", 'w') as f:
                json.dump(self.cache_index, f)
        except Exception as e:
            logging.error(f"Error saving cache index: {e}")

    def get_cached_path(self, cloud_path: str) -> Optional[Path]:
        """Get cached file path if it exists"""
        if cloud_path in self.cache_index:
            cache_path = self.cache_dir / self.cache_index[cloud_path]['local_name']
            if cache_path.exists():
                return cache_path
        return None

    def add_to_cache(self, cloud_path: str, data: bytes):
        """Add file to cache"""
        # Generate cache file name
        file_hash = hashlib.sha256(data).hexdigest()[:16]
        local_name = f"{file_hash}{Path(cloud_path).suffix}"
        cache_path = self.cache_dir / local_name
        
        # Write file
        with open(cache_path, 'wb') as f:
            f.write(data)
            
        # Update index
        self.cache_index[cloud_path] = {
            'local_name': local_name,
            'size': len(data),
            'last_accessed': time.time()
        }
        
        # Cleanup if needed
        self._cleanup_cache()
        self._save_index()
        
    def _cleanup_cache(self):
        """Remove old files if cache size exceeds limit"""
        current_size = sum(entry['size'] for entry in self.cache_index.values())
        
        if current_size > self.max_size:
            # Sort by last accessed time
            sorted_files = sorted(
                self.cache_index.items(),
                key=lambda x: x[1]['last_accessed']
            )
            
            # Remove oldest files until under limit
            while current_size > self.max_size * 0.9:  # Leave 10% buffer
                if not sorted_files:
                    break
                    
                cloud_path, info = sorted_files.pop(0)
                try:
                    os.remove(self.cache_dir / info['local_name'])
                    current_size -= info['size']
                    del self.cache_index[cloud_path]
                except Exception as e:
                    logging.error(f"Error removing cached file: {e}")

class StreamBuffer:
    def __init__(self, size: int = 1024 * 1024):
        self.size = size
        self.buffer = io.BytesIO()
        self.write_pos = 0
        self.read_pos = 0
        self.lock = threading.Lock()
        
    def write(self, data: bytes) -> int:
        with self.lock:
            current_pos = self.buffer.tell()
            self.buffer.seek(self.write_pos)
            bytes_written = self.buffer.write(data)
            self.write_pos = (self.write_pos + bytes_written) % self.size
            self.buffer.seek(current_pos)
            return bytes_written
            
    def read(self, size: int = -1) -> bytes:
        with self.lock:
            current_pos = self.buffer.tell()
            self.buffer.seek(self.read_pos)
            data = self.buffer.read(size)
            self.read_pos = (self.read_pos + len(data)) % self.size
            self.buffer.seek(current_pos)
            return data
            
    def available(self) -> int:
        return (self.write_pos - self.read_pos) % self.size

class CloudStreamingManager:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.dbx = None if not token else dropbox.Dropbox(token)
        self.cache = CloudCache(os.path.expanduser("~/.music_organizer/cache"))
        self.buffer = StreamBuffer(1024 * 1024 * 10)  # 10MB buffer
        self.current_stream = None
        self.is_streaming = False
        self.download_executor = ThreadPoolExecutor(max_workers=4)
        
    def connect(self, token: str):
        """Connect to Dropbox"""
        self.token = token
        self.dbx = dropbox.Dropbox(token)
        
    def list_files(self, path: str = "", recursive: bool = True) -> List[Dict]:
        """List files in Dropbox directory"""
        if not self.dbx:
            raise ValueError("Not connected to Dropbox")
            
        files = []
        try:
            if recursive:
                result = self.dbx.files_list_folder(path, recursive=True)
            else:
                result = self.dbx.files_list_folder(path)
                
            while True:
                for entry in result.entries:
                    if isinstance(entry, FileMetadata):
                        files.append({
                            'name': entry.name,
                            'path': entry.path_display,
                            'size': entry.size,
                            'modified': entry.server_modified,
                            'synced': self.cache.get_cached_path(entry.path_display) is not None
                        })
                        
                if not result.has_more:
                    break
                    
                result = self.dbx.files_list_folder_continue(result.cursor)
                
        except Exception as e:
            logging.error(f"Error listing files: {e}")
            
        return files
        
    def start_streaming(self, file_path: str) -> bool:
        """Start streaming a file from cloud"""
        if not self.dbx:
            raise ValueError("Not connected to cloud")
            
        try:
            # Check cache first
            cached_path = self.cache.get_cached_path(file_path)
            if cached_path:
                pygame.mixer.music.load(str(cached_path))
                pygame.mixer.music.play()
                return True
                
            # Start streaming
            self.current_stream = self.dbx.files_download_stream(file_path)
            
            # Fill initial buffer
            self._fill_buffer()
            
            # Start playback
            pygame.mixer.music.load(self.buffer)
            pygame.mixer.music.play()
            
            # Start buffer management
            self.is_streaming = True
            threading.Thread(
                target=self._manage_buffer,
                daemon=True
            ).start()
            
            # Start background download
            self.download_executor.submit(self._background_download, file_path)
            
            return True
            
        except Exception as e:
            logging.error(f"Streaming error: {e}")
            return False
            
    def _fill_buffer(self):
        """Fill streaming buffer"""
        while self.buffer.available() < self.buffer.size * 0.8:
            chunk = self.current_stream.read(1024 * 64)  # 64KB chunks
            if not chunk:
                break
            self.buffer.write(chunk)
            
    def _manage_buffer(self):
        """Manage streaming buffer"""
        while self.is_streaming and pygame.mixer.music.get_busy():
            if self.buffer.available() < self.buffer.size * 0.2:
                self._fill_buffer()
            time.sleep(0.1)
            
    def _background_download(self, file_path: str):
        """Download complete file in background"""
        try:
            _, response = self.dbx.files_download(file_path)
            self.cache.add_to_cache(file_path, response.content)
        except Exception as e:
            logging.error(f"Background download error: {e}")
            
    def stop_streaming(self):
        """Stop current stream"""
        self.is_streaming = False
        if self.current_stream:
            self.current_stream.close()
            self.current_stream = None
        self.buffer.seek(0)
        self.buffer.truncate()