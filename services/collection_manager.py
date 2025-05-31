"""
Collection management service for organizing requests
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from models.collection_model import RequestCollection, CollectionFolder, CollectionRequest
from models.request_model import APIRequest
from config.settings import AppSettings

class CollectionManager:
    """Manages request collections and their persistence"""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.collections: List[RequestCollection] = []
        self._load_collections()
    
    @property
    def collections_file(self) -> Path:
        """Path to collections file"""
        return self.settings.data_dir / "request_collections.json"
    
    def _load_collections(self):
        """Load collections from file"""
        if not self.collections_file.exists():
            self._create_default_collection()
            return
        
        try:
            with open(self.collections_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.collections = []
            for collection_data in data.get('collections', []):
                collection = RequestCollection.from_dict(collection_data)
                self.collections.append(collection)
            
            # Ensure at least one collection exists
            if not self.collections:
                self._create_default_collection()
                
        except Exception as e:
            print(f"Error loading collections: {e}")
            self._create_default_collection()
    
    def _create_default_collection(self):
        """Create a default collection"""
        default_collection = RequestCollection(
            name="My Requests",
            description="Default collection for API requests"
        )
        self.collections = [default_collection]
        self.save_collections()
    
    def save_collections(self):
        """Save collections to file"""
        try:
            # Ensure directory exists
            self.collections_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'collections': [collection.to_dict() for collection in self.collections]
            }
            
            with open(self.collections_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving collections: {e}")
    
    def create_collection(self, name: str, description: str = "") -> RequestCollection:
        """Create a new collection"""
        collection = RequestCollection(name=name, description=description)
        self.collections.append(collection)
        self.save_collections()
        return collection
    
    def get_collection(self, collection_id: str) -> Optional[RequestCollection]:
        """Get collection by ID"""
        for collection in self.collections:
            if collection.id == collection_id:
                return collection
        return None
    
    def get_collection_by_name(self, name: str) -> Optional[RequestCollection]:
        """Get collection by name"""
        for collection in self.collections:
            if collection.name == name:
                return collection
        return None
    
    def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection"""
        for i, collection in enumerate(self.collections):
            if collection.id == collection_id:
                del self.collections[i]
                self.save_collections()
                return True
        return False
    
    def rename_collection(self, collection_id: str, new_name: str) -> bool:
        """Rename a collection"""
        collection = self.get_collection(collection_id)
        if collection:
            collection.name = new_name
            self.save_collections()
            return True
        return False
    
    def add_folder(self, collection_id: str, name: str, parent_id: Optional[str] = None, description: str = "") -> Optional[CollectionFolder]:
        """Add a folder to a collection"""
        collection = self.get_collection(collection_id)
        if collection:
            folder = collection.add_folder(name, parent_id, description)
            self.save_collections()
            return folder
        return None
    
    def add_request(self, collection_id: str, request: APIRequest, parent_id: Optional[str] = None, name: str = "") -> Optional[CollectionRequest]:
        """Add a request to a collection"""
        collection = self.get_collection(collection_id)
        if collection:
            collection_request = collection.add_request(request, parent_id, name)
            self.save_collections()
            return collection_request
        return None
    
    def remove_item(self, collection_id: str, item_id: str) -> bool:
        """Remove an item from a collection"""
        collection = self.get_collection(collection_id)
        if collection and collection.remove_item(item_id):
            self.save_collections()
            return True
        return False
    
    def move_item(self, collection_id: str, item_id: str, new_parent_id: Optional[str]) -> bool:
        """Move an item to a new parent in a collection"""
        collection = self.get_collection(collection_id)
        if collection and collection.move_item(item_id, new_parent_id):
            self.save_collections()
            return True
        return False
    
    def update_item(self, collection_id: str, item_id: str, name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """Update an item's properties"""
        collection = self.get_collection(collection_id)
        if collection:
            item = collection.get_item(item_id)
            if item:
                if name is not None:
                    item.name = name
                if description is not None:
                    item.description = description
                item.modified_at = time.time()
                collection.modified_at = time.time()
                self.save_collections()
                return True
        return False
    
    def duplicate_item(self, collection_id: str, item_id: str, new_name: str = "") -> Optional[str]:
        """Duplicate an item in a collection"""
        collection = self.get_collection(collection_id)
        if not collection:
            return None
        
        item = collection.get_item(item_id)
        if not item:
            return None
        
        if isinstance(item, CollectionFolder):
            # Duplicate folder
            new_name = new_name or f"{item.name} Copy"
            new_folder = collection.add_folder(new_name, item.parent_id, item.description)
            
            # Recursively duplicate children
            children = collection.get_children(item_id)
            for child in children:
                self._duplicate_item_recursive(collection, child, new_folder.id)
            
            self.save_collections()
            return new_folder.id
            
        else:
            # Duplicate request
            new_name = new_name or f"{item.name} Copy"
            new_request = collection.add_request(item.request, item.parent_id, new_name)
            self.save_collections()
            return new_request.id
    
    def _duplicate_item_recursive(self, collection: RequestCollection, item: Any, new_parent_id: str):
        """Recursively duplicate an item and its children"""
        if isinstance(item, CollectionFolder):
            new_folder = collection.add_folder(item.name, new_parent_id, item.description)
            children = collection.get_children(item.id)
            for child in children:
                self._duplicate_item_recursive(collection, child, new_folder.id)
        elif isinstance(item, CollectionRequest):
            collection.add_request(item.request, new_parent_id, item.name)
    
    def search_across_collections(self, query: str) -> List[Dict[str, Any]]:
        """Search for items across all collections"""
        results = []
        for collection in self.collections:
            items = collection.search_items(query)
            for item in items:
                result = {
                    'collection_id': collection.id,
                    'collection_name': collection.name,
                    'item_id': item.id,
                    'item_name': item.name,
                    'item_type': 'folder' if isinstance(item, CollectionFolder) else 'request',
                    'description': item.description
                }
                if isinstance(item, CollectionRequest):
                    result['method'] = item.request.method
                    result['url'] = item.request.url
                results.append(result)
        return results
    
    def get_all_requests(self) -> List[Dict[str, Any]]:
        """Get all requests from all collections"""
        all_requests = []
        for collection in self.collections:
            for item in collection.items:
                if isinstance(item, CollectionRequest):
                    all_requests.append({
                        'collection_id': collection.id,
                        'collection_name': collection.name,
                        'item_id': item.id,
                        'name': item.name,
                        'request': item.request,
                        'created_at': item.created_at,
                        'modified_at': item.modified_at
                    })
        return all_requests
    
    def export_collection(self, collection_id: str, file_path: str) -> bool:
        """Export a collection to a file"""
        collection = self.get_collection(collection_id)
        if not collection:
            return False
        
        try:
            export_data = {
                'version': '1.0',
                'export_type': 'collection',
                'exported_at': time.time(),
                'collection': collection.to_dict()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting collection: {e}")
            return False
    
    def import_collection(self, file_path: str) -> Optional[RequestCollection]:
        """Import a collection from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get('export_type') != 'collection':
                return None
            
            collection_data = data.get('collection', {})
            collection = RequestCollection.from_dict(collection_data)
            
            # Ensure unique name
            original_name = collection.name
            counter = 1
            while self.get_collection_by_name(collection.name):
                collection.name = f"{original_name} ({counter})"
                counter += 1
            
            self.collections.append(collection)
            self.save_collections()
            return collection
            
        except Exception as e:
            print(f"Error importing collection: {e}")
            return None
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about all collections"""
        total_collections = len(self.collections)
        total_folders = 0
        total_requests = 0
        method_counts = {}
        
        for collection in self.collections:
            stats = collection.get_stats()
            total_folders += stats['folders']
            total_requests += stats['requests']
            
            for method, count in stats['methods'].items():
                method_counts[method] = method_counts.get(method, 0) + count
        
        return {
            'total_collections': total_collections,
            'total_folders': total_folders,
            'total_requests': total_requests,
            'method_distribution': method_counts,
            'collections': [
                {
                    'id': collection.id,
                    'name': collection.name,
                    'stats': collection.get_stats()
                }
                for collection in self.collections
            ]
        }