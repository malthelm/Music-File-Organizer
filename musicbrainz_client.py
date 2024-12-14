import musicbrainzngs
from typing import Dict, Optional
import logging

class MusicBrainzClient:
    def __init__(self):
        # Set up MusicBrainz API
        musicbrainzngs.set_useragent(
            "MusicFileOrganizer",
            "1.0",
            "https://github.com/yourusername/music-file-organizer"
        )
    
    def search_track(self, title: str, artist: str = None) -> Optional[Dict]:
        """Search for a track in MusicBrainz database"""
        try:
            query = f'recording:"{title}"'
            if artist:
                query += f' AND artist:"{artist}"'
            
            result = musicbrainzngs.search_recordings(query=query, limit=1)
            
            if result['recording-list']:
                recording = result['recording-list'][0]
                return {
                    'title': recording.get('title', ''),
                    'artist': recording.get('artist-credit-phrase', ''),
                    'album': recording.get('release-list', [{}])[0].get('title', ''),
                    'year': recording.get('release-list', [{}])[0].get('date', '')[:4],
                    'genre': recording.get('tag-list', [{}])[0].get('name', '') if recording.get('tag-list') else ''
                }
            return None
        except Exception as e:
            logging.error(f"MusicBrainz search error: {e}")
            return None

    def fetch_album_art(self, album: str, artist: str) -> Optional[str]:
        """Fetch album art URL from MusicBrainz"""
        try:
            result = musicbrainzngs.search_releases(
                release=album,
                artist=artist,
                limit=1
            )
            
            if result['release-list']:
                release_id = result['release-list'][0]['id']
                release = musicbrainzngs.get_release_by_id(
                    release_id,
                    includes=['artwork']
                )
                
                if 'cover-art-archive' in release['release']:
                    art = release['release']['cover-art-archive']
                    if art['front']:
                        return f"https://coverartarchive.org/release/{release_id}/front"
            return None
        except Exception as e:
            logging.error(f"Album art fetch error: {e}")
            return None 