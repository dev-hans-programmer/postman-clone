"""
Data persistence and management service
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

from models.request_model import APIRequest
from models.response_model import APIResponse
from models.environment_model import Environment
from config.settings import AppSettings

class DataManager:
    """Manages data persistence for requests, responses, and environments"""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.ensure_data_files()
    
    def ensure_data_files(self):
        """Ensure all required data files exist"""
        for file_path in [
            self.settings.history_file,
            self.settings.environments_file,
            self.settings.collections_file
        ]:
            if not file_path.exists():
                self._create_empty_file(file_path)
    
    def _create_empty_file(self, file_path: Path):
        """Create an empty JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump([], f)
        except Exception as e:
            print(f"Error creating file {file_path}: {e}")
    
    def _read_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read JSON file and return data"""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            return []
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []
    
    def _write_json_file(self, file_path: Path, data: List[Dict[str, Any]]):
        """Write data to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
    
    # Request History Management
    def save_to_history(self, request: APIRequest, response: APIResponse):
        """Save request-response pair to history"""
        history_entry = {
            'request': request.to_dict(),
            'response': response.to_dict(),
            'timestamp': time.time()
        }
        
        history = self._read_json_file(self.settings.history_file)
        history.insert(0, history_entry)  # Add to beginning
        
        # Keep only last 1000 entries
        if len(history) > 1000:
            history = history[:1000]
        
        self._write_json_file(self.settings.history_file, history)
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get request history"""
        history = self._read_json_file(self.settings.history_file)
        return history[:limit]
    
    def clear_history(self):
        """Clear all history"""
        self._write_json_file(self.settings.history_file, [])
    
    def delete_history_item(self, timestamp: float) -> bool:
        """Delete a specific history item"""
        history = self._read_json_file(self.settings.history_file)
        original_length = len(history)
        
        history = [item for item in history if item.get('timestamp') != timestamp]
        
        if len(history) < original_length:
            self._write_json_file(self.settings.history_file, history)
            return True
        return False
    
    # Environment Management
    def save_environment(self, environment: Environment):
        """Save an environment"""
        environments = self._read_json_file(self.settings.environments_file)
        
        # Update existing or add new
        found = False
        for i, env_data in enumerate(environments):
            if env_data.get('name') == environment.name:
                environments[i] = environment.to_dict()
                found = True
                break
        
        if not found:
            environments.append(environment.to_dict())
        
        self._write_json_file(self.settings.environments_file, environments)
    
    def get_environments(self) -> List[Environment]:
        """Get all environments"""
        environments_data = self._read_json_file(self.settings.environments_file)
        return [Environment.from_dict(data) for data in environments_data]
    
    def delete_environment(self, name: str) -> bool:
        """Delete an environment"""
        environments = self._read_json_file(self.settings.environments_file)
        original_length = len(environments)
        
        environments = [env for env in environments if env.get('name') != name]
        
        if len(environments) < original_length:
            self._write_json_file(self.settings.environments_file, environments)
            return True
        return False
    
    def get_active_environment(self) -> Optional[Environment]:
        """Get the currently active environment"""
        environments = self.get_environments()
        for env in environments:
            if env.is_active:
                return env
        return None
    
    def set_active_environment(self, name: str) -> bool:
        """Set an environment as active"""
        environments = self._read_json_file(self.settings.environments_file)
        
        # Deactivate all environments first
        for env in environments:
            env['is_active'] = False
        
        # Activate the specified environment
        for env in environments:
            if env.get('name') == name:
                env['is_active'] = True
                self._write_json_file(self.settings.environments_file, environments)
                return True
        
        return False
    
    # Request Collections Management
    def save_request_collection(self, name: str, requests: List[APIRequest]):
        """Save a collection of requests"""
        collections = self._read_json_file(self.settings.collections_file)
        
        collection_data = {
            'name': name,
            'requests': [req.to_dict() for req in requests],
            'created_at': time.time()
        }
        
        # Update existing or add new
        found = False
        for i, coll_data in enumerate(collections):
            if coll_data.get('name') == name:
                collections[i] = collection_data
                found = True
                break
        
        if not found:
            collections.append(collection_data)
        
        self._write_json_file(self.settings.collections_file, collections)
    
    def get_request_collections(self) -> List[Dict[str, Any]]:
        """Get all request collections"""
        return self._read_json_file(self.settings.collections_file)
    
    def delete_request_collection(self, name: str) -> bool:
        """Delete a request collection"""
        collections = self._read_json_file(self.settings.collections_file)
        original_length = len(collections)
        
        collections = [coll for coll in collections if coll.get('name') != name]
        
        if len(collections) < original_length:
            self._write_json_file(self.settings.collections_file, collections)
            return True
        return False
    
    # Export/Import functionality
    def export_data(self, file_path: str, data_type: str = "all") -> bool:
        """Export data to file"""
        try:
            export_data = {}
            
            if data_type in ["all", "history"]:
                export_data['history'] = self._read_json_file(self.settings.history_file)
            
            if data_type in ["all", "environments"]:
                export_data['environments'] = self._read_json_file(self.settings.environments_file)
            
            if data_type in ["all", "collections"]:
                export_data['collections'] = self._read_json_file(self.settings.collections_file)
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False
    
    def import_data(self, file_path: str, merge: bool = True) -> bool:
        """Import data from file"""
        try:
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            if 'history' in import_data:
                if merge:
                    existing_history = self._read_json_file(self.settings.history_file)
                    combined_history = import_data['history'] + existing_history
                    # Remove duplicates based on timestamp
                    seen_timestamps = set()
                    unique_history = []
                    for item in combined_history:
                        timestamp = item.get('timestamp')
                        if timestamp not in seen_timestamps:
                            seen_timestamps.add(timestamp)
                            unique_history.append(item)
                    self._write_json_file(self.settings.history_file, unique_history[:1000])
                else:
                    self._write_json_file(self.settings.history_file, import_data['history'])
            
            if 'environments' in import_data:
                if merge:
                    existing_envs = self._read_json_file(self.settings.environments_file)
                    # Merge by name, imported data takes precedence
                    env_dict = {env['name']: env for env in existing_envs}
                    for env in import_data['environments']:
                        env_dict[env['name']] = env
                    self._write_json_file(self.settings.environments_file, list(env_dict.values()))
                else:
                    self._write_json_file(self.settings.environments_file, import_data['environments'])
            
            if 'collections' in import_data:
                if merge:
                    existing_colls = self._read_json_file(self.settings.collections_file)
                    # Merge by name, imported data takes precedence
                    coll_dict = {coll['name']: coll for coll in existing_colls}
                    for coll in import_data['collections']:
                        coll_dict[coll['name']] = coll
                    self._write_json_file(self.settings.collections_file, list(coll_dict.values()))
                else:
                    self._write_json_file(self.settings.collections_file, import_data['collections'])
            
            return True
        except Exception as e:
            print(f"Error importing data: {e}")
            return False
