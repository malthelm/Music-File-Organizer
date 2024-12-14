from typing import Dict
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedStyle

class ThemeManager:
    LIGHT_THEME = {
        'background': '#ffffff',
        'foreground': '#000000',
        'selected': '#0078d7',
        'hover': '#e5f3ff',
        'accent': '#0078d7',
        'text': '#000000',
        'border': '#cccccc'
    }
    
    DARK_THEME = {
        'background': '#1e1e1e',
        'foreground': '#ffffff',
        'selected': '#264f78',
        'hover': '#2d2d2d',
        'accent': '#0078d7',
        'text': '#d4d4d4',
        'border': '#404040'
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.style = ThemedStyle(root)
        self.current_theme = 'light'
        self._configure_base_styles()

    def _configure_base_styles(self):
        """Configure base styles for the application"""
        self.style.configure(
            'Custom.TFrame',
            background=self.LIGHT_THEME['background']
        )
        self.style.configure(
            'Custom.TLabel',
            background=self.LIGHT_THEME['background'],
            foreground=self.LIGHT_THEME['text']
        )
        self.style.configure(
            'Custom.TButton',
            background=self.LIGHT_THEME['accent'],
            foreground=self.LIGHT_THEME['text']
        )
        # Configure more widget styles...

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.current_theme == 'light':
            self._apply_theme(self.DARK_THEME)
            self.current_theme = 'dark'
        else:
            self._apply_theme(self.LIGHT_THEME)
            self.current_theme = 'light'

    def _apply_theme(self, theme: Dict[str, str]):
        """Apply the specified theme to all widgets"""
        self.style.configure(
            'Custom.TFrame',
            background=theme['background']
        )
        self.style.configure(
            'Custom.TLabel',
            background=theme['background'],
            foreground=theme['text']
        )
        self.style.configure(
            'Custom.TButton',
            background=theme['accent'],
            foreground=theme['text']
        )
        
        # Configure Treeview colors
        self.style.configure(
            'Treeview',
            background=theme['background'],
            foreground=theme['text'],
            fieldbackground=theme['background']
        )
        self.style.map(
            'Treeview',
            background=[('selected', theme['selected'])],
            foreground=[('selected', theme['text'])]
        )
        
        # Update other widgets...
        self.root.configure(bg=theme['background']) 