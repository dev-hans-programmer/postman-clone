"""
Authentication configuration panel
"""

import customtkinter as ctk
import tkinter as tk
from typing import Dict, Callable
import base64

from models.request_model import AuthType

class AuthPanel:
    """Panel for configuring request authentication"""
    
    def __init__(self, parent, on_change_callback: Callable[[AuthType, Dict[str, str]], None]):
        self.parent = parent
        self.on_change_callback = on_change_callback
        
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
    
    def _create_widgets(self):
        """Create panel widgets"""
        # Title frame
        title_frame = ctk.CTkFrame(self.parent)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            title_frame,
            text="Authentication",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10, pady=10)
        
        # Auth type selection
        type_frame = ctk.CTkFrame(self.parent)
        type_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(type_frame, text="Type:").pack(side="left", padx=10, pady=10)
        
        self.auth_type_var = tk.StringVar(value="none")
        self.auth_type_dropdown = ctk.CTkOptionMenu(
            type_frame,
            variable=self.auth_type_var,
            values=["none", "basic", "bearer", "api_key"],
            command=self.on_auth_type_changed
        )
        self.auth_type_dropdown.pack(side="left", padx=10, pady=10)
        
        # Content frame for auth-specific fields
        self.content_frame = ctk.CTkFrame(self.parent)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create different auth panels
        self._create_no_auth_panel()
        self._create_basic_auth_panel()
        self._create_bearer_auth_panel()
        self._create_api_key_auth_panel()
        
        # Show initial panel
        self.show_no_auth_panel()
    
    def _create_no_auth_panel(self):
        """Create no authentication panel"""
        self.no_auth_frame = ctk.CTkFrame(self.content_frame)
        
        ctk.CTkLabel(
            self.no_auth_frame,
            text="No authentication required",
            text_color="gray"
        ).pack(expand=True, pady=50)
    
    def _create_basic_auth_panel(self):
        """Create basic authentication panel"""
        self.basic_auth_frame = ctk.CTkFrame(self.content_frame)
        
        # Username field
        username_frame = ctk.CTkFrame(self.basic_auth_frame)
        username_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(username_frame, text="Username:", width=100).pack(side="left", padx=10, pady=10)
        self.username_entry = ctk.CTkEntry(
            username_frame,
            placeholder_text="Enter username"
        )
        self.username_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        
        # Password field
        password_frame = ctk.CTkFrame(self.basic_auth_frame)
        password_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(password_frame, text="Password:", width=100).pack(side="left", padx=10, pady=10)
        self.password_entry = ctk.CTkEntry(
            password_frame,
            placeholder_text="Enter password",
            show="*"
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        
        # Show password checkbox
        self.show_password_var = tk.BooleanVar()
        show_password_check = ctk.CTkCheckBox(
            self.basic_auth_frame,
            text="Show password",
            variable=self.show_password_var,
            command=self.toggle_password_visibility
        )
        show_password_check.pack(padx=20, pady=10, anchor="w")
    
    def _create_bearer_auth_panel(self):
        """Create bearer token authentication panel"""
        self.bearer_auth_frame = ctk.CTkFrame(self.content_frame)
        
        # Token field
        token_frame = ctk.CTkFrame(self.bearer_auth_frame)
        token_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(token_frame, text="Token:", width=100).pack(side="left", padx=10, pady=10)
        self.token_entry = ctk.CTkEntry(
            token_frame,
            placeholder_text="Enter bearer token"
        )
        self.token_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        
        # Token prefix info
        info_label = ctk.CTkLabel(
            self.bearer_auth_frame,
            text="The token will be sent as: Authorization: Bearer <token>",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        info_label.pack(padx=20, pady=(0, 20))
    
    def _create_api_key_auth_panel(self):
        """Create API key authentication panel"""
        self.api_key_auth_frame = ctk.CTkFrame(self.content_frame)
        
        # Key field
        key_frame = ctk.CTkFrame(self.api_key_auth_frame)
        key_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(key_frame, text="Key:", width=100).pack(side="left", padx=10, pady=10)
        self.api_key_entry = ctk.CTkEntry(
            key_frame,
            placeholder_text="API key name (e.g., X-API-Key)"
        )
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        
        # Value field
        value_frame = ctk.CTkFrame(self.api_key_auth_frame)
        value_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(value_frame, text="Value:", width=100).pack(side="left", padx=10, pady=10)
        self.api_value_entry = ctk.CTkEntry(
            value_frame,
            placeholder_text="API key value"
        )
        self.api_value_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        
        # Location selection
        location_frame = ctk.CTkFrame(self.api_key_auth_frame)
        location_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(location_frame, text="Add to:", width=100).pack(side="left", padx=10, pady=10)
        
        self.api_location_var = tk.StringVar(value="header")
        location_dropdown = ctk.CTkOptionMenu(
            location_frame,
            variable=self.api_location_var,
            values=["header", "query"],
            command=self._notify_change
        )
        location_dropdown.pack(side="left", padx=10, pady=10)
    
    def _setup_layout(self):
        """Setup layout"""
        pass
    
    def _setup_bindings(self):
        """Setup event bindings"""
        # Basic auth bindings
        if hasattr(self, 'username_entry'):
            self.username_entry.bind('<KeyRelease>', lambda e: self._notify_change())
            self.password_entry.bind('<KeyRelease>', lambda e: self._notify_change())
        
        # Bearer auth bindings
        if hasattr(self, 'token_entry'):
            self.token_entry.bind('<KeyRelease>', lambda e: self._notify_change())
        
        # API key auth bindings
        if hasattr(self, 'api_key_entry'):
            self.api_key_entry.bind('<KeyRelease>', lambda e: self._notify_change())
            self.api_value_entry.bind('<KeyRelease>', lambda e: self._notify_change())
    
    def on_auth_type_changed(self, auth_type: str):
        """Handle authentication type change"""
        # Hide all panels
        self.no_auth_frame.pack_forget()
        self.basic_auth_frame.pack_forget()
        self.bearer_auth_frame.pack_forget()
        self.api_key_auth_frame.pack_forget()
        
        # Show appropriate panel
        if auth_type == "none":
            self.show_no_auth_panel()
        elif auth_type == "basic":
            self.show_basic_auth_panel()
        elif auth_type == "bearer":
            self.show_bearer_auth_panel()
        elif auth_type == "api_key":
            self.show_api_key_auth_panel()
        
        self._notify_change()
    
    def show_no_auth_panel(self):
        """Show no authentication panel"""
        self.no_auth_frame.pack(fill="both", expand=True)
    
    def show_basic_auth_panel(self):
        """Show basic authentication panel"""
        self.basic_auth_frame.pack(fill="both", expand=True)
    
    def show_bearer_auth_panel(self):
        """Show bearer token panel"""
        self.bearer_auth_frame.pack(fill="both", expand=True)
    
    def show_api_key_auth_panel(self):
        """Show API key panel"""
        self.api_key_auth_frame.pack(fill="both", expand=True)
    
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_password_var.get():
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="*")
    
    def _notify_change(self, *args):
        """Notify parent of changes"""
        auth_type = AuthType(self.auth_type_var.get())
        auth_data = self.get_auth_data()
        self.on_change_callback(auth_type, auth_data)
    
    def get_auth_data(self) -> Dict[str, str]:
        """Get current authentication data"""
        auth_type = self.auth_type_var.get()
        
        if auth_type == "basic":
            return {
                'username': self.username_entry.get(),
                'password': self.password_entry.get()
            }
        elif auth_type == "bearer":
            return {
                'token': self.token_entry.get()
            }
        elif auth_type == "api_key":
            return {
                'key': self.api_key_entry.get(),
                'value': self.api_value_entry.get(),
                'location': self.api_location_var.get()
            }
        
        return {}
    
    def set_auth_data(self, auth_type: AuthType, auth_data: Dict[str, str]):
        """Set authentication data"""
        self.auth_type_var.set(auth_type.value)
        self.on_auth_type_changed(auth_type.value)
        
        if auth_type == AuthType.BASIC:
            self.username_entry.delete(0, 'end')
            self.username_entry.insert(0, auth_data.get('username', ''))
            self.password_entry.delete(0, 'end')
            self.password_entry.insert(0, auth_data.get('password', ''))
        
        elif auth_type == AuthType.BEARER:
            self.token_entry.delete(0, 'end')
            self.token_entry.insert(0, auth_data.get('token', ''))
        
        elif auth_type == AuthType.API_KEY:
            self.api_key_entry.delete(0, 'end')
            self.api_key_entry.insert(0, auth_data.get('key', ''))
            self.api_value_entry.delete(0, 'end')
            self.api_value_entry.insert(0, auth_data.get('value', ''))
            self.api_location_var.set(auth_data.get('location', 'header'))
    
    def load_auth(self, auth_type: AuthType, auth_data: Dict[str, str]):
        """Load authentication data into panel"""
        self.set_auth_data(auth_type, auth_data)
    
    def clear(self):
        """Clear authentication data"""
        self.auth_type_var.set("none")
        self.on_auth_type_changed("none")
        
        # Clear all fields
        if hasattr(self, 'username_entry'):
            self.username_entry.delete(0, 'end')
            self.password_entry.delete(0, 'end')
        
        if hasattr(self, 'token_entry'):
            self.token_entry.delete(0, 'end')
        
        if hasattr(self, 'api_key_entry'):
            self.api_key_entry.delete(0, 'end')
            self.api_value_entry.delete(0, 'end')
            self.api_location_var.set('header')
