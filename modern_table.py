import customtkinter as ctk
import tkinter as tk
from typing import List, Dict, Any, Callable

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