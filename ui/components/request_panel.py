"""
Request body configuration panel
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import json
from typing import Callable, Optional

from models.request_model import APIRequest
from utils.json_formatter import JSONFormatter

class RequestPanel:
    """Panel for configuring request body"""
    
    def __init__(self, parent, on_change_callback: Callable[[str, str], None]):
        self.parent = parent
        self.on_change_callback = on_change_callback
        self.json_formatter = JSONFormatter()
        
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
    
    def _create_widgets(self):
        """Create panel widgets"""
        # Body type selection
        self.type_frame = ctk.CTkFrame(self.parent)
        self.type_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(self.type_frame, text="Body Type:").pack(side="left", padx=10, pady=10)
        
        self.body_type_var = tk.StringVar(value="json")
        self.body_type_dropdown = ctk.CTkOptionMenu(
            self.type_frame,
            variable=self.body_type_var,
            values=["json", "raw", "form-data", "x-www-form-urlencoded"],
            width=200,
            command=self.on_body_type_changed
        )
        self.body_type_dropdown.pack(side="left", padx=10, pady=10)
        
        # Format button for JSON
        self.format_btn = ctk.CTkButton(
            self.type_frame,
            text="Format JSON",
            width=100,
            command=self.format_json
        )
        self.format_btn.pack(side="right", padx=10, pady=10)
        
        # Body content area
        self.content_frame = ctk.CTkFrame(self.parent)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Text editor for body
        self._create_text_editor()
        
        # Form data editor (hidden by default)
        self._create_form_editor()
        
        # Show appropriate editor
        self.show_text_editor()
    
    def _create_text_editor(self):
        """Create text editor for raw/JSON content"""
        self.text_frame = ctk.CTkFrame(self.content_frame)
        
        # Text widget with scrollbar
        self.text_widget = tk.Text(
            self.text_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#212121",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#2196F3",
            relief="flat",
            borderwidth=0
        )
        
        self.text_scrollbar = ctk.CTkScrollbar(
            self.text_frame,
            command=self.text_widget.yview
        )
        self.text_widget.configure(yscrollcommand=self.text_scrollbar.set)
        
        # Pack text editor
        self.text_scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.text_widget.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Bind text change events
        self.text_widget.bind('<KeyRelease>', self.on_text_changed)
        self.text_widget.bind('<Button-1>', self.on_text_changed)
    
    def _create_form_editor(self):
        """Create form data editor"""
        self.form_frame = ctk.CTkFrame(self.content_frame)
        
        # Header
        header_frame = ctk.CTkFrame(self.form_frame)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Key", width=200).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(header_frame, text="Value").pack(side="left", padx=(0, 10))
        
        # Scrollable frame for form fields
        self.form_scroll_frame = ctk.CTkScrollableFrame(self.form_frame)
        self.form_scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Form entries list
        self.form_entries = []
        
        # Add button
        add_btn = ctk.CTkButton(
            self.form_frame,
            text="Add Field",
            command=self.add_form_field
        )
        add_btn.pack(pady=10)
        
        # Add initial field
        self.add_form_field()
    
    def _setup_layout(self):
        """Setup layout"""
        pass
    
    def _setup_bindings(self):
        """Setup event bindings"""
        pass
    
    def on_body_type_changed(self, body_type: str):
        """Handle body type change"""
        if body_type in ["json", "raw"]:
            self.show_text_editor()
        else:
            self.show_form_editor()
        
        # Show/hide format button
        if body_type == "json":
            self.format_btn.pack(side="right", padx=10, pady=10)
        else:
            self.format_btn.pack_forget()
        
        self._notify_change()
    
    def show_text_editor(self):
        """Show text editor"""
        self.form_frame.pack_forget()
        self.text_frame.pack(fill="both", expand=True)
    
    def show_form_editor(self):
        """Show form data editor"""
        self.text_frame.pack_forget()
        self.form_frame.pack(fill="both", expand=True)
    
    def add_form_field(self):
        """Add a new form field"""
        field_frame = ctk.CTkFrame(self.form_scroll_frame)
        field_frame.pack(fill="x", pady=2)
        
        key_entry = ctk.CTkEntry(field_frame, width=200, placeholder_text="Key")
        key_entry.pack(side="left", padx=(0, 10))
        
        value_entry = ctk.CTkEntry(field_frame, placeholder_text="Value")
        value_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        remove_btn = ctk.CTkButton(
            field_frame,
            text="×",
            width=30,
            command=lambda: self.remove_form_field(field_frame, (key_entry, value_entry))
        )
        remove_btn.pack(side="right")
        
        # Bind change events
        key_entry.bind('<KeyRelease>', lambda e: self._notify_change())
        value_entry.bind('<KeyRelease>', lambda e: self._notify_change())
        
        self.form_entries.append((key_entry, value_entry))
    
    def remove_form_field(self, field_frame, entries):
        """Remove a form field"""
        field_frame.destroy()
        if entries in self.form_entries:
            self.form_entries.remove(entries)
        self._notify_change()
    
    def on_text_changed(self, event=None):
        """Handle text content change"""
        self._notify_change()
    
    def _notify_change(self):
        """Notify parent of changes"""
        body_type = self.body_type_var.get()
        body_content = self.get_body_content()
        self.on_change_callback(body_content, body_type)
    
    def get_body_content(self) -> str:
        """Get current body content"""
        body_type = self.body_type_var.get()
        
        if body_type in ["json", "raw"]:
            return self.text_widget.get("1.0", tk.END).strip()
        
        elif body_type in ["form-data", "x-www-form-urlencoded"]:
            form_data = {}
            for key_entry, value_entry in self.form_entries:
                key = key_entry.get().strip()
                value = value_entry.get().strip()
                if key:
                    form_data[key] = value
            
            if body_type == "form-data":
                return json.dumps(form_data)
            else:  # x-www-form-urlencoded
                from urllib.parse import urlencode
                return urlencode(form_data)
        
        return ""
    
    def set_body_content(self, content: str, body_type: str = None):
        """Set body content"""
        if body_type:
            self.body_type_var.set(body_type)
            self.on_body_type_changed(body_type)
        
        current_type = self.body_type_var.get()
        
        if current_type in ["json", "raw"]:
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", content)
        
        elif current_type in ["form-data", "x-www-form-urlencoded"]:
            # Clear existing form fields
            for key_entry, value_entry in self.form_entries:
                key_entry.master.destroy()
            self.form_entries.clear()
            
            # Parse content and populate form
            try:
                if current_type == "form-data":
                    data = json.loads(content) if content else {}
                else:  # x-www-form-urlencoded
                    from urllib.parse import parse_qs
                    parsed = parse_qs(content)
                    data = {k: v[0] if v else '' for k, v in parsed.items()}
                
                for key, value in data.items():
                    self.add_form_field()
                    key_entry, value_entry = self.form_entries[-1]
                    key_entry.insert(0, key)
                    value_entry.insert(0, str(value))
                
                # Add empty field if no data
                if not data:
                    self.add_form_field()
                    
            except Exception:
                # If parsing fails, add empty field
                self.add_form_field()
    
    def format_json(self):
        """Format JSON content"""
        if self.body_type_var.get() != "json":
            return
        
        content = self.text_widget.get("1.0", tk.END).strip()
        if not content:
            return
        
        try:
            formatted = self.json_formatter.format(content)
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", formatted)
        except Exception as e:
            tk.messagebox.showerror("JSON Format Error", f"Invalid JSON: {e}")
    
    def set_body_visible(self, visible: bool):
        """Show or hide the body panel"""
        if visible:
            self.parent.pack(fill="both", expand=True)
        else:
            self.parent.pack_forget()
    
    def clear(self):
        """Clear all content"""
        self.body_type_var.set("json")
        self.text_widget.delete("1.0", tk.END)
        
        # Clear form fields
        for key_entry, value_entry in self.form_entries:
            key_entry.master.destroy()
        self.form_entries.clear()
        self.add_form_field()
        
        self.show_text_editor()
    
    def load_request(self, request: APIRequest):
        """Load request data into panel"""
        self.set_body_content(request.body, request.body_type)
