"""
Request history management panel
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Dict, Any
import time
from datetime import datetime

from services.data_manager import DataManager

class HistoryPanel:
    """Panel for displaying and managing request history"""
    
    def __init__(self, parent, data_manager: DataManager, load_callback: Callable[[Dict[str, Any]], None]):
        self.parent = parent
        self.data_manager = data_manager
        self.load_callback = load_callback
        self.history_data = []
        
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
        self.refresh_history()
    
    def _create_widgets(self):
        """Create panel widgets"""
        # Title frame
        title_frame = ctk.CTkFrame(self.parent)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            title_frame,
            text="Request History",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10, pady=10)
        
        # Control buttons
        controls_frame = ctk.CTkFrame(title_frame)
        controls_frame.pack(side="right", padx=10, pady=5)
        
        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="Refresh",
            width=80,
            command=self.refresh_history
        )
        refresh_btn.pack(side="left", padx=2)
        
        clear_btn = ctk.CTkButton(
            controls_frame,
            text="Clear All",
            width=80,
            fg_color="#FF4444",
            hover_color="#CC0000",
            command=self.clear_history
        )
        clear_btn.pack(side="left", padx=2)
        
        # Search frame
        search_frame = ctk.CTkFrame(self.parent)
        search_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(search_frame, text="Filter:").pack(side="left", padx=10, pady=10)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search by URL, method, or status..."
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        # Method filter
        self.method_filter_var = tk.StringVar(value="All")
        method_filter = ctk.CTkOptionMenu(
            search_frame,
            variable=self.method_filter_var,
            values=["All", "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
            width=100,
            command=self.on_filter_changed
        )
        method_filter.pack(side="right", padx=10, pady=10)
        
        ctk.CTkLabel(search_frame, text="Method:").pack(side="right", padx=(0, 5), pady=10)
        
        # History list frame
        list_frame = ctk.CTkFrame(self.parent)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create treeview for history
        self._create_history_tree(list_frame)
        
        # Context menu
        self._create_context_menu()
    
    def _create_history_tree(self, parent):
        """Create treeview for history display"""
        # Create frame for treeview
        tree_frame = ctk.CTkFrame(parent)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Define columns
        columns = ("method", "url", "status", "time", "size", "timestamp")
        
        self.history_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        # Configure column headings and widths
        self.history_tree.heading("method", text="Method", anchor="w")
        self.history_tree.heading("url", text="URL", anchor="w")
        self.history_tree.heading("status", text="Status", anchor="w")
        self.history_tree.heading("time", text="Time", anchor="w")
        self.history_tree.heading("size", text="Size", anchor="w")
        self.history_tree.heading("timestamp", text="Date", anchor="w")
        
        self.history_tree.column("method", width=80, minwidth=60)
        self.history_tree.column("url", width=300, minwidth=200)
        self.history_tree.column("status", width=80, minwidth=60)
        self.history_tree.column("time", width=80, minwidth=60)
        self.history_tree.column("size", width=80, minwidth=60)
        self.history_tree.column("timestamp", width=150, minwidth=120)
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.history_tree.xview)
        
        self.history_tree.configure(yscrollcommand=v_scrollbar.set)
        self.history_tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Pack widgets
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.history_tree.pack(side="left", fill="both", expand=True)
        
        # Configure tree styling
        self._configure_tree_styling()
    
    def _configure_tree_styling(self):
        """Configure treeview styling"""
        style = ttk.Style()
        
        # Configure treeview style for dark theme
        style.theme_use("clam")
        
        style.configure("Treeview",
                       background="#2b2b2b",
                       foreground="white",
                       rowheight=25,
                       fieldbackground="#2b2b2b",
                       borderwidth=0,
                       relief="flat")
        
        style.configure("Treeview.Heading",
                       background="#404040",
                       foreground="white",
                       borderwidth=1,
                       relief="solid")
        
        style.map("Treeview",
                 background=[('selected', '#2196F3')],
                 foreground=[('selected', 'white')])
        
        style.map("Treeview.Heading",
                 background=[('active', '#505050')])
    
    def _create_context_menu(self):
        """Create context menu for history items"""
        self.context_menu = tk.Menu(self.parent, tearoff=0, bg="#2b2b2b", fg="white")
        self.context_menu.add_command(label="Load Request", command=self.load_selected_request)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy URL", command=self.copy_selected_url)
        self.context_menu.add_command(label="Copy as cURL", command=self.copy_as_curl)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self.delete_selected_item)
        
        # Bind context menu
        self.history_tree.bind("<Button-3>", self.show_context_menu)
        self.history_tree.bind("<Control-Button-1>", self.show_context_menu)  # For Mac
    
    def _setup_layout(self):
        """Setup layout"""
        pass
    
    def _setup_bindings(self):
        """Setup event bindings"""
        # Double-click to load request
        self.history_tree.bind("<Double-1>", lambda e: self.load_selected_request())
        
        # Enter key to load request
        self.history_tree.bind("<Return>", lambda e: self.load_selected_request())
        
        # Delete key to delete item
        self.history_tree.bind("<Delete>", lambda e: self.delete_selected_item())
    
    def refresh_history(self):
        """Refresh history display"""
        try:
            self.history_data = self.data_manager.get_history(limit=500)
            self._populate_history_tree()
        except Exception as e:
            print(f"Error refreshing history: {e}")
            messagebox.showerror("Error", f"Failed to load history: {e}")
    
    def _populate_history_tree(self):
        """Populate treeview with history data"""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Apply filters
        filtered_data = self._apply_filters()
        
        # Add items to tree
        for i, entry in enumerate(filtered_data):
            try:
                request = entry.get('request', {})
                response = entry.get('response', {})
                timestamp = entry.get('timestamp', 0)
                
                # Extract display data
                method = request.get('method', 'Unknown')
                url = request.get('url', 'Unknown URL')
                status_code = response.get('status_code', 'Error')
                response_time = response.get('response_time', 0)
                size = response.get('size', 0)
                
                # Format values
                status_display = str(status_code) if status_code else "Error"
                time_display = f"{response_time:.0f}ms" if response_time else "N/A"
                size_display = self._format_size(size)
                date_display = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                
                # Truncate URL if too long
                if len(url) > 50:
                    display_url = url[:47] + "..."
                else:
                    display_url = url
                
                # Insert item
                item_id = self.history_tree.insert(
                    "",
                    "end",
                    values=(method, display_url, status_display, time_display, size_display, date_display),
                    tags=(str(i),)
                )
                
                # Color coding based on status
                self._apply_status_coloring(item_id, status_code)
                
            except Exception as e:
                print(f"Error processing history entry: {e}")
                continue
    
    def _apply_filters(self) -> List[Dict[str, Any]]:
        """Apply search and method filters to history data"""
        filtered_data = self.history_data.copy()
        
        # Apply search filter
        search_term = self.search_entry.get().lower().strip()
        if search_term:
            filtered_data = [
                entry for entry in filtered_data
                if self._matches_search(entry, search_term)
            ]
        
        # Apply method filter
        method_filter = self.method_filter_var.get()
        if method_filter != "All":
            filtered_data = [
                entry for entry in filtered_data
                if entry.get('request', {}).get('method', '').upper() == method_filter.upper()
            ]
        
        return filtered_data
    
    def _matches_search(self, entry: Dict[str, Any], search_term: str) -> bool:
        """Check if entry matches search term"""
        request = entry.get('request', {})
        response = entry.get('response', {})
        
        # Search in URL
        url = request.get('url', '').lower()
        if search_term in url:
            return True
        
        # Search in method
        method = request.get('method', '').lower()
        if search_term in method:
            return True
        
        # Search in status code
        status = str(response.get('status_code', '')).lower()
        if search_term in status:
            return True
        
        # Search in status text
        status_text = response.get('status_text', '').lower()
        if search_term in status_text:
            return True
        
        return False
    
    def _format_size(self, size: int) -> str:
        """Format response size for display"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f}KB"
        else:
            return f"{size / (1024 * 1024):.1f}MB"
    
    def _apply_status_coloring(self, item_id: str, status_code: int):
        """Apply color coding based on HTTP status code"""
        if isinstance(status_code, int):
            if 200 <= status_code < 300:
                # Success - green
                self.history_tree.set(item_id, "status", f"✓ {status_code}")
            elif 300 <= status_code < 400:
                # Redirect - blue
                self.history_tree.set(item_id, "status", f"→ {status_code}")
            elif 400 <= status_code < 500:
                # Client error - orange
                self.history_tree.set(item_id, "status", f"⚠ {status_code}")
            elif status_code >= 500:
                # Server error - red
                self.history_tree.set(item_id, "status", f"✗ {status_code}")
    
    def on_search_changed(self, event=None):
        """Handle search text change"""
        self._populate_history_tree()
    
    def on_filter_changed(self, method: str):
        """Handle method filter change"""
        self._populate_history_tree()
    
    def get_selected_entry(self) -> Dict[str, Any]:
        """Get currently selected history entry"""
        selection = self.history_tree.selection()
        if not selection:
            return None
        
        item = selection[0]
        tags = self.history_tree.item(item, "tags")
        if not tags:
            return None
        
        try:
            index = int(tags[0])
            filtered_data = self._apply_filters()
            if 0 <= index < len(filtered_data):
                return filtered_data[index]
        except (ValueError, IndexError):
            pass
        
        return None
    
    def load_selected_request(self):
        """Load selected request into the main interface"""
        entry = self.get_selected_entry()
        if not entry:
            messagebox.showwarning("Warning", "Please select a request to load")
            return
        
        request_data = entry.get('request', {})
        if self.load_callback:
            self.load_callback(request_data)
    
    def copy_selected_url(self):
        """Copy selected request URL to clipboard"""
        entry = self.get_selected_entry()
        if not entry:
            messagebox.showwarning("Warning", "Please select a request")
            return
        
        url = entry.get('request', {}).get('url', '')
        if url:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(url)
            messagebox.showinfo("Copied", "URL copied to clipboard")
    
    def copy_as_curl(self):
        """Copy selected request as cURL command"""
        entry = self.get_selected_entry()
        if not entry:
            messagebox.showwarning("Warning", "Please select a request")
            return
        
        try:
            request = entry.get('request', {})
            curl_command = self._generate_curl_command(request)
            
            self.parent.clipboard_clear()
            self.parent.clipboard_append(curl_command)
            messagebox.showinfo("Copied", "cURL command copied to clipboard")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate cURL command: {e}")
    
    def _generate_curl_command(self, request: Dict[str, Any]) -> str:
        """Generate cURL command from request data"""
        parts = ["curl"]
        
        # Method
        method = request.get('method', 'GET')
        if method != 'GET':
            parts.append(f"-X {method}")
        
        # URL
        url = request.get('url', '')
        parts.append(f"'{url}'")
        
        # Headers
        headers = request.get('headers', {})
        for key, value in headers.items():
            parts.append(f"-H '{key}: {value}'")
        
        # Body
        body = request.get('body', '')
        if body and method in ['POST', 'PUT', 'PATCH']:
            # Escape single quotes in body
            escaped_body = body.replace("'", "'\"'\"'")
            parts.append(f"-d '{escaped_body}'")
        
        return " \\\n  ".join(parts)
    
    def delete_selected_item(self):
        """Delete selected history item"""
        entry = self.get_selected_entry()
        if not entry:
            messagebox.showwarning("Warning", "Please select a request to delete")
            return
        
        timestamp = entry.get('timestamp')
        if timestamp and messagebox.askyesno("Confirm Delete", "Delete this history item?"):
            try:
                success = self.data_manager.delete_history_item(timestamp)
                if success:
                    self.refresh_history()
                else:
                    messagebox.showerror("Error", "Failed to delete history item")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete history item: {e}")
    
    def clear_history(self):
        """Clear all history"""
        if messagebox.askyesno("Confirm Clear", "Clear all request history?"):
            try:
                self.data_manager.clear_history()
                self.refresh_history()
                messagebox.showinfo("Success", "History cleared successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear history: {e}")
    
    def show_context_menu(self, event):
        """Show context menu"""
        # Select item under cursor
        item = self.history_tree.identify_row(event.y)
        if item:
            self.history_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def export_history(self, file_path: str):
        """Export history to file"""
        try:
            success = self.data_manager.export_data(file_path, "history")
            if success:
                messagebox.showinfo("Success", f"History exported to {file_path}")
            else:
                messagebox.showerror("Error", "Failed to export history")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")
