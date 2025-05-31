"""
Main application window and controller
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import simpledialog
import sys
from typing import Optional

from config.settings import AppSettings
from services.api_client import APIClient
from services.data_manager import DataManager
from services.collection_manager import CollectionManager
from models.request_model import APIRequest, AuthType
from models.response_model import APIResponse
from models.environment_model import Environment

from ui.components.request_panel import RequestPanel
from ui.components.response_panel import ResponsePanel
from ui.components.headers_panel import HeadersPanel
from ui.components.auth_panel import AuthPanel
from ui.components.environment_panel import EnvironmentPanel
from ui.components.history_panel import HistoryPanel
from ui.components.collection_panel import CollectionPanel

class MainWindow:
    """Main application window"""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.api_client = APIClient(
            timeout=self.settings.get_int('network', 'timeout', 30),
            verify_ssl=self.settings.get_bool('network', 'verify_ssl', True),
            max_redirects=self.settings.get_int('network', 'max_redirects', 10)
        )
        self.data_manager = DataManager(settings)
        self.collection_manager = CollectionManager(settings)
        
        self.current_request = APIRequest()
        self.current_response: Optional[APIResponse] = None
        self.active_environment: Optional[Environment] = None
        
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
        self._load_initial_data()
    
    def _setup_window(self):
        """Initialize the main window"""
        self.root = ctk.CTk()
        self.root.title("API Tester - Professional REST Client")
        
        # Window configuration
        width = self.settings.get_int('appearance', 'window_width', 1200)
        height = self.settings.get_int('appearance', 'window_height', 800)
        
        # Center window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(800, 600)
        
        # Set window icon and properties
        try:
            self.root.iconname("API Tester")
        except:
            pass
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Create main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create toolbar
        self._create_toolbar()
        
        # Create main content area with three panels
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Sidebar for collections
        self.sidebar = ctk.CTkFrame(self.content_frame, width=300)
        self.sidebar.pack(side="left", fill="y", padx=(0, 5))
        self.sidebar.pack_propagate(False)
        
        # Main content paned window
        self.paned_window = ctk.CTkFrame(self.content_frame)
        self.paned_window.pack(side="right", fill="both", expand=True)
        
        # Left panel for request configuration
        self.left_panel = ctk.CTkFrame(self.paned_window)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Right panel for response display
        self.right_panel = ctk.CTkFrame(self.paned_window)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Create component panels
        self._create_collection_panel()
        self._create_request_components()
        self._create_response_components()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_menu_bar(self):
        """Create application menu bar"""
        # Since CustomTkinter doesn't have native menu support, we'll create a custom toolbar
        self.menu_frame = ctk.CTkFrame(self.main_frame, height=40)
        self.menu_frame.pack(fill="x", pady=(0, 10))
        self.menu_frame.pack_propagate(False)
        
        # File menu buttons
        file_frame = ctk.CTkFrame(self.menu_frame)
        file_frame.pack(side="left", padx=10, pady=5)
        
        self.new_btn = ctk.CTkButton(
            file_frame, text="New", width=80, height=30,
            command=self.new_request
        )
        self.new_btn.pack(side="left", padx=2)
        
        self.save_btn = ctk.CTkButton(
            file_frame, text="Save", width=80, height=30,
            command=self.save_request
        )
        self.save_btn.pack(side="left", padx=2)
        
        self.import_btn = ctk.CTkButton(
            file_frame, text="Import", width=80, height=30,
            command=self.import_data
        )
        self.import_btn.pack(side="left", padx=2)
        
        self.export_btn = ctk.CTkButton(
            file_frame, text="Export", width=80, height=30,
            command=self.export_data
        )
        self.export_btn.pack(side="left", padx=2)
        
        # Environment selector
        env_frame = ctk.CTkFrame(self.menu_frame)
        env_frame.pack(side="right", padx=10, pady=5)
        
        ctk.CTkLabel(env_frame, text="Environment:").pack(side="left", padx=(0, 5))
        
        self.env_var = tk.StringVar(value="No Environment")
        self.env_dropdown = ctk.CTkOptionMenu(
            env_frame, variable=self.env_var, width=150,
            command=self.on_environment_changed
        )
        self.env_dropdown.pack(side="left", padx=2)
        
        self.manage_env_btn = ctk.CTkButton(
            env_frame, text="Manage", width=80, height=30,
            command=self.show_environment_manager
        )
        self.manage_env_btn.pack(side="left", padx=2)
    
    def _create_toolbar(self):
        """Create main toolbar with request controls"""
        self.toolbar_frame = ctk.CTkFrame(self.main_frame, height=50)
        self.toolbar_frame.pack(fill="x", pady=(0, 10))
        self.toolbar_frame.pack_propagate(False)
        
        # HTTP method dropdown
        self.method_var = tk.StringVar(value="GET")
        self.method_dropdown = ctk.CTkOptionMenu(
            self.toolbar_frame,
            variable=self.method_var,
            values=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
            width=100,
            command=self.on_method_changed
        )
        self.method_dropdown.pack(side="left", padx=10, pady=10)
        
        # URL entry
        self.url_entry = ctk.CTkEntry(
            self.toolbar_frame,
            placeholder_text="Enter request URL...",
            height=30
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.url_entry.bind('<Return>', lambda e: self.send_request())
        
        # Send button
        self.send_btn = ctk.CTkButton(
            self.toolbar_frame,
            text="Send",
            width=100,
            height=30,
            command=self.send_request,
            fg_color="#00C851",
            hover_color="#007E33"
        )
        self.send_btn.pack(side="right", padx=10, pady=10)
    
    def _create_collection_panel(self):
        """Create collection management panel"""
        self.collection_panel = CollectionPanel(
            self.sidebar,
            self.collection_manager,
            self.load_request_from_collection
        )
    
    def _create_request_components(self):
        """Create request configuration components"""
        # Create notebook for request tabs
        self.request_notebook = ctk.CTkTabview(self.left_panel)
        self.request_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self.request_notebook.add("Body")
        self.request_notebook.add("Headers")
        self.request_notebook.add("Auth")
        self.request_notebook.add("History")
        
        # Create component panels
        self.request_panel = RequestPanel(
            self.request_notebook.tab("Body"),
            self.on_request_changed
        )
        
        self.headers_panel = HeadersPanel(
            self.request_notebook.tab("Headers"),
            self.on_headers_changed
        )
        
        self.auth_panel = AuthPanel(
            self.request_notebook.tab("Auth"),
            self.on_auth_changed
        )
        
        self.history_panel = HistoryPanel(
            self.request_notebook.tab("History"),
            self.data_manager,
            self.load_request_from_history
        )
    
    def _create_response_components(self):
        """Create response display components"""
        self.response_panel = ResponsePanel(self.right_panel)
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_frame = ctk.CTkFrame(self.main_frame, height=30)
        self.status_frame.pack(fill="x", pady=(10, 0))
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Response info labels
        self.response_info_frame = ctk.CTkFrame(self.status_frame)
        self.response_info_frame.pack(side="right", padx=10, pady=2)
        
        self.status_code_label = ctk.CTkLabel(
            self.response_info_frame,
            text="",
            width=100
        )
        self.status_code_label.pack(side="right", padx=5)
        
        self.time_label = ctk.CTkLabel(
            self.response_info_frame,
            text="",
            width=100
        )
        self.time_label.pack(side="right", padx=5)
        
        self.size_label = ctk.CTkLabel(
            self.response_info_frame,
            text="",
            width=100
        )
        self.size_label.pack(side="right", padx=5)
    
    def _setup_layout(self):
        """Setup window layout and weights"""
        # Configure grid weights for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
    
    def _setup_bindings(self):
        """Setup event bindings"""
        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_request())
        self.root.bind('<Control-s>', lambda e: self.save_request())
        self.root.bind('<Control-o>', lambda e: self.import_data())
        self.root.bind('<Control-e>', lambda e: self.export_data())
        self.root.bind('<F5>', lambda e: self.send_request())
        
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _load_initial_data(self):
        """Load initial data and setup"""
        # Load environments
        self.refresh_environments()
        
        # Load active environment
        active_env = self.data_manager.get_active_environment()
        if active_env:
            self.active_environment = active_env
            self.env_var.set(active_env.name)
        
        # Load history
        self.history_panel.refresh_history()
    
    def refresh_environments(self):
        """Refresh environment dropdown"""
        environments = self.data_manager.get_environments()
        env_names = [env.name for env in environments]
        env_names.insert(0, "No Environment")
        
        self.env_dropdown.configure(values=env_names)
    
    def on_method_changed(self, method: str):
        """Handle HTTP method change"""
        self.current_request.method = method
        # Show/hide body panel based on method
        if method in ['GET', 'HEAD', 'DELETE']:
            self.request_panel.set_body_visible(False)
        else:
            self.request_panel.set_body_visible(True)
    
    def on_request_changed(self, body: str, body_type: str):
        """Handle request body changes"""
        self.current_request.body = body
        self.current_request.body_type = body_type
    
    def on_headers_changed(self, headers: dict):
        """Handle headers changes"""
        self.current_request.headers = headers
    
    def on_auth_changed(self, auth_type: AuthType, auth_data: dict):
        """Handle authentication changes"""
        self.current_request.auth_type = auth_type
        self.current_request.auth_data = auth_data
    
    def on_environment_changed(self, env_name: str):
        """Handle environment selection change"""
        if env_name == "No Environment":
            self.active_environment = None
            self.data_manager.set_active_environment("")
        else:
            environments = self.data_manager.get_environments()
            for env in environments:
                if env.name == env_name:
                    self.active_environment = env
                    self.data_manager.set_active_environment(env_name)
                    break
    
    def send_request(self):
        """Send the API request"""
        # Update request from UI
        self.current_request.url = self.url_entry.get().strip()
        self.current_request.method = self.method_var.get()
        
        # Validate request
        is_valid, error_msg = self.current_request.validate()
        if not is_valid:
            messagebox.showerror("Invalid Request", error_msg)
            return
        
        # Update UI state
        self.send_btn.configure(text="Sending...", state="disabled")
        self.status_label.configure(text="Sending request...")
        self.response_panel.clear_response()
        
        # Get environment variables
        env_vars = {}
        if self.active_environment:
            env_vars = self.active_environment.get_variables_dict()
        
        # Send request
        self.api_client.make_request(
            self.current_request,
            self.on_response_received,
            env_vars
        )
    
    def on_response_received(self, response: APIResponse):
        """Handle received API response"""
        self.current_response = response
        
        # Update UI in main thread
        self.root.after(0, self._update_response_ui)
    
    def _update_response_ui(self):
        """Update UI with response data"""
        if not self.current_response:
            return
        
        # Update response panel
        self.response_panel.display_response(self.current_response)
        
        # Update status bar
        if self.current_response.error:
            self.status_label.configure(text=f"Error: {self.current_response.error}")
            self.status_code_label.configure(text="Error")
        else:
            self.status_label.configure(text="Request completed")
            self.status_code_label.configure(
                text=f"{self.current_response.status_code} {self.current_response.status_text}"
            )
        
        self.time_label.configure(text=self.current_response.formatted_time)
        self.size_label.configure(text=self.current_response.formatted_size)
        
        # Reset send button
        self.send_btn.configure(text="Send", state="normal")
        
        # Save to history
        if self.current_response and not self.current_response.error:
            self.data_manager.save_to_history(self.current_request, self.current_response)
            self.history_panel.refresh_history()
    
    def new_request(self):
        """Create a new request"""
        self.current_request = APIRequest()
        self.current_response = None
        
        # Clear UI
        self.url_entry.delete(0, 'end')
        self.method_var.set("GET")
        self.request_panel.clear()
        self.headers_panel.clear()
        self.auth_panel.clear()
        self.response_panel.clear_response()
        
        # Update status
        self.status_label.configure(text="New request created")
        self.status_code_label.configure(text="")
        self.time_label.configure(text="")
        self.size_label.configure(text="")
    
    def save_request(self):
        """Save current request to collection"""
        if not self.current_request.url:
            messagebox.showwarning("Save Request", "No request to save")
            return
        
        # Update current request with UI values
        self.current_request.url = self.url_entry.get().strip()
        self.current_request.method = self.method_var.get()
        
        # Simple dialog for request name
        name = simpledialog.askstring("Save Request", "Enter request name:")
        if name:
            self.current_request.name = name
            self.collection_panel.add_request_to_collection(self.current_request, name)
            messagebox.showinfo("Saved", f"Request '{name}' saved to collection")
    
    def import_data(self):
        """Import data from file"""
        file_path = filedialog.askopenfilename(
            title="Import Data",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            success = self.data_manager.import_data(file_path, merge=True)
            if success:
                messagebox.showinfo("Import", "Data imported successfully")
                self.refresh_environments()
                self.history_panel.refresh_history()
            else:
                messagebox.showerror("Import", "Failed to import data")
    
    def export_data(self):
        """Export data to file"""
        file_path = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            success = self.data_manager.export_data(file_path, "all")
            if success:
                messagebox.showinfo("Export", "Data exported successfully")
            else:
                messagebox.showerror("Export", "Failed to export data")
    
    def show_environment_manager(self):
        """Show environment management dialog"""
        env_window = EnvironmentPanel(self.root, self.data_manager, self.refresh_environments)
    
    def load_request_from_history(self, request_data: dict):
        """Load a request from history"""
        self.current_request = APIRequest.from_dict(request_data)
        
        # Update UI
        self.url_entry.delete(0, 'end')
        self.url_entry.insert(0, self.current_request.url)
        self.method_var.set(self.current_request.method)
        
        # Update panels
        self.request_panel.load_request(self.current_request)
        self.headers_panel.load_headers(self.current_request.headers)
        self.auth_panel.load_auth(self.current_request.auth_type, self.current_request.auth_data)
        
        # Clear previous response
        self.response_panel.clear_response()
        self.status_label.configure(text="Request loaded from history")
    
    def load_request_from_collection(self, request: APIRequest):
        """Load a request from collection"""
        # Update UI
        self.current_request = request
        self.url_entry.delete(0, 'end')
        self.url_entry.insert(0, request.url)
        self.method_var.set(request.method)
        
        # Load into panels
        self.request_panel.load_request(request)
        self.headers_panel.load_headers(request.headers)
        self.auth_panel.load_auth(request.auth_type, request.auth_data)
        
        # Clear response
        self.response_panel.clear_response()
        self.status_label.configure(text="Request loaded from collection")
    
    def on_closing(self):
        """Handle application closing"""
        # Save window position and size
        geometry = self.root.geometry()
        width, height = geometry.split('+')[0].split('x')
        self.settings.set('appearance', 'window_width', width)
        self.settings.set('appearance', 'window_height', height)
        self.settings.save_settings()
        
        # Close application
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
