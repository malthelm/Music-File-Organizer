import numpy as np
from typing import List, Tuple
import librosa
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import colorsys
import customtkinter as ctk
import cairo
from PIL import Image, ImageTk
import time

class TurellVisualizer(ctk.CTkCanvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg='black', highlightthickness=0)
        
        # Turrell-inspired color palettes
        self.color_palettes = {
            'dawn': [(0.05, 0.05, 0.2), (0.7, 0.4, 0.5), (1.0, 0.7, 0.4)],
            'dusk': [(0.2, 0.05, 0.3), (0.5, 0.1, 0.4), (0.8, 0.3, 0.5)],
            'ganzfeld': [(0.1, 0.1, 0.5), (0.3, 0.3, 0.8), (0.5, 0.5, 1.0)],
            'skyspace': [(0.0, 0.1, 0.3), (0.2, 0.4, 0.7), (0.5, 0.7, 1.0)]
        }
        
        self.current_palette = 'skyspace'
        self.transition_speed = 0.02
        self.color_position = 0.0
        
        # Audio analysis parameters
        self.frequency_bands = np.linspace(20, 20000, 4)  # 4 frequency bands
        self.smoothing = 0.3  # Color transition smoothing
        
        self.bind('<Configure>', self.on_resize)
        self.animation_frame = None
        self.surface = None
        self.context = None
        
    def on_resize(self, event):
        """Handle window resize"""
        self.setup_cairo_surface()
        self.redraw()
        
    def setup_cairo_surface(self):
        """Initialize Cairo surface for drawing"""
        width = self.winfo_width()
        height = self.winfo_height()
        
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.context = cairo.Context(self.surface)
        
    def update_visualization(self, audio_data: np.ndarray, sample_rate: int):
        """Update visualization with new audio data"""
        # Analyze frequency bands
        spectrum = np.fft.rfft(audio_data)
        freqs = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
        
        # Calculate energy in each band
        energies = []
        for i in range(len(self.frequency_bands)-1):
            mask = (freqs >= self.frequency_bands[i]) & (freqs < self.frequency_bands[i+1])
            energy = np.sum(np.abs(spectrum[mask])) / len(spectrum[mask]) if len(spectrum[mask]) > 0 else 0
            energies.append(energy)
        
        # Normalize energies
        energies = np.array(energies) / np.max(energies) if np.max(energies) > 0 else np.zeros_like(energies)
        
        # Update visualization
        self.update_colors(energies)
        self.redraw()
        
    def update_colors(self, energies: np.ndarray):
        """Update color transitions based on audio energy"""
        # Move through color palette based on audio energy
        self.color_position = (self.color_position + np.mean(energies) * self.transition_speed) % 1.0
        
    def redraw(self):
        """Redraw the visualization"""
        if not self.surface:
            return
            
        width = self.winfo_width()
        height = self.winfo_height()
        
        # Clear context
        self.context.save()
        self.context.set_source_rgb(0, 0, 0)
        self.context.paint()
        
        # Create Turrell-inspired gradient
        self._draw_turrell_effect(width, height)
        
        # Convert to Tkinter-compatible image
        self._update_canvas()
        
        # Schedule next frame
        self.animation_frame = self.after(33, self.redraw)  # ~30 FPS
        
    def _draw_turrell_effect(self, width: int, height: int):
        """Draw Turrell-inspired light effect"""
        # Get current color palette
        palette = self.color_palettes[self.current_palette]
        
        # Create radial gradient
        center_x = width / 2
        center_y = height / 2
        radius = max(width, height)
        
        # Calculate current colors based on position
        idx = int(self.color_position * (len(palette) - 1))
        next_idx = (idx + 1) % len(palette)
        t = self.color_position * (len(palette) - 1) - idx
        
        # Interpolate colors
        current_color = self._interpolate_colors(palette[idx], palette[next_idx], t)
        
        # Create gradient
        pat = cairo.RadialGradient(
            center_x, center_y, 0,
            center_x, center_y, radius
        )
        
        # Add color stops
        pat.add_color_stop_rgba(0, *current_color, 1.0)
        pat.add_color_stop_rgba(0.7, *self._adjust_color(current_color, -0.2), 0.8)
        pat.add_color_stop_rgba(1.0, *self._adjust_color(current_color, -0.4), 0.6)
        
        # Draw gradient
        self.context.set_source(pat)
        self.context.arc(center_x, center_y, radius, 0, 2 * np.pi)
        self.context.fill()
        
        # Add Turrell-style aperture effect
        self._draw_aperture(center_x, center_y, radius * 0.4)
        
    def _draw_aperture(self, x: float, y: float, radius: float):
        """Draw Turrell-style aperture"""
        # Create subtle glow effect
        for i in range(10):
            alpha = 0.1 - (i * 0.01)
            self.context.set_source_rgba(1, 1, 1, alpha)
            self.context.arc(x, y, radius + i*2, 0, 2 * np.pi)
            self.context.fill()
            
    def _interpolate_colors(self, color1: Tuple[float, float, float], 
                          color2: Tuple[float, float, float], 
                          t: float) -> Tuple[float, float, float]:
        """Smoothly interpolate between two colors"""
        # Convert to HSV for better interpolation
        hsv1 = colorsys.rgb_to_hsv(*color1)
        hsv2 = colorsys.rgb_to_hsv(*color2)
        
        # Interpolate in HSV space
        h = self._interpolate_angle(hsv1[0], hsv2[0], t)
        s = hsv1[1] + t * (hsv2[1] - hsv1[1])
        v = hsv1[2] + t * (hsv2[2] - hsv1[2])
        
        # Convert back to RGB
        return colorsys.hsv_to_rgb(h, s, v)
        
    def _interpolate_angle(self, a1: float, a2: float, t: float) -> float:
        """Interpolate between two angles (for hue)"""
        diff = (a2 - a1 + 0.5) % 1.0 - 0.5
        return (a1 + diff * t) % 1.0
        
    def _adjust_color(self, color: Tuple[float, float, float], amount: float) -> Tuple[float, float, float]:
        """Adjust color brightness"""
        return tuple(max(0, min(1, c + amount)) for c in color)
        
    def _update_canvas(self):
        """Update Tkinter canvas with Cairo surface"""
        data = self.surface.get_data()
        image = Image.frombuffer('RGBA', (self.surface.get_width(), self.surface.get_height()), data.tobytes(), 'raw', 'BGRA', 0, 1)
        photo = ImageTk.PhotoImage(image)
        
        # Update canvas
        self.create_image(0, 0, image=photo, anchor='nw')
        self.image = photo  # Keep reference
        
    def change_palette(self, palette_name: str):
        """Change color palette"""
        if palette_name in self.color_palettes:
            self.current_palette = palette_name
            
    def cleanup(self):
        """Clean up resources"""
        if self.animation_frame:
            self.after_cancel(self.animation_frame)

class AudioVisualizer:
    def __init__(self):
        self.fig = None
        self.canvas = None
        
    def create_spectrum_analyzer(self, master) -> FigureCanvasTkAgg:
        """Create a real-time spectrum analyzer"""
        self.fig = Figure(figsize=(6, 2), dpi=100)
        self.fig.patch.set_facecolor('#1E1E1E')
        
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#1E1E1E')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        
        # Initialize empty plot
        self.spectrum_line, = ax.plot([], [], color='#0078D4')
        ax.set_ylim(-60, 0)
        ax.set_xlim(0, 20000)
        ax.set_xscale('log')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        return self.canvas

    def update_spectrum(self, audio_data: np.ndarray, sample_rate: int):
        """Update spectrum analyzer with new audio data"""
        if self.fig is None:
            return
            
        # Calculate spectrum
        spectrum = np.fft.rfft(audio_data)
        freq = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
        magnitude = 20 * np.log10(np.abs(spectrum) + 1e-10)
        
        # Update plot
        self.spectrum_line.set_data(freq, magnitude)
        self.canvas.draw()

    def create_waveform(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Generate waveform data for visualization"""
        return librosa.feature.melspectrogram(y=audio_data, sr=sample_rate) 