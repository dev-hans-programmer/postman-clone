"""
Environment and variable models for API testing
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
import time

@dataclass
class EnvironmentVariable:
    """Individual environment variable"""
    
    key: str = ""
    value: str = ""
    description: str = ""
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'enabled': self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentVariable':
        """Create from dictionary"""
        return cls(
            key=data.get('key', ''),
            value=data.get('value', ''),
            description=data.get('description', ''),
            enabled=data.get('enabled', True)
        )

@dataclass
class Environment:
    """Environment containing multiple variables"""
    
    name: str = ""
    variables: List[EnvironmentVariable] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    is_active: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'variables': [var.to_dict() for var in self.variables],
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Environment':
        """Create from dictionary"""
        env = cls()
        env.name = data.get('name', '')
        env.variables = [
            EnvironmentVariable.from_dict(var_data) 
            for var_data in data.get('variables', [])
        ]
        env.created_at = data.get('created_at', time.time())
        env.is_active = data.get('is_active', False)
        return env
    
    def get_variables_dict(self) -> Dict[str, str]:
        """Get enabled variables as a dictionary"""
        return {
            var.key: var.value 
            for var in self.variables 
            if var.enabled and var.key
        }
    
    def add_variable(self, key: str, value: str, description: str = "") -> None:
        """Add a new variable"""
        self.variables.append(EnvironmentVariable(
            key=key,
            value=value,
            description=description,
            enabled=True
        ))
    
    def remove_variable(self, key: str) -> bool:
        """Remove a variable by key"""
        for i, var in enumerate(self.variables):
            if var.key == key:
                del self.variables[i]
                return True
        return False
    
    def update_variable(self, key: str, value: str, description: str = None) -> bool:
        """Update an existing variable"""
        for var in self.variables:
            if var.key == key:
                var.value = value
                if description is not None:
                    var.description = description
                return True
        return False
    
    def substitute_variables(self, text: str) -> str:
        """Replace {{variable}} placeholders with actual values"""
        result = text
        variables = self.get_variables_dict()
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, value)
        
        return result
