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
        
        # Create main content area with resizable paned windows
        self.main_paned = tk.PanedWindow(
            self.main_frame, 
            orient=tk.HORIZONTAL, 
            sashrelief=tk.RAISED, 
            sashwidth=6,
            bg="#212121"
        )
        self.main_paned.pack(fill="both", expand=True, pady=(10, 0))
        
        # Sidebar for collections (left pane)
        self.sidebar_frame = ctk.CTkFrame(self.main_paned)
        self.sidebar_collapsed = False
        self.sidebar_width = self.settings.get_int('layout', 'sidebar_width', 300)
        self.main_paned.add(self.sidebar_frame, minsize=50, width=self.sidebar_width)
        
        # Content paned window for request/response (right pane)
        self.content_paned = tk.PanedWindow(
            self.main_paned, 
            orient=tk.HORIZONTAL, 
            sashrelief=tk.RAISED, 
            sashwidth=6,
            bg="#212121"
        )
        self.main_paned.add(self.content_paned, minsize=600)
        
        # Left panel for request configuration
        self.left_panel = ctk.CTkFrame(self.content_paned)
        self.request_panel_width = self.settings.get_int('layout', 'request_panel_width', 400)
        self.content_paned.add(self.left_panel, minsize=300, width=self.request_panel_width)
        
        # Right panel for response display
        self.right_panel = ctk.CTkFrame(self.content_paned)
        self.response_panel_width = self.settings.get_int('layout', 'response_panel_width', 400)
        self.content_paned.add(self.right_panel, minsize=300, width=self.response_panel_width)
        
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
        
        # Layout control buttons
        self.toggle_sidebar_btn = ctk.CTkButton(
            self.toolbar_frame,
            text="⋘",
            width=30,
            height=30,
            command=self.toggle_sidebar,
            fg_color="#9C27B0",
            hover_color="#7B1FA2"
        )
        self.toggle_sidebar_btn.pack(side="right", padx=(5, 0), pady=10)
        
        self.layout_btn = ctk.CTkButton(
            self.toolbar_frame,
            text="Layout",
            width=80,
            height=30,
            command=self.show_layout_options,
            fg_color="#607D8B",
            hover_color="#455A64"
        )
        self.layout_btn.pack(side="right", padx=5, pady=10)
        
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
            self.sidebar_frame,
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
    
    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        if self.sidebar_collapsed:
            # Expand sidebar
            self.main_paned.paneconfigure(self.sidebar_frame, width=self.sidebar_width, minsize=250)
            self.toggle_sidebar_btn.configure(text="⋘")
            self.sidebar_collapsed = False
        else:
            # Collapse sidebar
            self.sidebar_width = self.main_paned.paneconfig(self.sidebar_frame)['width'][4]
            self.main_paned.paneconfigure(self.sidebar_frame, width=0, minsize=0)
            self.toggle_sidebar_btn.configure(text="⋙")
            self.sidebar_collapsed = True
    
    def show_layout_options(self):
        """Show layout configuration dialog"""
        layout_window = LayoutOptionsDialog(self.root, self.settings, self._apply_layout_settings)
    
    def _apply_layout_settings(self):
        """Apply layout settings from preferences"""
        # Update panel sizes based on settings
        self.sidebar_width = self.settings.get_int('layout', 'sidebar_width', 300)
        self.request_panel_width = self.settings.get_int('layout', 'request_panel_width', 400)
        self.response_panel_width = self.settings.get_int('layout', 'response_panel_width', 400)
        
        if not self.sidebar_collapsed:
            self.main_paned.paneconfigure(self.sidebar_frame, width=self.sidebar_width)
        self.content_paned.paneconfigure(self.left_panel, width=self.request_panel_width)
        self.content_paned.paneconfigure(self.right_panel, width=self.response_panel_width)
    
    def _save_layout_settings(self):
        """Save current layout settings"""
        if not self.sidebar_collapsed:
            current_sidebar_width = self.main_paned.paneconfig(self.sidebar_frame)['width'][4]
            self.settings.set('layout', 'sidebar_width', str(current_sidebar_width))
        
        current_request_width = self.content_paned.paneconfig(self.left_panel)['width'][4]
        current_response_width = self.content_paned.paneconfig(self.right_panel)['width'][4]
        
        self.settings.set('layout', 'request_panel_width', str(current_request_width))
        self.settings.set('layout', 'response_panel_width', str(current_response_width))
        self.settings.save_settings()
    
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


class LayoutOptionsDialog:
    """Dialog for layout configuration options"""
    
    def __init__(self, parent, settings: AppSettings, apply_callback):
        self.settings = settings
        self.apply_callback = apply_callback
        
        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Layout Options")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.after(100, lambda: self.dialog.focus())
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="Layout Configuration", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Panel size controls
        self._create_size_controls(main_frame)
        
        # Layout presets
        self._create_presets(main_frame)
        
        # Buttons
        self._create_buttons(main_frame)
    
    def _create_size_controls(self, parent):
        """Create panel size control widgets"""
        sizes_frame = ctk.CTkFrame(parent)
        sizes_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(sizes_frame, text="Panel Sizes", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Sidebar width
        sidebar_frame = ctk.CTkFrame(sizes_frame)
        sidebar_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(sidebar_frame, text="Sidebar Width:").pack(side="left", padx=5)
        self.sidebar_var = tk.StringVar(value=str(self.settings.get_int('layout', 'sidebar_width', 300)))
        sidebar_entry = ctk.CTkEntry(sidebar_frame, textvariable=self.sidebar_var, width=80)
        sidebar_entry.pack(side="right", padx=5)
        
        # Request panel width
        request_frame = ctk.CTkFrame(sizes_frame)
        request_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(request_frame, text="Request Panel Width:").pack(side="left", padx=5)
        self.request_var = tk.StringVar(value=str(self.settings.get_int('layout', 'request_panel_width', 400)))
        request_entry = ctk.CTkEntry(request_frame, textvariable=self.request_var, width=80)
        request_entry.pack(side="right", padx=5)
        
        # Response panel width
        response_frame = ctk.CTkFrame(sizes_frame)
        response_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(response_frame, text="Response Panel Width:").pack(side="left", padx=5)
        self.response_var = tk.StringVar(value=str(self.settings.get_int('layout', 'response_panel_width', 400)))
        response_entry = ctk.CTkEntry(response_frame, textvariable=self.response_var, width=80)
        response_entry.pack(side="right", padx=5)
    
    def _create_presets(self, parent):
        """Create layout preset buttons"""
        presets_frame = ctk.CTkFrame(parent)
        presets_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(presets_frame, text="Layout Presets", font=("Arial", 14, "bold")).pack(pady=10)
        
        buttons_frame = ctk.CTkFrame(presets_frame)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        # Preset buttons
        ctk.CTkButton(buttons_frame, text="Default", command=self._apply_default, width=80).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Wide Request", command=self._apply_wide_request, width=100).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Wide Response", command=self._apply_wide_response, width=100).pack(side="left", padx=5)
    
    def _create_buttons(self, parent):
        """Create dialog buttons"""
        button_frame = ctk.CTkFrame(parent)
        button_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(button_frame, text="Apply", command=self._apply_settings, width=80).pack(side="right", padx=(5, 0))
        ctk.CTkButton(button_frame, text="Cancel", command=self._close_dialog, width=80).pack(side="right", padx=5)
    
    def _apply_default(self):
        """Apply default layout"""
        self.sidebar_var.set("300")
        self.request_var.set("400")
        self.response_var.set("400")
    
    def _apply_wide_request(self):
        """Apply wide request layout"""
        self.sidebar_var.set("250")
        self.request_var.set("500")
        self.response_var.set("350")
    
    def _apply_wide_response(self):
        """Apply wide response layout"""
        self.sidebar_var.set("250")
        self.request_var.set("350")
        self.response_var.set("500")
    
    def _apply_settings(self):
        """Apply and save settings"""
        try:
            # Validate and save settings
            sidebar_width = int(self.sidebar_var.get())
            request_width = int(self.request_var.get())
            response_width = int(self.response_var.get())
            
            # Basic validation
            if sidebar_width < 200 or sidebar_width > 600:
                messagebox.showerror("Invalid Input", "Sidebar width must be between 200 and 600 pixels")
                return
            
            if request_width < 250 or request_width > 800:
                messagebox.showerror("Invalid Input", "Request panel width must be between 250 and 800 pixels")
                return
                
            if response_width < 250 or response_width > 800:
                messagebox.showerror("Invalid Input", "Response panel width must be between 250 and 800 pixels")
                return
            
            # Save settings
            self.settings.set('layout', 'sidebar_width', str(sidebar_width))
            self.settings.set('layout', 'request_panel_width', str(request_width))
            self.settings.set('layout', 'response_panel_width', str(response_width))
            self.settings.save_settings()
            
            # Apply settings
            self.apply_callback()
            
            # Close dialog
            self._close_dialog()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values")
    
    def _close_dialog(self):
        """Close the dialog"""
        self.dialog.destroy()
