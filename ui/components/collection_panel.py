"""
Collection management panel with tree view
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from typing import Dict, Any, Callable, Optional, List
import time

from models.collection_model import RequestCollection, CollectionFolder, CollectionRequest
from models.request_model import APIRequest
from services.collection_manager import CollectionManager

class CollectionPanel:
    """Panel for managing request collections with tree view"""
    
    def __init__(self, parent, collection_manager: CollectionManager, load_request_callback: Callable[[APIRequest], None]):
        self.parent = parent
        self.collection_manager = collection_manager
        self.load_request_callback = load_request_callback
        self.current_collection: Optional[RequestCollection] = None
        
        # Set default collection
        if self.collection_manager.collections:
            self.current_collection = self.collection_manager.collections[0]
        
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
        self._refresh_tree()
    
    def _create_widgets(self):
        """Create panel widgets"""
        # Header frame
        header_frame = ctk.CTkFrame(self.parent)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        # Collection selector
        collection_frame = ctk.CTkFrame(header_frame)
        collection_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(collection_frame, text="Collection:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        
        self.collection_var = tk.StringVar()
        self.collection_dropdown = ctk.CTkOptionMenu(
            collection_frame,
            variable=self.collection_var,
            values=self._get_collection_names(),
            command=self.on_collection_changed,
            width=150
        )
        self.collection_dropdown.pack(side="left", padx=5, fill="x", expand=True)
        
        # Collection management buttons
        btn_frame = ctk.CTkFrame(collection_frame)
        btn_frame.pack(side="right", padx=5)
        
        new_collection_btn = ctk.CTkButton(
            btn_frame,
            text="New",
            width=50,
            command=self.create_new_collection
        )
        new_collection_btn.pack(side="left", padx=2)
        
        manage_btn = ctk.CTkButton(
            btn_frame,
            text="Manage",
            width=60,
            command=self.show_collection_manager
        )
        manage_btn.pack(side="left", padx=2)
        
        # Search frame
        search_frame = ctk.CTkFrame(header_frame)
        search_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search requests..."
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        clear_search_btn = ctk.CTkButton(
            search_frame,
            text="×",
            width=30,
            command=self.clear_search
        )
        clear_search_btn.pack(side="right", padx=5, pady=5)
        
        # Tree frame
        tree_frame = ctk.CTkFrame(self.parent)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Create treeview
        self._create_tree_view(tree_frame)
        
        # Action buttons frame
        action_frame = ctk.CTkFrame(self.parent)
        action_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        # Add buttons
        add_folder_btn = ctk.CTkButton(
            action_frame,
            text="Add Folder",
            width=80,
            command=self.add_folder
        )
        add_folder_btn.pack(side="left", padx=2, pady=5)
        
        add_request_btn = ctk.CTkButton(
            action_frame,
            text="Save Current",
            width=80,
            command=self.save_current_request
        )
        add_request_btn.pack(side="left", padx=2, pady=5)
        
        # Context menu
        self._create_context_menu()
    
    def _create_tree_view(self, parent):
        """Create the tree view for collections"""
        # Create frame for tree
        tree_container = ctk.CTkFrame(parent)
        tree_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create treeview
        self.tree = ttk.Treeview(tree_container, show="tree")
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure tree styling
        self._configure_tree_styling()
    
    def _configure_tree_styling(self):
        """Configure tree view styling"""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure colors for dark theme
        style.configure("Treeview",
                       background="#2b2b2b",
                       foreground="white",
                       rowheight=25,
                       fieldbackground="#2b2b2b",
                       borderwidth=0,
                       relief="flat")
        
        style.map("Treeview",
                 background=[('selected', '#2196F3')],
                 foreground=[('selected', 'white')])
    
    def _create_context_menu(self):
        """Create context menu for tree items"""
        self.context_menu = tk.Menu(self.parent, tearoff=0, bg="#2b2b2b", fg="white")
        
        # Request-specific actions
        self.context_menu.add_command(label="Load Request", command=self.load_selected_request)
        self.context_menu.add_command(label="Duplicate", command=self.duplicate_selected_item)
        self.context_menu.add_separator()
        
        # Folder actions
        self.context_menu.add_command(label="Add Folder", command=self.add_folder_to_selected)
        self.context_menu.add_command(label="Add Request", command=self.add_request_to_selected)
        self.context_menu.add_separator()
        
        # Common actions
        self.context_menu.add_command(label="Rename", command=self.rename_selected_item)
        self.context_menu.add_command(label="Delete", command=self.delete_selected_item)
        
        # Bind context menu
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Control-Button-1>", self.show_context_menu)  # For Mac
    
    def _setup_layout(self):
        """Setup layout"""
        pass
    
    def _setup_bindings(self):
        """Setup event bindings"""
        # Double-click to load request
        self.tree.bind("<Double-1>", self.on_item_double_click)
        
        # Enter key to load request
        self.tree.bind("<Return>", lambda e: self.load_selected_request())
        
        # Delete key
        self.tree.bind("<Delete>", lambda e: self.delete_selected_item())
    
    def _get_collection_names(self) -> List[str]:
        """Get list of collection names"""
        return [collection.name for collection in self.collection_manager.collections]
    
    def on_collection_changed(self, collection_name: str):
        """Handle collection selection change"""
        collection = self.collection_manager.get_collection_by_name(collection_name)
        if collection:
            self.current_collection = collection
            self._refresh_tree()
    
    def _refresh_tree(self):
        """Refresh the tree view"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.current_collection:
            return
        
        # Update collection dropdown
        collection_names = self._get_collection_names()
        self.collection_dropdown.configure(values=collection_names)
        if self.current_collection.name in collection_names:
            self.collection_var.set(self.current_collection.name)
        
        # Build tree structure
        tree_data = self.current_collection.get_tree_structure()
        self._populate_tree(tree_data)
    
    def _populate_tree(self, tree_data: List[Dict[str, Any]], parent_id: str = ""):
        """Populate tree with data"""
        for item_data in tree_data:
            item_type = item_data['type']
            item_name = item_data['name']
            item_id = item_data['id']
            
            # Create display text
            if item_type == 'folder':
                display_text = f"📁 {item_name}"
            else:
                method = item_data.get('method', 'GET')
                url = item_data.get('url', '')
                # Truncate URL for display
                if len(url) > 30:
                    url = url[:27] + "..."
                display_text = f"{method} {item_name}"
                if url and item_name != url:
                    display_text += f" ({url})"
            
            # Insert item
            tree_item = self.tree.insert(
                parent_id,
                "end",
                text=display_text,
                tags=(item_type, item_id)
            )
            
            # Add children for folders
            if item_type == 'folder' and 'children' in item_data:
                self._populate_tree(item_data['children'], tree_item)
    
    def on_search_changed(self, event=None):
        """Handle search text change"""
        query = self.search_entry.get().strip()
        if not query:
            self._refresh_tree()
            return
        
        if not self.current_collection:
            return
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Search and display results
        results = self.current_collection.search_items(query)
        for item in results:
            item_type = 'folder' if isinstance(item, CollectionFolder) else 'request'
            
            if item_type == 'folder':
                display_text = f"📁 {item.name}"
            else:
                if isinstance(item, CollectionRequest):
                    method = item.request.method
                    display_text = f"{method} {item.name}"
                    if item.request.url:
                        url = item.request.url
                        if len(url) > 30:
                            url = url[:27] + "..."
                        display_text += f" ({url})"
                else:
                    display_text = item.name
            
            self.tree.insert(
                "",
                "end",
                text=display_text,
                tags=(item_type, item.id)
            )
    
    def clear_search(self):
        """Clear search and refresh tree"""
        self.search_entry.delete(0, 'end')
        self._refresh_tree()
    
    def get_selected_item_id(self) -> Optional[str]:
        """Get ID of currently selected item"""
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = selection[0]
        tags = self.tree.item(item, "tags")
        return tags[1] if len(tags) > 1 else None
    
    def get_selected_item_type(self) -> Optional[str]:
        """Get type of currently selected item"""
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = selection[0]
        tags = self.tree.item(item, "tags")
        return tags[0] if len(tags) > 0 else None
    
    def on_item_double_click(self, event):
        """Handle double-click on tree item"""
        item_type = self.get_selected_item_type()
        if item_type == 'request':
            self.load_selected_request()
    
    def load_selected_request(self):
        """Load selected request into main interface"""
        item_id = self.get_selected_item_id()
        item_type = self.get_selected_item_type()
        
        if not item_id or item_type != 'request' or not self.current_collection:
            return
        
        collection_item = self.current_collection.get_item(item_id)
        if collection_item and isinstance(collection_item, CollectionRequest):
            self.load_request_callback(collection_item.request)
    
    def show_context_menu(self, event):
        """Show context menu"""
        # Select item under cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            
            # Configure menu based on item type
            item_type = self.get_selected_item_type()
            
            # Enable/disable menu items based on context
            self.context_menu.entryconfig("Load Request", state="normal" if item_type == 'request' else "disabled")
            
            self.context_menu.post(event.x_root, event.y_root)
    
    def create_new_collection(self):
        """Create a new collection"""
        name = simpledialog.askstring("New Collection", "Enter collection name:")
        if name:
            collection = self.collection_manager.create_collection(name)
            self.current_collection = collection
            self._refresh_tree()
    
    def show_collection_manager(self):
        """Show collection management dialog"""
        CollectionManagerDialog(self.parent, self.collection_manager, self._refresh_tree)
    
    def add_folder(self):
        """Add a new folder"""
        if not self.current_collection:
            return
        
        name = simpledialog.askstring("New Folder", "Enter folder name:")
        if name:
            selected_id = self.get_selected_item_id()
            selected_type = self.get_selected_item_type()
            
            # If selected item is a request, use its parent
            parent_id = None
            if selected_type == 'folder':
                parent_id = selected_id
            elif selected_type == 'request':
                selected_item = self.current_collection.get_item(selected_id)
                if selected_item:
                    parent_id = selected_item.parent_id
            
            self.collection_manager.add_folder(self.current_collection.id, name, parent_id)
            self._refresh_tree()
    
    def add_folder_to_selected(self):
        """Add folder to selected folder"""
        selected_type = self.get_selected_item_type()
        if selected_type != 'folder':
            messagebox.showwarning("Warning", "Please select a folder first")
            return
        
        self.add_folder()
    
    def add_request_to_selected(self):
        """Add request to selected folder"""
        selected_type = self.get_selected_item_type()
        if selected_type != 'folder':
            messagebox.showwarning("Warning", "Please select a folder first")
            return
        
        # Create a simple request
        name = simpledialog.askstring("New Request", "Enter request name:")
        if name:
            selected_id = self.get_selected_item_id()
            request = APIRequest(name=name, url="https://api.example.com", method="GET")
            self.collection_manager.add_request(self.current_collection.id, request, selected_id, name)
            self._refresh_tree()
    
    def save_current_request(self):
        """Save current request to collection"""
        # This would be called from the main window with the current request
        messagebox.showinfo("Info", "This feature will be connected to the main request panel")
    
    def duplicate_selected_item(self):
        """Duplicate selected item"""
        item_id = self.get_selected_item_id()
        if not item_id or not self.current_collection:
            return
        
        item = self.current_collection.get_item(item_id)
        if item:
            new_name = f"{item.name} Copy"
            self.collection_manager.duplicate_item(self.current_collection.id, item_id, new_name)
            self._refresh_tree()
    
    def rename_selected_item(self):
        """Rename selected item"""
        item_id = self.get_selected_item_id()
        if not item_id or not self.current_collection:
            return
        
        item = self.current_collection.get_item(item_id)
        if item:
            new_name = simpledialog.askstring("Rename", "Enter new name:")
            if new_name and new_name != item.name:
                self.collection_manager.update_item(self.current_collection.id, item_id, name=new_name)
                self._refresh_tree()
    
    def delete_selected_item(self):
        """Delete selected item"""
        item_id = self.get_selected_item_id()
        if not item_id or not self.current_collection:
            return
        
        item = self.current_collection.get_item(item_id)
        if item:
            item_type = "folder" if isinstance(item, CollectionFolder) else "request"
            if messagebox.askyesno("Confirm Delete", f"Delete {item_type} '{item.name}'?"):
                self.collection_manager.remove_item(self.current_collection.id, item_id)
                self._refresh_tree()
    
    def add_request_to_collection(self, request: APIRequest, name: str = ""):
        """Add a request to the current collection (called from main window)"""
        if not self.current_collection:
            return
        
        selected_id = self.get_selected_item_id()
        selected_type = self.get_selected_item_type()
        
        # Determine parent folder
        parent_id = None
        if selected_type == 'folder':
            parent_id = selected_id
        elif selected_type == 'request':
            selected_item = self.current_collection.get_item(selected_id)
            if selected_item:
                parent_id = selected_item.parent_id
        
        self.collection_manager.add_request(self.current_collection.id, request, parent_id, name)
        self._refresh_tree()


class CollectionManagerDialog:
    """Dialog for managing collections"""
    
    def __init__(self, parent, collection_manager: CollectionManager, refresh_callback: Callable[[], None]):
        self.collection_manager = collection_manager
        self.refresh_callback = refresh_callback
        
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Collection Manager")
        self.window.geometry("600x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        self._create_widgets()
        self._refresh_list()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Manage Collections",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Collections list
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        self.collections_listbox = tk.Listbox(
            list_frame,
            bg="#212121",
            fg="#ffffff",
            selectbackground="#2196F3",
            relief="flat",
            borderwidth=0
        )
        self.collections_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        new_btn = ctk.CTkButton(button_frame, text="New", command=self.create_collection)
        new_btn.pack(side="left", padx=5)
        
        rename_btn = ctk.CTkButton(button_frame, text="Rename", command=self.rename_collection)
        rename_btn.pack(side="left", padx=5)
        
        delete_btn = ctk.CTkButton(
            button_frame, 
            text="Delete", 
            command=self.delete_collection,
            fg_color="#FF4444",
            hover_color="#CC0000"
        )
        delete_btn.pack(side="left", padx=5)
        
        export_btn = ctk.CTkButton(button_frame, text="Export", command=self.export_collection)
        export_btn.pack(side="left", padx=5)
        
        import_btn = ctk.CTkButton(button_frame, text="Import", command=self.import_collection)
        import_btn.pack(side="left", padx=5)
        
        close_btn = ctk.CTkButton(button_frame, text="Close", command=self.close_dialog)
        close_btn.pack(side="right", padx=5)
    
    def _refresh_list(self):
        """Refresh collections list"""
        self.collections_listbox.delete(0, tk.END)
        for collection in self.collection_manager.collections:
            stats = collection.get_stats()
            display_text = f"{collection.name} ({stats['requests']} requests, {stats['folders']} folders)"
            self.collections_listbox.insert(tk.END, display_text)
    
    def create_collection(self):
        """Create new collection"""
        name = simpledialog.askstring("New Collection", "Enter collection name:")
        if name:
            self.collection_manager.create_collection(name)
            self._refresh_list()
            self.refresh_callback()
    
    def rename_collection(self):
        """Rename selected collection"""
        selection = self.collections_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a collection")
            return
        
        index = selection[0]
        collection = self.collection_manager.collections[index]
        new_name = simpledialog.askstring("Rename Collection", "Enter new name:", initialvalue=collection.name)
        
        if new_name and new_name != collection.name:
            self.collection_manager.rename_collection(collection.id, new_name)
            self._refresh_list()
            self.refresh_callback()
    
    def delete_collection(self):
        """Delete selected collection"""
        selection = self.collections_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a collection")
            return
        
        if len(self.collection_manager.collections) <= 1:
            messagebox.showwarning("Warning", "Cannot delete the last collection")
            return
        
        index = selection[0]
        collection = self.collection_manager.collections[index]
        
        if messagebox.askyesno("Confirm Delete", f"Delete collection '{collection.name}'?"):
            self.collection_manager.delete_collection(collection.id)
            self._refresh_list()
            self.refresh_callback()
    
    def export_collection(self):
        """Export selected collection"""
        selection = self.collections_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a collection")
            return
        
        index = selection[0]
        collection = self.collection_manager.collections[index]
        
        file_path = filedialog.asksaveasfilename(
            title="Export Collection",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialvalue=f"{collection.name}.json"
        )
        
        if file_path:
            if self.collection_manager.export_collection(collection.id, file_path):
                messagebox.showinfo("Success", "Collection exported successfully")
            else:
                messagebox.showerror("Error", "Failed to export collection")
    
    def import_collection(self):
        """Import collection from file"""
        file_path = filedialog.askopenfilename(
            title="Import Collection",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            collection = self.collection_manager.import_collection(file_path)
            if collection:
                messagebox.showinfo("Success", f"Collection '{collection.name}' imported successfully")
                self._refresh_list()
                self.refresh_callback()
            else:
                messagebox.showerror("Error", "Failed to import collection")
    
    def close_dialog(self):
        """Close the dialog"""
        self.window.destroy()