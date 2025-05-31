"""
Collection and folder models for organizing requests
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
import time
import uuid

from .request_model import APIRequest

@dataclass
class CollectionItem:
    """Base class for collection items"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    parent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'parent_id': self.parent_id,
            'type': self.__class__.__name__
        }

@dataclass
class CollectionFolder(CollectionItem):
    """Folder for organizing requests and other folders"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data['type'] = 'folder'
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectionFolder':
        """Create from dictionary"""
        folder = cls()
        folder.id = data.get('id', str(uuid.uuid4()))
        folder.name = data.get('name', '')
        folder.description = data.get('description', '')
        folder.created_at = data.get('created_at', time.time())
        folder.modified_at = data.get('modified_at', time.time())
        folder.parent_id = data.get('parent_id')
        return folder

@dataclass
class CollectionRequest(CollectionItem):
    """Request item in a collection"""
    request: APIRequest = field(default_factory=APIRequest)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data['type'] = 'request'
        data['request'] = self.request.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectionRequest':
        """Create from dictionary"""
        item = cls()
        item.id = data.get('id', str(uuid.uuid4()))
        item.name = data.get('name', '')
        item.description = data.get('description', '')
        item.created_at = data.get('created_at', time.time())
        item.modified_at = data.get('modified_at', time.time())
        item.parent_id = data.get('parent_id')
        
        request_data = data.get('request', {})
        item.request = APIRequest.from_dict(request_data)
        # Sync name if not set
        if not item.name and item.request.name:
            item.name = item.request.name
        
        return item

@dataclass
class RequestCollection:
    """A collection containing folders and requests"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    items: List[Union[CollectionFolder, CollectionRequest]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'items': [item.to_dict() for item in self.items]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequestCollection':
        """Create from dictionary"""
        collection = cls()
        collection.id = data.get('id', str(uuid.uuid4()))
        collection.name = data.get('name', '')
        collection.description = data.get('description', '')
        collection.created_at = data.get('created_at', time.time())
        collection.modified_at = data.get('modified_at', time.time())
        
        # Load items
        items_data = data.get('items', [])
        for item_data in items_data:
            item_type = item_data.get('type', 'request')
            if item_type == 'folder':
                collection.items.append(CollectionFolder.from_dict(item_data))
            else:
                collection.items.append(CollectionRequest.from_dict(item_data))
        
        return collection
    
    def add_folder(self, name: str, parent_id: Optional[str] = None, description: str = "") -> CollectionFolder:
        """Add a new folder to the collection"""
        folder = CollectionFolder(
            name=name,
            description=description,
            parent_id=parent_id
        )
        self.items.append(folder)
        self.modified_at = time.time()
        return folder
    
    def add_request(self, request: APIRequest, parent_id: Optional[str] = None, name: str = "") -> CollectionRequest:
        """Add a request to the collection"""
        if not name:
            name = request.name or f"{request.method} {request.url}"
        
        collection_request = CollectionRequest(
            name=name,
            request=request,
            parent_id=parent_id
        )
        self.items.append(collection_request)
        self.modified_at = time.time()
        return collection_request
    
    def remove_item(self, item_id: str) -> bool:
        """Remove an item from the collection"""
        # First remove all children of this item
        self._remove_children(item_id)
        
        # Then remove the item itself
        for i, item in enumerate(self.items):
            if item.id == item_id:
                del self.items[i]
                self.modified_at = time.time()
                return True
        return False
    
    def _remove_children(self, parent_id: str):
        """Recursively remove all children of an item"""
        children = [item for item in self.items if item.parent_id == parent_id]
        for child in children:
            self._remove_children(child.id)
            self.items.remove(child)
    
    def get_item(self, item_id: str) -> Optional[Union[CollectionFolder, CollectionRequest]]:
        """Get an item by ID"""
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    def get_children(self, parent_id: Optional[str] = None) -> List[Union[CollectionFolder, CollectionRequest]]:
        """Get all children of a parent (or root items if parent_id is None)"""
        return [item for item in self.items if item.parent_id == parent_id]
    
    def move_item(self, item_id: str, new_parent_id: Optional[str]) -> bool:
        """Move an item to a new parent"""
        item = self.get_item(item_id)
        if item:
            item.parent_id = new_parent_id
            item.modified_at = time.time()
            self.modified_at = time.time()
            return True
        return False
    
    def get_tree_structure(self) -> List[Dict[str, Any]]:
        """Get the collection as a tree structure"""
        def build_tree(parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
            children = self.get_children(parent_id)
            tree = []
            
            for child in sorted(children, key=lambda x: (x.__class__.__name__, x.name)):
                node = {
                    'id': child.id,
                    'name': child.name,
                    'type': 'folder' if isinstance(child, CollectionFolder) else 'request',
                    'description': child.description,
                    'created_at': child.created_at,
                    'modified_at': child.modified_at
                }
                
                if isinstance(child, CollectionRequest):
                    node['method'] = child.request.method
                    node['url'] = child.request.url
                
                # Add children for folders
                if isinstance(child, CollectionFolder):
                    node['children'] = build_tree(child.id)
                
                tree.append(node)
            
            return tree
        
        return build_tree()
    
    def search_items(self, query: str) -> List[Union[CollectionFolder, CollectionRequest]]:
        """Search for items by name, description, or URL"""
        query = query.lower()
        results = []
        
        for item in self.items:
            if (query in item.name.lower() or 
                query in item.description.lower()):
                results.append(item)
            elif isinstance(item, CollectionRequest):
                if (query in item.request.url.lower() or 
                    query in item.request.method.lower()):
                    results.append(item)
        
        return results
    
    def get_stats(self) -> Dict[str, int]:
        """Get collection statistics"""
        stats = {
            'total_items': len(self.items),
            'folders': 0,
            'requests': 0,
            'methods': {}
        }
        
        for item in self.items:
            if isinstance(item, CollectionFolder):
                stats['folders'] += 1
            else:
                stats['requests'] += 1
                method = item.request.method
                stats['methods'][method] = stats['methods'].get(method, 0) + 1
        
        return stats