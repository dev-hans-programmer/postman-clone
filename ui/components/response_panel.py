"""
Response display panel
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import json
from typing import Optional

from models.response_model import APIResponse
from utils.json_formatter import JSONFormatter

class ResponsePanel:
    """Panel for displaying API responses"""
    
    def __init__(self, parent):
        self.parent = parent
        self.json_formatter = JSONFormatter()
        self.current_response: Optional[APIResponse] = None
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create panel widgets"""
        # Title
        title_frame = ctk.CTkFrame(self.parent)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            title_frame,
            text="Response",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=10, pady=10)
        
        # Response tabs
        self.response_notebook = ctk.CTkTabview(self.parent)
        self.response_notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Add tabs
        self.response_notebook.add("Body")
        self.response_notebook.add("Headers")
        self.response_notebook.add("Info")
        
        # Create tab content
        self._create_body_tab()
        self._create_headers_tab()
        self._create_info_tab()
        
        # Initial state
        self.show_no_response()
    
    def _create_body_tab(self):
        """Create response body tab"""
        body_tab = self.response_notebook.tab("Body")
        
        # Toolbar
        toolbar_frame = ctk.CTkFrame(body_tab)
        toolbar_frame.pack(fill="x", padx=10, pady=10)
        
        # Format options
        self.format_var = tk.StringVar(value="Pretty")
        format_dropdown = ctk.CTkOptionMenu(
            toolbar_frame,
            variable=self.format_var,
            values=["Pretty", "Raw"],
            command=self.on_format_changed
        )
        format_dropdown.pack(side="left", padx=10, pady=5)
        
        # Copy button
        copy_btn = ctk.CTkButton(
            toolbar_frame,
            text="Copy",
            width=80,
            command=self.copy_response_body
        )
        copy_btn.pack(side="right", padx=10, pady=5)
        
        # Response body text area
        self.body_frame = ctk.CTkFrame(body_tab)
        self.body_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.body_text = tk.Text(
            self.body_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#212121",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#2196F3",
            relief="flat",
            borderwidth=0,
            state="disabled"
        )
        
        self.body_scrollbar = ctk.CTkScrollbar(
            self.body_frame,
            command=self.body_text.yview
        )
        self.body_text.configure(yscrollcommand=self.body_scrollbar.set)
        
        self.body_scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.body_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    
    def _create_headers_tab(self):
        """Create response headers tab"""
        headers_tab = self.response_notebook.tab("Headers")
        
        # Headers display frame
        self.headers_frame = ctk.CTkFrame(headers_tab)
        self.headers_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create treeview for headers
        self.headers_tree = ttk.Treeview(
            self.headers_frame,
            columns=("value",),
            show="tree headings",
            height=15
        )
        
        self.headers_tree.heading("#0", text="Header", anchor="w")
        self.headers_tree.heading("value", text="Value", anchor="w")
        
        self.headers_tree.column("#0", width=200, minwidth=150)
        self.headers_tree.column("value", width=400, minwidth=200)
        
        # Scrollbar for headers
        headers_scrollbar = ttk.Scrollbar(
            self.headers_frame,
            orient="vertical",
            command=self.headers_tree.yview
        )
        self.headers_tree.configure(yscrollcommand=headers_scrollbar.set)
        
        # Pack headers widgets
        headers_scrollbar.pack(side="right", fill="y")
        self.headers_tree.pack(side="left", fill="both", expand=True)
    
    def _create_info_tab(self):
        """Create response info tab"""
        info_tab = self.response_notebook.tab("Info")
        
        # Info display frame
        self.info_frame = ctk.CTkScrollableFrame(info_tab)
        self.info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Info labels will be created dynamically
        self.info_labels = {}
    
    def _setup_layout(self):
        """Setup layout"""
        pass
    
    def display_response(self, response: APIResponse):
        """Display response data"""
        self.current_response = response
        
        if response.error:
            self._show_error(response.error)
        else:
            self._show_response_body(response)
            self._show_response_headers(response)
            self._show_response_info(response)
    
    def _show_response_body(self, response: APIResponse):
        """Show response body"""
        self.body_text.configure(state="normal")
        self.body_text.delete("1.0", tk.END)
        
        if response.body:
            if self.format_var.get() == "Pretty" and response.is_json:
                try:
                    formatted = self.json_formatter.format(response.body)
                    self.body_text.insert("1.0", formatted)
                except Exception:
                    self.body_text.insert("1.0", response.body)
            else:
                self.body_text.insert("1.0", response.body)
        else:
            self.body_text.insert("1.0", "No response body")
        
        self.body_text.configure(state="disabled")
    
    def _show_response_headers(self, response: APIResponse):
        """Show response headers"""
        # Clear existing items
        for item in self.headers_tree.get_children():
            self.headers_tree.delete(item)
        
        # Add headers
        for header, value in response.headers.items():
            self.headers_tree.insert("", "end", text=header, values=(value,))
    
    def _show_response_info(self, response: APIResponse):
        """Show response information"""
        # Clear existing info
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        
        self.info_labels.clear()
        
        # Create info fields
        info_data = [
            ("Status Code", f"{response.status_code} {response.status_text}"),
            ("Response Time", response.formatted_time),
            ("Content Type", response.content_type),
            ("Content Size", response.formatted_size),
            ("Timestamp", response.timestamp)
        ]
        
        for i, (label, value) in enumerate(info_data):
            # Label
            label_widget = ctk.CTkLabel(
                self.info_frame,
                text=f"{label}:",
                font=ctk.CTkFont(weight="bold"),
                anchor="w"
            )
            label_widget.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            
            # Value
            value_widget = ctk.CTkLabel(
                self.info_frame,
                text=str(value),
                anchor="w"
            )
            value_widget.grid(row=i, column=1, sticky="w", padx=10, pady=5)
            
            self.info_labels[label] = value_widget
        
        # Configure grid weights
        self.info_frame.grid_columnconfigure(1, weight=1)
    
    def _show_error(self, error_msg: str):
        """Show error message"""
        # Show error in body tab
        self.body_text.configure(state="normal")
        self.body_text.delete("1.0", tk.END)
        self.body_text.insert("1.0", f"Error: {error_msg}")
        self.body_text.configure(state="disabled")
        
        # Clear headers
        for item in self.headers_tree.get_children():
            self.headers_tree.delete(item)
        
        # Show error info
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        
        error_label = ctk.CTkLabel(
            self.info_frame,
            text=f"Request failed: {error_msg}",
            text_color="red"
        )
        error_label.pack(padx=10, pady=10)
    
    def show_no_response(self):
        """Show no response state"""
        # Clear body
        self.body_text.configure(state="normal")
        self.body_text.delete("1.0", tk.END)
        self.body_text.insert("1.0", "Send a request to see the response here")
        self.body_text.configure(state="disabled")
        
        # Clear headers
        for item in self.headers_tree.get_children():
            self.headers_tree.delete(item)
        
        # Clear info
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        
        no_response_label = ctk.CTkLabel(
            self.info_frame,
            text="No response yet. Send a request to see response details here.",
            text_color="gray"
        )
        no_response_label.pack(padx=10, pady=10)
    
    def on_format_changed(self, format_type: str):
        """Handle format change"""
        if self.current_response:
            self._show_response_body(self.current_response)
    
    def copy_response_body(self):
        """Copy response body to clipboard"""
        if self.current_response and self.current_response.body:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(self.current_response.body)
    
    def clear_response(self):
        """Clear response display"""
        self.current_response = None
        self.show_no_response()
