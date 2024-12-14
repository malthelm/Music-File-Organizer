import xmltodict
from dataclasses import dataclass
from typing import List, Dict, Optional
import os

@dataclass
class RekordboxTrack:
    id: str
    name: str
    artist: str
    album: str
    genre: str
    bpm: float
    key: str
    rating: int
    location: str
    hot_cues: List[Dict]
    memory_points: List[Dict]
    beat_grid: List[Dict]

class RekordboxManager:
    def __init__(self):
        self.library = {}
        self.playlists = {}
        
    def import_library(self, xml_path: str):
        """Import Rekordbox XML library"""
        with open(xml_path, 'r', encoding='utf-8') as f:
            data = xmltodict.parse(f.read())
            
        # Parse tracks
        tracks = data['DJ_PLAYLISTS']['COLLECTION']['TRACK']
        for track in tracks:
            rb_track = RekordboxTrack(
                id=track['@TrackID'],
                name=track.get('@Name', ''),
                artist=track.get('@Artist', ''),
                album=track.get('@Album', ''),
                genre=track.get('@Genre', ''),
                bpm=float(track.get('@AverageBpm', 0)),
                key=track.get('@Tonality', ''),
                rating=int(track.get('@Rating', 0)),
                location=track.get('@Location', ''),
                hot_cues=self._parse_cues(track.get('POSITION_MARK', [])),
                memory_points=self._parse_memory(track.get('POSITION_MARK', [])),
                beat_grid=self._parse_beatgrid(track.get('TEMPO', []))
            )
            self.library[rb_track.id] = rb_track
            
        # Parse playlists
        playlists = data['DJ_PLAYLISTS']['PLAYLISTS']['NODE']
        self._parse_playlists(playlists)
    
    def _parse_cues(self, cues: List[Dict]) -> List[Dict]:
        """Parse hot cues from Rekordbox data"""
        if not cues:
            return []
        return [
            {
                'position': float(cue.get('@Start', 0)),
                'name': cue.get('@Name', ''),
                'type': cue.get('@Type', 'cue'),
                'color': cue.get('@Color', '#ffffff')
            }
            for cue in (cues if isinstance(cues, list) else [cues])
            if cue.get('@Type') == '0'  # Hot cues
        ]

    def _parse_memory(self, points: List[Dict]) -> List[Dict]:
        """Parse memory points from Rekordbox data"""
        if not points:
            return []
        return [
            {
                'position': float(point.get('@Start', 0)),
                'name': point.get('@Name', ''),
                'color': point.get('@Color', '#ffffff')
            }
            for point in (points if isinstance(points, list) else [points])
            if point.get('@Type') == '1'  # Memory points
        ]

    def _parse_beatgrid(self, tempo_data: List[Dict]) -> List[Dict]:
        """Parse beat grid from Rekordbox data"""
        if not tempo_data:
            return []
        
        beatgrid = []
        current_bpm = 0
        current_beat = 0
        
        for tempo in tempo_data:
            bpm = float(tempo.get('@Bpm', 0))
            position = float(tempo.get('@Inizio', 0))
            
            if bpm != current_bpm:
                beatgrid.append({
                    'position': position,
                    'bpm': bpm,
                    'beat': current_beat
                })
                current_bpm = bpm
                
            current_beat += 1
            
        return beatgrid

    def _parse_playlists(self, nodes: List[Dict], parent: str = ''):
        """Recursively parse playlist structure"""
        if not nodes:
            return
        
        for node in (nodes if isinstance(nodes, list) else [nodes]):
            playlist_type = node.get('@Type', '')
            name = node.get('@Name', '')
            
            if playlist_type == '0':  # Folder
                self._parse_playlists(node.get('NODE', []), f"{parent}/{name}")
            else:  # Playlist
                tracks = node.get('TRACK', [])
                if tracks:
                    self.playlists[f"{parent}/{name}"] = [
                        track.get('@Key', '') 
                        for track in (tracks if isinstance(tracks, list) else [tracks])
                    ]

    def export_library(self, output_path: str):
        """Export library to Rekordbox XML format"""
        library_data = {
            'DJ_PLAYLISTS': {
                '@Version': '1.0',
                'COLLECTION': {
                    'TRACK': [
                        {
                            '@TrackID': track.id,
                            '@Name': track.name,
                            '@Artist': track.artist,
                            '@Album': track.album,
                            '@Genre': track.genre,
                            '@AverageBpm': str(track.bpm),
                            '@Tonality': track.key,
                            '@Rating': str(track.rating),
                            '@Location': track.location,
                            'POSITION_MARK': [
                                *[{
                                    '@Type': '0',
                                    '@Start': str(cue['position']),
                                    '@Name': cue['name'],
                                    '@Color': cue['color']
                                } for cue in track.hot_cues],
                                *[{
                                    '@Type': '1',
                                    '@Start': str(point['position']),
                                    '@Name': point['name'],
                                    '@Color': point['color']
                                } for point in track.memory_points]
                            ],
                            'TEMPO': [
                                {
                                    '@Inizio': str(beat['position']),
                                    '@Bpm': str(beat['bpm']),
                                    '@Battito': str(beat['beat'])
                                }
                                for beat in track.beat_grid
                            ]
                        }
                        for track in self.library.values()
                    ]
                },
                'PLAYLISTS': self._export_playlists()
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            xmltodict.unparse(library_data, output=f, pretty=True)

    def _export_playlists(self) -> Dict:
        """Convert playlists to Rekordbox XML format"""
        def create_playlist_node(path: str, tracks: List[str]) -> Dict:
            return {
                '@Type': '1',
                '@Name': path.split('/')[-1],
                'TRACK': [{'@Key': track_id} for track_id in tracks]
            }
        
        def create_folder_node(name: str, contents: List[Dict]) -> Dict:
            return {
                '@Type': '0',
                '@Name': name,
                'NODE': contents
            }
        
        # Group playlists by folder structure
        folder_structure = {}
        for path, tracks in self.playlists.items():
            parts = path.strip('/').split('/')
            current = folder_structure
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = tracks
        
        # Convert structure to Rekordbox format
        def convert_structure(structure: Dict) -> List[Dict]:
            nodes = []
            for name, content in structure.items():
                if isinstance(content, dict):
                    nodes.append(create_folder_node(name, convert_structure(content)))
                else:
                    nodes.append(create_playlist_node(name, content))
            return nodes
        
        return {'NODE': convert_structure(folder_structure)}

    def export_to_rekordbox(self, output_path: str, playlists: Dict[str, List[str]]):
        """Export library and playlists to Rekordbox XML"""
        # Create XML structure
        data = {
            'DJ_PLAYLISTS': {
                '@Version': '1.0',
                'PRODUCT': {
                    '@Name': 'Music Organizer',
                    '@Version': '1.0',
                    '@Company': 'Custom Software'
                },
                'COLLECTION': {'TRACK': []},
                'PLAYLISTS': {'NODE': []}
            }
        }
        
        # Add tracks
        track_id = 1
        track_map = {}  # Map file paths to track IDs
        
        for file_path, audio_file in self.library.items():
            track_data = {
                '@TrackID': str(track_id),
                '@Name': audio_file.metadata.title or os.path.basename(file_path),
                '@Artist': audio_file.metadata.artist,
                '@Album': audio_file.metadata.album,
                '@Genre': audio_file.metadata.genre,
                '@Kind': audio_file.extension[1:].upper(),
                '@Size': str(audio_file.size),
                '@Location': f"file://localhost{file_path}",
                '@AverageBpm': str(audio_file.metadata.bpm),
                '@Tonality': audio_file.metadata.key,
                '@Rating': '0',
                'TEMPO': [],
                'POSITION_MARK': []
            }
            
            # Add beat grid if available
            if hasattr(audio_file.metadata, 'beat_grid'):
                for beat in audio_file.metadata.beat_grid:
                    track_data['TEMPO'].append({
                        '@Inizio': str(beat['position']),
                        '@Bpm': str(beat['bpm']),
                        '@Metro': '4/4',
                        '@Battito': str(beat['beat'])
                    })
                    
            # Add hot cues if available
            if hasattr(audio_file.metadata, 'hot_cues'):
                for i, cue in enumerate(audio_file.metadata.hot_cues):
                    track_data['POSITION_MARK'].append({
                        '@Name': cue.get('name', f'Hot Cue {i+1}'),
                        '@Type': '0',
                        '@Start': str(cue['position']),
                        '@Num': str(i),
                        '@Red': '40',
                        '@Green': '226',
                        '@Blue': '20'
                    })
                    
            data['DJ_PLAYLISTS']['COLLECTION']['TRACK'].append(track_data)
            track_map[file_path] = track_id
            track_id += 1
            
        # Add playlists
        for name, tracks in playlists.items():
            playlist_node = {
                '@Name': name,
                '@Type': '0',
                'TRACK': []
            }
            
            for track_path in tracks:
                if track_path in track_map:
                    playlist_node['TRACK'].append({
                        '@Key': str(track_map[track_path])
                    })
                    
            data['DJ_PLAYLISTS']['PLAYLISTS']['NODE'].append(playlist_node)
            
        # Write XML file
        with open(output_path, 'w', encoding='utf-8') as f:
            xmltodict.unparse(data, output=f, pretty=True)