import librosa
import numpy as np
import essentia
import essentia.standard as es
from typing import Dict, Tuple

class AudioAnalyzer:
    def __init__(self):
        self.analyzer = es.MusicExtractor()
        
    def analyze_track(self, file_path: str) -> Dict:
        """Perform comprehensive audio analysis"""
        # Load audio file
        y, sr = librosa.load(file_path)
        
        # Basic analysis
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        chromagram = librosa.feature.chroma_cqt(y=y, sr=sr)
        
        # Advanced analysis using essentia
        features, features_frames = self.analyzer(file_path)
        
        return {
            'bpm': tempo,
            'key': self._estimate_key(chromagram),
            'energy': features['lowlevel.average_loudness'],
            'danceability': features['rhythm.danceability'],
            'beats': beats.tolist(),
            'mood': {
                'happy': features['mood_happy'],
                'aggressive': features['mood_aggressive'],
                'relaxed': features['mood_relaxed']
            }
        }
    
    def generate_waveform(self, file_path: str) -> np.ndarray:
        """Generate waveform visualization data"""
        y, sr = librosa.load(file_path)
        return librosa.feature.melspectrogram(y=y, sr=sr) 