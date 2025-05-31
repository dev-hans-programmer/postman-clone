"""
Environment management panel
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, List, Optional

from models.environment_model import Environment, EnvironmentVariable
from services.data_manager import DataManager

class EnvironmentPanel:
    """Panel for managing environments and variables"""
    
    def __init__(self, parent, data_manager: DataManager, refresh_callback: Callable[[], None]):
        self.parent = parent
        self.data_manager = data_manager
        self.refresh_callback = refresh_callback
        
        self.environments: List[Environment] = []
        self.current_environment: Optional[Environment] = None
        
        self._create_window()
        self._create_widgets()
        self._setup_layout()
        self._load_environments()
    
    def _create_window(self):
        """Create environment management window"""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Environment Manager")
        self.window.geometry("800x600")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 800) // 2
        y = (self.window.winfo_screenheight() - 600) // 2
        self.window.geometry(f"800x600+{x}+{y}")
    
    def _create_widgets(self):
        """Create panel widgets"""
        # Main container
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Environment Manager",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Content frame with two panels
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Left panel - Environment list
        left_panel = ctk.CTkFrame(content_frame)
        left_panel.pack(side="left", fill="y", padx=(10, 5), pady=10)
        
        # Right panel - Environment variables
        right_panel = ctk.CTkFrame(content_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
        
        self._create_environment_list(left_panel)
        self._create_variable_editor(right_panel)
        
        # Button frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.close_window
        )
        close_btn.pack(side="right", padx=10, pady=10)
        
        # Save button
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save All",
            command=self.save_all_environments,
            fg_color="#00C851",
            hover_color="#007E33"
        )
        save_btn.pack(side="right", padx=10, pady=10)
    
    def _create_environment_list(self, parent):
        """Create environment list panel"""
        # Title
        list_title = ctk.CTkLabel(
            parent,
            text="Environments",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        list_title.pack(pady=10)
        
        # New environment button
        new_btn = ctk.CTkButton(
            parent,
            text="New Environment",
            width=200,
            command=self.create_new_environment
        )
        new_btn.pack(pady=5)
        
        # Environment listbox
        listbox_frame = ctk.CTkFrame(parent)
        listbox_frame.pack(fill="both", expand=True, pady=10)
        
        self.env_listbox = tk.Listbox(
            listbox_frame,
            bg="#212121",
            fg="#ffffff",
            selectbackground="#2196F3",
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10)
        )
        self.env_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.env_listbox.bind('<<ListboxSelect>>', self.on_environment_selected)
        
        # Environment buttons
        btn_frame = ctk.CTkFrame(parent)
        btn_frame.pack(fill="x", pady=5)
        
        duplicate_btn = ctk.CTkButton(
            btn_frame,
            text="Duplicate",
            width=95,
            command=self.duplicate_environment
        )
        duplicate_btn.pack(side="left", padx=2)
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Delete",
            width=95,
            fg_color="#FF4444",
            hover_color="#CC0000",
            command=self.delete_environment
        )
        delete_btn.pack(side="right", padx=2)
    
    def _create_variable_editor(self, parent):
        """Create variable editor panel"""
        # Title with environment name
        self.var_title = ctk.CTkLabel(
            parent,
            text="Select an environment",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.var_title.pack(pady=10)
        
        # Environment name editor
        name_frame = ctk.CTkFrame(parent)
        name_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(name_frame, text="Name:", width=80).pack(side="left", padx=10, pady=10)
        self.env_name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="Environment name"
        )
        self.env_name_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.env_name_entry.bind('<KeyRelease>', self.on_environment_name_changed)
        
        # Set active button
        self.set_active_btn = ctk.CTkButton(
            name_frame,
            text="Set Active",
            width=100,
            command=self.set_environment_active
        )
        self.set_active_btn.pack(side="right", padx=10, pady=10)
        
        # Variables section
        variables_frame = ctk.CTkFrame(parent)
        variables_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Variables header
        var_header_frame = ctk.CTkFrame(variables_frame)
        var_header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            var_header_frame,
            text="Variables",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        add_var_btn = ctk.CTkButton(
            var_header_frame,
            text="Add Variable",
            width=100,
            command=self.add_variable
        )
        add_var_btn.pack(side="right")
        
        # Variables table header
        table_header = ctk.CTkFrame(variables_frame)
        table_header.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(table_header, text="Enabled", width=80).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(table_header, text="Key", width=150).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(table_header, text="Value", width=200).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(table_header, text="Description").pack(side="left", padx=(0, 10))
        
        # Scrollable frame for variables
        self.variables_scroll_frame = ctk.CTkScrollableFrame(variables_frame)
        self.variables_scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Variable entries list
        self.variable_entries = []
        
        # Initially disabled
        self._set_editor_enabled(False)
    
    def _setup_layout(self):
        """Setup layout"""
        pass
    
    def _load_environments(self):
        """Load environments from data manager"""
        self.environments = self.data_manager.get_environments()
        self._refresh_environment_list()
    
    def _refresh_environment_list(self):
        """Refresh the environment listbox"""
        self.env_listbox.delete(0, tk.END)
        
        for env in self.environments:
            display_name = env.name
            if env.is_active:
                display_name += " (Active)"
            self.env_listbox.insert(tk.END, display_name)
    
    def _set_editor_enabled(self, enabled: bool):
        """Enable or disable the variable editor"""
        state = "normal" if enabled else "disabled"
        self.env_name_entry.configure(state=state)
        self.set_active_btn.configure(state=state)
        
        for _, key_entry, value_entry, desc_entry, enabled_check, _ in self.variable_entries:
            key_entry.configure(state=state)
            value_entry.configure(state=state)
            desc_entry.configure(state=state)
            enabled_check.configure(state=state)
    
    def create_new_environment(self):
        """Create a new environment"""
        name = simpledialog.askstring("New Environment", "Enter environment name:")
        if name:
            # Check if name already exists
            for env in self.environments:
                if env.name == name:
                    messagebox.showerror("Error", f"Environment '{name}' already exists")
                    return
            
            # Create new environment
            new_env = Environment(name=name)
            self.environments.append(new_env)
            self._refresh_environment_list()
            
            # Select the new environment
            self.env_listbox.selection_set(len(self.environments) - 1)
            self.on_environment_selected()
    
    def duplicate_environment(self):
        """Duplicate selected environment"""
        selection = self.env_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an environment to duplicate")
            return
        
        env_index = selection[0]
        original_env = self.environments[env_index]
        
        # Get new name
        new_name = simpledialog.askstring(
            "Duplicate Environment", 
            f"Enter name for duplicated environment:",
            initialvalue=f"{original_env.name} Copy"
        )
        
        if new_name:
            # Check if name already exists
            for env in self.environments:
                if env.name == new_name:
                    messagebox.showerror("Error", f"Environment '{new_name}' already exists")
                    return
            
            # Create duplicate
            duplicate_env = Environment(
                name=new_name,
                variables=[
                    EnvironmentVariable(
                        key=var.key,
                        value=var.value,
                        description=var.description,
                        enabled=var.enabled
                    ) for var in original_env.variables
                ]
            )
            
            self.environments.append(duplicate_env)
            self._refresh_environment_list()
    
    def delete_environment(self):
        """Delete selected environment"""
        selection = self.env_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an environment to delete")
            return
        
        env_index = selection[0]
        env = self.environments[env_index]
        
        if messagebox.askyesno("Confirm Delete", f"Delete environment '{env.name}'?"):
            self.environments.pop(env_index)
            self._refresh_environment_list()
            
            # Clear editor
            self.current_environment = None
            self._set_editor_enabled(False)
            self.var_title.configure(text="Select an environment")
            self._clear_variables()
    
    def on_environment_selected(self, event=None):
        """Handle environment selection"""
        selection = self.env_listbox.curselection()
        if not selection:
            return
        
        env_index = selection[0]
        self.current_environment = self.environments[env_index]
        
        # Update editor
        self._set_editor_enabled(True)
        self.var_title.configure(text=f"Environment: {self.current_environment.name}")
        self.env_name_entry.delete(0, tk.END)
        self.env_name_entry.insert(0, self.current_environment.name)
        
        # Load variables
        self._load_variables()
    
    def on_environment_name_changed(self, event=None):
        """Handle environment name change"""
        if self.current_environment:
            new_name = self.env_name_entry.get()
            self.current_environment.name = new_name
            self.var_title.configure(text=f"Environment: {new_name}")
            self._refresh_environment_list()
    
    def set_environment_active(self):
        """Set current environment as active"""
        if not self.current_environment:
            return
        
        # Deactivate all environments
        for env in self.environments:
            env.is_active = False
        
        # Activate current environment
        self.current_environment.is_active = True
        self._refresh_environment_list()
        
        messagebox.showinfo("Success", f"Environment '{self.current_environment.name}' is now active")
    
    def _load_variables(self):
        """Load variables for current environment"""
        self._clear_variables()
        
        if not self.current_environment:
            return
        
        for var in self.current_environment.variables:
            self._add_variable_row(var.key, var.value, var.description, var.enabled)
        
        # Add empty row for new variables
        self._add_variable_row()
    
    def _clear_variables(self):
        """Clear all variable entries"""
        for var_frame, _, _, _, _, _ in self.variable_entries:
            var_frame.destroy()
        self.variable_entries.clear()
    
    def add_variable(self):
        """Add a new variable row"""
        self._add_variable_row()
    
    def _add_variable_row(self, key="", value="", description="", enabled=True):
        """Add a variable entry row"""
        var_frame = ctk.CTkFrame(self.variables_scroll_frame)
        var_frame.pack(fill="x", pady=2)
        
        # Enabled checkbox
        enabled_var = tk.BooleanVar(value=enabled)
        enabled_check = ctk.CTkCheckBox(
            var_frame,
            text="",
            variable=enabled_var,
            width=80
        )
        enabled_check.pack(side="left", padx=(0, 10))
        
        # Key entry
        key_entry = ctk.CTkEntry(var_frame, width=150, placeholder_text="Variable name")
        key_entry.pack(side="left", padx=(0, 10))
        key_entry.insert(0, key)
        
        # Value entry
        value_entry = ctk.CTkEntry(var_frame, width=200, placeholder_text="Variable value")
        value_entry.pack(side="left", padx=(0, 10))
        value_entry.insert(0, value)
        
        # Description entry
        desc_entry = ctk.CTkEntry(var_frame, placeholder_text="Description (optional)")
        desc_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        desc_entry.insert(0, description)
        
        # Remove button
        remove_btn = ctk.CTkButton(
            var_frame,
            text="×",
            width=30,
            command=lambda: self._remove_variable_row(var_frame, entry_tuple)
        )
        remove_btn.pack(side="right")
        
        entry_tuple = (var_frame, key_entry, value_entry, desc_entry, enabled_check, enabled_var)
        self.variable_entries.append(entry_tuple)
        
        return entry_tuple
    
    def _remove_variable_row(self, var_frame, entry_tuple):
        """Remove a variable row"""
        var_frame.destroy()
        if entry_tuple in self.variable_entries:
            self.variable_entries.remove(entry_tuple)
    
    def _get_current_variables(self) -> List[EnvironmentVariable]:
        """Get current variables from the editor"""
        variables = []
        
        for _, key_entry, value_entry, desc_entry, _, enabled_var in self.variable_entries:
            key = key_entry.get().strip()
            value = value_entry.get().strip()
            description = desc_entry.get().strip()
            enabled = enabled_var.get()
            
            if key:  # Only add variables with non-empty keys
                variables.append(EnvironmentVariable(
                    key=key,
                    value=value,
                    description=description,
                    enabled=enabled
                ))
        
        return variables
    
    def save_all_environments(self):
        """Save all environments"""
        try:
            # Update current environment variables
            if self.current_environment:
                self.current_environment.variables = self._get_current_variables()
            
            # Save all environments
            for env in self.environments:
                self.data_manager.save_environment(env)
            
            messagebox.showinfo("Success", "All environments saved successfully")
            
            # Refresh parent callback
            if self.refresh_callback:
                self.refresh_callback()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save environments: {e}")
    
    def close_window(self):
        """Close the environment manager window"""
        # Ask to save if there are changes
        if messagebox.askyesnocancel("Save Changes", "Save changes before closing?"):
            self.save_all_environments()
        
        self.window.destroy()
