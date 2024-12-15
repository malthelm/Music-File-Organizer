from typing import Dict, Optional, Callable
import json
import os
from pathlib import Path
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError
import logging
import threading
from queue import Queue

class CloudSync:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.dbx = None if not token else dropbox.Dropbox(token)
        self.cache = CloudCache(os.path.expanduser("~/.music_organizer/cache"))
        self.sync_queue = Queue()
        self._start_sync_worker()
        
    def _start_sync_worker(self):
        def worker():
            while True:
                try:
                    item = self.sync_queue.get()
                    if item is None:
                        break
                    self._sync_item(item)
                except:
                    continue
                    
        threading.Thread(target=worker, daemon=True).start()
        
    def sync_library(self, callback: Optional[Callable] = None):
        """Sync entire library with cloud"""
        if not self.dbx:
            raise ValueError("Not connected to cloud")
            
        try:
            # Get cloud files
            result = self.dbx.files_list_folder("", recursive=True)
            cloud_files = {
                entry.path_lower: entry
                for entry in result.entries
                if isinstance(entry, dropbox.files.FileMetadata)
            }
            
            # Compare with local files
            total = len(cloud_files)
            for i, (path, metadata) in enumerate(cloud_files.items()):
                if callback:
                    callback(i, total)
                    
                local_path = self.cache.get_cached_path(path)
                if not local_path or metadata.server_modified > self.cache.get_modified_time(path):
                    self.sync_queue.put(path)
                    
        except Exception as e:
            logging.error(f"Sync error: {e}")
            raise 