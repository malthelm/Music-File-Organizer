import librosa
import numpy as np
from typing import Dict, List, Tuple
import essentia
import essentia.standard as es
from concurrent.futures import ThreadPoolExecutor
import logging

class AdvancedAudioAnalyzer:
    def __init__(self):
        self.extractor = es.MusicExtractor()
        self.key_detector = es.KeyExtractor()
        self.rhythm_extractor = es.RhythmExtractor2013()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize essentia algorithms for mood analysis
        self.energy = es.Energy()
        self.loudness = es.Loudness()
        self.spectral_contrast = es.SpectralContrast()
        
    def analyze_file(self, file_path: str) -> Dict:
        """Perform comprehensive audio analysis"""
        try:
            # Basic analysis with librosa
            y, sr = librosa.load(file_path)
            
            # Run analyses in parallel
            futures = [
                self.executor.submit(self._analyze_rhythm, y, sr),
                self.executor.submit(self._analyze_key, y, sr),
                self.executor.submit(self._analyze_mood, y, sr),
                self.executor.submit(self._analyze_spectral, y, sr)
            ]
            
            # Combine results
            results = {}
            for future in futures:
                results.update(future.result())
                
            return results
            
        except Exception as e:
            logging.error(f"Analysis error for {file_path}: {e}")
            return {}
            
    def _analyze_mood(self, y: np.ndarray, sr: int) -> Dict:
        """Analyze mood and emotion using spectral features"""
        # Convert to mono if needed
        if len(y.shape) > 1:
            y = np.mean(y, axis=1)
            
        # Energy and loudness features
        energy = float(np.mean(librosa.feature.rms(y=y)[0]))
        spectral = librosa.feature.spectral_contrast(y=y, sr=sr)
        
        # Calculate mood features
        mood_features = {
            'energy': energy,
            'mood_aggressive': float(np.mean(spectral[0])),  # Low frequency contrast
            'mood_happy': float(np.mean(spectral[1:3])),     # Mid frequency contrast
            'mood_relaxed': float(np.mean(spectral[3:]))     # High frequency contrast
        }
        
        # Normalize values
        max_val = max(mood_features.values())
        if max_val > 0:
            mood_features = {k: v/max_val for k, v in mood_features.items()}
        
        return mood_features
        
    def _analyze_rhythm(self, y: np.ndarray, sr: int) -> Dict:
        """Analyze rhythm features"""
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        # Additional rhythm features
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr)
        
        return {
            'tempo': float(tempo),
            'beat_positions': beats.tolist(),
            'rhythm_strength': float(np.mean(pulse)),
            'rhythm_regularity': float(np.std(np.diff(beats)))
        }
        
    def _analyze_key(self, y: np.ndarray, sr: int) -> Dict:
        """Analyze key and harmony"""
        chromagram = librosa.feature.chroma_cqt(y=y, sr=sr)
        key, scale = librosa.estimate_key(y, sr)
        
        return {
            'key': key,
            'scale': scale,
            'key_strength': float(np.max(np.mean(chromagram, axis=1)))
        }
        
    def _analyze_spectral(self, y: np.ndarray, sr: int) -> Dict:
        """Analyze spectral features"""
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        
        return {
            'brightness': float(np.mean(spectral_centroids)),
            'warmth': float(np.mean(spectral_rolloff)),
            'spectral_complexity': float(np.std(spectral_centroids))
        }

    def find_similar_tracks(self, reference: str, candidates: List[str]) -> List[Tuple[str, float]]:
        """Find similar tracks using audio features"""
        try:
            ref_features = self._extract_features(reference)
            
            # Process candidates in parallel
            with ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(self._calculate_similarity, ref_features, c): c 
                    for c in candidates
                }
                
                similarities = []
                for future in futures:
                    candidate = futures[future]
                    try:
                        similarity = future.result()
                        similarities.append((candidate, similarity))
                    except Exception as e:
                        logging.error(f"Error comparing {candidate}: {e}")
                        
            return sorted(similarities, key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logging.error(f"Error finding similar tracks: {e}")
            return []
            
    def _extract_features(self, file_path: str) -> np.ndarray:
        """Extract feature vector for similarity comparison"""
        y, sr = librosa.load(file_path)
        
        # Extract various features
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        spectral = librosa.feature.spectral_contrast(y=y, sr=sr)
        
        # Combine features
        features = np.concatenate([
            np.mean(mfcc, axis=1),
            np.mean(chroma, axis=1),
            np.mean(spectral, axis=1)
        ])
        
        return features
        
    def _calculate_similarity(self, feat1: np.ndarray, feat2: np.ndarray) -> float:
        """Calculate similarity between feature vectors"""
        # Normalize features
        feat1_norm = feat1 / np.linalg.norm(feat1)
        feat2_norm = feat2 / np.linalg.norm(feat2)
        
        # Calculate cosine similarity
        similarity = np.dot(feat1_norm, feat2_norm)
        
        return float(similarity)