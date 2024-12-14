import customtkinter as ctk
import darkdetect
from gui.music_organizer_gui import ModernMusicGUI

if __name__ == "__main__":
    # Set appearance mode based on system
    ctk.set_appearance_mode("system")
    # Use macOS native system theme
    ctk.set_default_color_theme("blue")
    
    # Create the root window with native macOS styling
    root = ctk.CTk()
    root.configure(fg_color=("white", "gray14"))
    
    # Set window attributes
    root.title("Music Organizer")
    root.minsize(900, 600)
    
    # Create and run the app
    app = ModernMusicGUI(root)
    root.mainloop() 