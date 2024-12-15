from typing import Dict, List, Set
import os
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from music_scanner import AudioFile

class DuplicateFinder:
    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size
        self.duplicates: Dict[str, List[str]] = {}

    def calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(self.chunk_size), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def find_duplicates(self, audio_files: Dict[str, AudioFile]) -> Dict[str, List[str]]:
        """Find duplicate files based on content"""
        checksums: Dict[str, List[str]] = {}
        
        # Calculate checksums in parallel
        with ThreadPoolExecutor() as executor:
            future_to_path = {
                executor.submit(self.calculate_checksum, af.path): af.path
                for af in audio_files.values()
            }
            
            for future in future_to_path:
                path = future_to_path[future]
                try:
                    checksum = future.result()
                    if checksum not in checksums:
                        checksums[checksum] = []
                    checksums[checksum].append(path)
                except Exception as e:
                    logging.error(f"Error calculating checksum for {path}: {e}")

        # Filter out unique files
        self.duplicates = {
            checksum: paths
            for checksum, paths in checksums.items()
            if len(paths) > 1
        }
        
        return self.duplicates 