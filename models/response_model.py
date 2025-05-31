"""
Response data model for API testing
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
import time
import json

@dataclass
class APIResponse:
    """Data model for API responses"""
    
    status_code: int = 0
    status_text: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    body: str = ""
    response_time: float = 0.0  # in milliseconds
    size: int = 0  # response size in bytes
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization"""
        return {
            'status_code': self.status_code,
            'status_text': self.status_text,
            'headers': self.headers,
            'body': self.body,
            'response_time': self.response_time,
            'size': self.size,
            'timestamp': self.timestamp,
            'error': self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIResponse':
        """Create response from dictionary"""
        response = cls()
        response.status_code = data.get('status_code', 0)
        response.status_text = data.get('status_text', '')
        response.headers = data.get('headers', {})
        response.body = data.get('body', '')
        response.response_time = data.get('response_time', 0.0)
        response.size = data.get('size', 0)
        response.timestamp = data.get('timestamp', time.time())
        response.error = data.get('error')
        return response
    
    @property
    def is_success(self) -> bool:
        """Check if response indicates success"""
        return 200 <= self.status_code < 300
    
    @property
    def is_json(self) -> bool:
        """Check if response content is JSON"""
        content_type = self.headers.get('content-type', '').lower()
        return 'application/json' in content_type
    
    def get_formatted_body(self) -> str:
        """Get formatted response body"""
        if not self.body:
            return ""
        
        if self.is_json:
            try:
                parsed = json.loads(self.body)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                pass
        
        return self.body
    
    @property
    def content_type(self) -> str:
        """Get response content type"""
        return self.headers.get('content-type', 'text/plain')
    
    @property
    def formatted_size(self) -> str:
        """Get human-readable size"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"
    
    @property
    def formatted_time(self) -> str:
        """Get human-readable response time"""
        if self.response_time < 1000:
            return f"{self.response_time:.0f} ms"
        else:
            return f"{self.response_time / 1000:.1f} s"
