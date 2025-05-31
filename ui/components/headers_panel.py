"""
HTTP Headers configuration panel
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable

class HeadersPanel:
    """Panel for managing HTTP headers"""
    
    def __init__(self, parent, on_change_callback: Callable[[Dict[str, str]], None]):
        self.parent = parent
        self.on_change_callback = on_change_callback
        self.header_entries = []
        
        self._create_widgets()
        self._setup_layout()
        self._add_initial_headers()
    
    def _create_widgets(self):
        """Create panel widgets"""
        # Title frame
        title_frame = ctk.CTkFrame(self.parent)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            title_frame,
            text="Headers",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10, pady=10)
        
        # Add button
        add_btn = ctk.CTkButton(
            title_frame,
            text="Add Header",
            width=100,
            command=self.add_header_field
        )
        add_btn.pack(side="right", padx=10, pady=10)
        
        # Headers table frame
        table_frame = ctk.CTkFrame(self.parent)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Column headers
        header_row = ctk.CTkFrame(table_frame)
        header_row.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header_row,
            text="Enabled",
            width=80,
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            header_row,
            text="Key",
            width=200,
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            header_row,
            text="Value",
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        # Scrollable frame for headers
        self.headers_scroll_frame = ctk.CTkScrollableFrame(table_frame)
        self.headers_scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def _setup_layout(self):
        """Setup layout"""
        pass
    
    def _add_initial_headers(self):
        """Add some common headers as examples"""
        # Add empty header field
        self.add_header_field()
    
    def add_header_field(self, key: str = "", value: str = "", enabled: bool = True):
        """Add a new header field"""
        header_frame = ctk.CTkFrame(self.headers_scroll_frame)
        header_frame.pack(fill="x", pady=2)
        
        # Enabled checkbox
        enabled_var = tk.BooleanVar(value=enabled)
        enabled_check = ctk.CTkCheckBox(
            header_frame,
            text="",
            variable=enabled_var,
            width=80,
            command=self._notify_change
        )
        enabled_check.pack(side="left", padx=(0, 10))
        
        # Key entry
        key_entry = ctk.CTkEntry(
            header_frame,
            width=200,
            placeholder_text="Header name"
        )
        key_entry.pack(side="left", padx=(0, 10))
        key_entry.insert(0, key)
        
        # Value entry
        value_entry = ctk.CTkEntry(
            header_frame,
            placeholder_text="Header value"
        )
        value_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        value_entry.insert(0, value)
        
        # Remove button
        remove_btn = ctk.CTkButton(
            header_frame,
            text="×",
            width=30,
            command=lambda: self.remove_header_field(header_frame, (enabled_var, key_entry, value_entry))
        )
        remove_btn.pack(side="right")
        
        # Store reference
        header_entry = (enabled_var, key_entry, value_entry)
        self.header_entries.append(header_entry)
        
        # Bind change events
        key_entry.bind('<KeyRelease>', lambda e: self._notify_change())
        value_entry.bind('<KeyRelease>', lambda e: self._notify_change())
        
        return header_entry
    
    def remove_header_field(self, header_frame, header_entry):
        """Remove a header field"""
        header_frame.destroy()
        if header_entry in self.header_entries:
            self.header_entries.remove(header_entry)
        self._notify_change()
    
    def _notify_change(self):
        """Notify parent of changes"""
        headers = self.get_headers()
        self.on_change_callback(headers)
    
    def get_headers(self) -> Dict[str, str]:
        """Get current headers as dictionary"""
        headers = {}
        for enabled_var, key_entry, value_entry in self.header_entries:
            if enabled_var.get():  # Only include enabled headers
                key = key_entry.get().strip()
                value = value_entry.get().strip()
                if key:  # Only include headers with non-empty keys
                    headers[key] = value
        return headers
    
    def set_headers(self, headers: Dict[str, str]):
        """Set headers from dictionary"""
        # Clear existing headers
        self.clear()
        
        # Add headers from dictionary
        for key, value in headers.items():
            self.add_header_field(key, value, True)
        
        # Add empty field for new headers
        if headers:
            self.add_header_field()
    
    def load_headers(self, headers: Dict[str, str]):
        """Load headers into the panel"""
        self.set_headers(headers)
    
    def clear(self):
        """Clear all headers"""
        for enabled_var, key_entry, value_entry in self.header_entries:
            key_entry.master.destroy()
        self.header_entries.clear()
        self.add_header_field()
    
    def add_common_header(self, header_type: str):
        """Add common headers"""
        common_headers = {
            'content-type-json': ('Content-Type', 'application/json'),
            'content-type-form': ('Content-Type', 'application/x-www-form-urlencoded'),
            'accept-json': ('Accept', 'application/json'),
            'user-agent': ('User-Agent', 'API-Tester/1.0'),
            'authorization': ('Authorization', 'Bearer '),
            'cache-control': ('Cache-Control', 'no-cache')
        }
        
        if header_type in common_headers:
            key, value = common_headers[header_type]
            self.add_header_field(key, value, True)
    
    def get_header_suggestions(self) -> list:
        """Get list of common header suggestions"""
        return [
            'Accept',
            'Accept-Encoding',
            'Accept-Language',
            'Authorization',
            'Cache-Control',
            'Content-Type',
            'Cookie',
            'Host',
            'If-Modified-Since',
            'If-None-Match',
            'Origin',
            'Referer',
            'User-Agent',
            'X-API-Key',
            'X-Forwarded-For',
            'X-Requested-With'
        ]
