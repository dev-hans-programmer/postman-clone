"""
Request data model for API testing
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from enum import Enum
import json
import time

class AuthType(Enum):
    """Authentication types supported"""
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"

@dataclass
class APIRequest:
    """Data model for API requests"""
    
    url: str = ""
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, str] = field(default_factory=dict)
    body: str = ""
    body_type: str = "json"  # json, form-data, raw, x-www-form-urlencoded
    auth_type: AuthType = AuthType.NONE
    auth_data: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    name: str = ""
    description: str = ""
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary for serialization"""
        return {
            'url': self.url,
            'method': self.method,
            'headers': self.headers,
            'params': self.params,
            'body': self.body,
            'body_type': self.body_type,
            'auth_type': self.auth_type.value,
            'auth_data': self.auth_data,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIRequest':
        """Create request from dictionary"""
        request = cls()
        request.url = data.get('url', '')
        request.method = data.get('method', 'GET')
        request.headers = data.get('headers', {})
        request.params = data.get('params', {})
        request.body = data.get('body', '')
        request.body_type = data.get('body_type', 'json')
        request.auth_type = AuthType(data.get('auth_type', 'none'))
        request.auth_data = data.get('auth_data', {})
        request.name = data.get('name', '')
        request.description = data.get('description', '')
        request.created_at = data.get('created_at', time.time())
        return request
    
    def get_request_headers(self) -> Dict[str, str]:
        """Get headers including authentication"""
        headers = self.headers.copy()
        
        if self.auth_type == AuthType.BEARER:
            token = self.auth_data.get('token', '')
            if token:
                headers['Authorization'] = f'Bearer {token}'
        
        elif self.auth_type == AuthType.API_KEY:
            key = self.auth_data.get('key', '')
            value = self.auth_data.get('value', '')
            location = self.auth_data.get('location', 'header')
            
            if key and value and location == 'header':
                headers[key] = value
        
        # Set content-type based on body type
        if self.body and self.method in ['POST', 'PUT', 'PATCH']:
            if self.body_type == 'json':
                headers['Content-Type'] = 'application/json'
            elif self.body_type == 'x-www-form-urlencoded':
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        return headers
    
    def get_request_body(self) -> Optional[Any]:
        """Get formatted request body"""
        if not self.body:
            return None
        
        if self.body_type == 'json':
            try:
                return json.loads(self.body)
            except json.JSONDecodeError:
                return self.body
        
        return self.body
    
    def validate(self) -> tuple[bool, str]:
        """Validate the request"""
        if not self.url:
            return False, "URL is required"
        
        if not self.url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"
        
        if self.body_type == 'json' and self.body:
            try:
                json.loads(self.body)
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON in body: {e}"
        
        return True, ""
