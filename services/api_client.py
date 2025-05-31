"""
HTTP API Client for making requests
"""

import requests
import time
import threading
from typing import Callable, Optional, Dict, Any
from urllib3.exceptions import InsecureRequestWarning
import urllib3

from models.request_model import APIRequest, AuthType
from models.response_model import APIResponse

# Disable SSL warnings for testing purposes
urllib3.disable_warnings(InsecureRequestWarning)

class APIClient:
    """HTTP client for API requests"""
    
    def __init__(self, timeout: int = 30, verify_ssl: bool = True, max_redirects: int = 10):
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.max_redirects = max_redirects
        self.session = requests.Session()
        self.session.max_redirects = max_redirects
    
    def make_request(
        self, 
        request: APIRequest, 
        callback: Callable[[APIResponse], None],
        environment_vars: Optional[Dict[str, str]] = None
    ) -> None:
        """Make an async HTTP request"""
        def _request_thread():
            try:
                response = self._execute_request(request, environment_vars)
                callback(response)
            except Exception as e:
                error_response = APIResponse(error=str(e))
                callback(error_response)
        
        thread = threading.Thread(target=_request_thread, daemon=True)
        thread.start()
    
    def _execute_request(
        self, 
        request: APIRequest, 
        environment_vars: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """Execute the actual HTTP request"""
        start_time = time.time()
        
        try:
            # Substitute environment variables in URL
            url = request.url
            if environment_vars:
                for key, value in environment_vars.items():
                    url = url.replace(f"{{{{{key}}}}}", value)
            
            # Prepare headers
            headers = request.get_request_headers()
            if environment_vars:
                for key, value in headers.items():
                    for env_key, env_value in environment_vars.items():
                        headers[key] = value.replace(f"{{{{{env_key}}}}}", env_value)
            
            # Prepare authentication
            auth = None
            if request.auth_type == AuthType.BASIC:
                username = request.auth_data.get('username', '')
                password = request.auth_data.get('password', '')
                if username and password:
                    auth = (username, password)
            
            # Prepare request body
            body = request.get_request_body()
            if isinstance(body, str) and environment_vars:
                for key, value in environment_vars.items():
                    body = body.replace(f"{{{{{key}}}}}", value)
            
            # Prepare parameters
            params = request.params.copy()
            if environment_vars:
                for key, value in params.items():
                    for env_key, env_value in environment_vars.items():
                        params[key] = value.replace(f"{{{{{env_key}}}}}", env_value)
            
            # Add API key to params if needed
            if request.auth_type == AuthType.API_KEY:
                key = request.auth_data.get('key', '')
                value = request.auth_data.get('value', '')
                location = request.auth_data.get('location', 'header')
                
                if key and value and location == 'query':
                    params[key] = value
            
            # Make the request
            response = self.session.request(
                method=request.method,
                url=url,
                headers=headers,
                params=params,
                data=body if request.body_type != 'json' else None,
                json=body if request.body_type == 'json' and isinstance(body, (dict, list)) else None,
                auth=auth,
                timeout=self.timeout,
                verify=self.verify_ssl,
                allow_redirects=True
            )
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            
            # Parse response
            try:
                response_body = response.text
            except Exception:
                response_body = ""
            
            # Create response object
            api_response = APIResponse(
                status_code=response.status_code,
                status_text=response.reason or "",
                headers=dict(response.headers),
                body=response_body,
                response_time=response_time,
                size=len(response.content) if response.content else 0
            )
            
            return api_response
            
        except requests.exceptions.Timeout:
            return APIResponse(
                error="Request timed out",
                response_time=(time.time() - start_time) * 1000
            )
        except requests.exceptions.ConnectionError as e:
            return APIResponse(
                error=f"Connection error: {str(e)}",
                response_time=(time.time() - start_time) * 1000
            )
        except requests.exceptions.RequestException as e:
            return APIResponse(
                error=f"Request error: {str(e)}",
                response_time=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return APIResponse(
                error=f"Unexpected error: {str(e)}",
                response_time=(time.time() - start_time) * 1000
            )
    
    def update_settings(self, timeout: int, verify_ssl: bool, max_redirects: int):
        """Update client settings"""
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.max_redirects = max_redirects
        self.session.max_redirects = max_redirects
