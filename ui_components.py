import customtkinter as ctk
from typing import Callable, Optional, List, Dict, Any
import math
import json
import tkinter as tk

class ModernTable(ctk.CTkFrame):
    def __init__(self, master, columns: List[Dict[str, Any]], **kwargs):
        super().__init__(master, **kwargs)
        
        self.columns = columns
        self.rows = []
        self.selected_items = set()
        self.sort_column = None
        self.sort_reverse = False
        
        # Create header
        self.header = ctk.CTkFrame(self)
        self.header.pack(fill=tk.X, pady=(0, 5))
        
        # Configure column weights
        for i, col in enumerate(columns):
            self.header.grid_columnconfigure(i, weight=col.get('weight', 1))
            
            # Create header button
            btn = ctk.CTkButton(
                self.header,
                text=col['title'],
                command=lambda c=col['key']: self.sort_by(c),
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                height=30
            )
            btn.grid(row=0, column=i, sticky="ew", padx=1)
        
        # Create scrollable frame for rows
        self.container = ctk.CTkScrollableFrame(self)
        self.container.pack(fill=tk.BOTH, expand=True)

    def add_row(self, data: Dict[str, Any]):
        """Add a new row to the table"""
        row = ctk.CTkFrame(self.container)
        row.pack(fill=tk.X, pady=1)
        
        # Store data with row
        row.data = data
        
        for i, col in enumerate(self.columns):
            value = data.get(col['key'], '')
            
            # Create cell
            cell = ctk.CTkLabel(
                row,
                text=str(value),
                anchor='w',
                padx=10
            )
            cell.grid(row=0, column=i, sticky="ew")
            
        # Configure row weights
        for i in range(len(self.columns)):
            row.grid_columnconfigure(i, weight=self.columns[i].get('weight', 1))
            
        # Bind selection
        row.bind('<Button-1>', lambda e, r=row: self.select_row(r))
        row.bind('<Control-Button-1>', lambda e, r=row: self.toggle_selection(r))
        row.bind('<Shift-Button-1>', lambda e, r=row: self.extend_selection(r))
        
        self.rows.append(row)
        return row

    def select_row(self, row):
        """Select a single row"""
        self.clear_selection()
        self._highlight_row(row)
        self.selected_items = {row}

    def toggle_selection(self, row):
        """Toggle row selection (for Ctrl+click)"""
        if row in self.selected_items:
            self._unhighlight_row(row)
            self.selected_items.remove(row)
        else:
            self._highlight_row(row)
            self.selected_items.add(row)

    def extend_selection(self, row):
        """Extend selection to row (for Shift+click)"""
        if not self.selected_items:
            self.select_row(row)
            return
            
        # Find range
        start_idx = min(self.rows.index(r) for r in self.selected_items)
        end_idx = self.rows.index(row)
        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx
            
        # Select range
        self.clear_selection()
        for i in range(start_idx, end_idx + 1):
            self._highlight_row(self.rows[i])
            self.selected_items.add(self.rows[i])

    def clear_selection(self):
        """Clear all selections"""
        for row in self.selected_items:
            self._unhighlight_row(row)
        self.selected_items.clear()

    def _highlight_row(self, row):
        """Highlight a row"""
        row.configure(fg_color=("gray75", "gray25"))

    def _unhighlight_row(self, row):
        """Remove highlight from a row"""
        row.configure(fg_color="transparent")

    def sort_by(self, key: str):
        """Sort table by column"""
        if self.sort_column == key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = key
            self.sort_reverse = False
            
        # Sort rows
        self.rows.sort(
            key=lambda r: r.data.get(key, ''),
            reverse=self.sort_reverse
        )
        
        # Repack rows
        for row in self.rows:
            row.pack_forget()
            row.pack(fill=tk.X, pady=1)

    def get_selected_data(self) -> List[Dict[str, Any]]:
        """Get data from selected rows"""
        return [row.data for row in self.selected_items]

    def clear(self):
        """Clear all rows"""
        for row in self.rows:
            row.destroy()
        self.rows.clear()
        self.selected_items.clear()

    def get_children(self):
        """Get all row widgets"""
        return self.rows

    def identify_row(self, y: int) -> Optional[ctk.CTkFrame]:
        """Identify row at given y coordinate"""
        for row in self.rows:
            bbox = row.bbox()
            if bbox and bbox[1] <= y <= bbox[1] + bbox[3]:
                return row
        return None

    def index(self, row: ctk.CTkFrame) -> int:
        """Get index of row"""
        return self.rows.index(row)

    def move(self, row: ctk.CTkFrame, target_index: int):
        """Move row to new position"""
        if 0 <= target_index < len(self.rows):
            self.rows.remove(row)
            self.rows.insert(target_index, row)
            self._repack_rows()

    def _repack_rows(self):
        """Repack all rows in current order"""
        for row in self.rows:
            row.pack_forget()
            row.pack(fill=tk.X, pady=1)

class WaveformView(ctk.CTkCanvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.waveform_data = None
        self.peaks = []
        self.configure(bg='black', highlightthickness=0)
        self.bind('<Configure>', self.redraw)

    def set_waveform(self, data):
        self.waveform_data = data
        self.redraw()

    def redraw(self, event=None):
        self.delete('all')
        if not self.waveform_data:
            return

        width = self.winfo_width()
        height = self.winfo_height()
        
        # Draw background
        self.create_rectangle(0, 0, width, height, fill='#1E1E1E', outline='')
        
        # Calculate waveform
        samples_per_pixel = len(self.waveform_data) / width
        self.peaks = []
        
        for x in range(width):
            start = int(x * samples_per_pixel)
            end = int((x + 1) * samples_per_pixel)
            peak = max(abs(self.waveform_data[start:end]))
            self.peaks.append(peak)
            
            # Draw peak
            peak_height = peak * height / 2
            self.create_line(
                x, height/2 - peak_height,
                x, height/2 + peak_height,
                fill='#0078D4',
                width=1
            )

class ModernSlider(ctk.CTkSlider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(
            button_color='#0078D4',
            button_hover_color='#106EBE',
            progress_color='#0078D4',
            fg_color='#333333'
        )

class ModernButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(
            corner_radius=6,
            fg_color='#0078D4',
            hover_color='#106EBE',
            text_color='white'
        )

class SidebarButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(
            corner_radius=0,
            fg_color='transparent',
            hover_color='#333333',
            anchor='w',
            height=40
        )

class DraggableTable(ModernTable):
    def enable_drag_drop(self):
        self.drag_source_register('*')
        self.drop_target_register('*')
        self.dnd_bind('<<DragInitCmd>>', self._drag_init)
        self.dnd_bind('<<DragEndCmd>>', self._drag_end)
        self.dnd_bind('<<DropEnter>>', self._drop_enter)
        self.dnd_bind('<<DropPosition>>', self._drop_position)
        self.dnd_bind('<<Drop>>', self._drop)
        
    def _drag_init(self, event):
        # Get selected items
        selection = self.get_selected_data()
        if not selection:
            return
            
        # Prepare drag data
        data = json.dumps({
            'type': 'table_rows',
            'items': selection
        })
        
        return (COPY, data)
        
    def _drop_enter(self, event):
        return event.action
        
    def _drop_position(self, event):
        return event.action
        
    def _drop(self, event):
        try:
            data = json.loads(event.data)
            if data['type'] == 'table_rows':
                self.handle_drop(data['items'])
        except:
            pass
            
        return event.action