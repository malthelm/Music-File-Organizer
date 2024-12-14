from typing import Dict, List
from collections import Counter
import os
from music_scanner import AudioFile

class StatsManager:
    def __init__(self):
        self.total_files = 0
        self.total_size = 0
        self.format_counts: Dict[str, int] = Counter()
        self.tag_counts: Dict[str, int] = Counter()
        self.artist_counts: Dict[str, int] = Counter()
        self.genre_counts: Dict[str, int] = Counter()

    def update_stats(self, audio_files: Dict[str, AudioFile]):
        """Update statistics based on current audio files"""
        self.total_files = len(audio_files)
        self.total_size = sum(af.size for af in audio_files.values())
        
        self.format_counts.clear()
        self.tag_counts.clear()
        self.artist_counts.clear()
        self.genre_counts.clear()

        for audio_file in audio_files.values():
            self.format_counts[audio_file.extension] += 1
            if audio_file.tags:
                self.tag_counts.update(audio_file.tags)
            if audio_file.metadata.artist:
                self.artist_counts[audio_file.metadata.artist] += 1
            if audio_file.metadata.genre:
                self.genre_counts[audio_file.metadata.genre] += 1

    def get_summary(self) -> Dict:
        """Get summary statistics"""
        return {
            'total_files': self.total_files,
            'total_size': self._format_size(self.total_size),
            'formats': dict(self.format_counts.most_common()),
            'top_tags': dict(self.tag_counts.most_common(10)),
            'top_artists': dict(self.artist_counts.most_common(10)),
            'top_genres': dict(self.genre_counts.most_common(10))
        }

    def _format_size(self, size: int) -> str:
        """Format size in bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB" 