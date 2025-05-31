"""
JSON formatting and validation utilities
"""

import json
import re
from typing import Any, Dict, Union, Optional

class JSONFormatter:
    """Utility class for JSON formatting and validation"""
    
    def __init__(self, indent: int = 2, sort_keys: bool = False):
        """
        Initialize JSON formatter
        
        Args:
            indent: Number of spaces for indentation
            sort_keys: Whether to sort object keys
        """
        self.indent = indent
        self.sort_keys = sort_keys
    
    def format(self, json_string: str, compact: bool = False) -> str:
        """
        Format JSON string with proper indentation
        
        Args:
            json_string: JSON string to format
            compact: If True, format in compact style
            
        Returns:
            Formatted JSON string
            
        Raises:
            json.JSONDecodeError: If the input is not valid JSON
        """
        if not json_string or not json_string.strip():
            return ""
        
        try:
            # Parse JSON
            parsed = json.loads(json_string)
            
            # Format based on compact flag
            if compact:
                return json.dumps(
                    parsed,
                    separators=(',', ':'),
                    ensure_ascii=False,
                    sort_keys=self.sort_keys
                )
            else:
                return json.dumps(
                    parsed,
                    indent=self.indent,
                    ensure_ascii=False,
                    sort_keys=self.sort_keys
                )
                
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON: {e}", e.doc, e.pos)
    
    def minify(self, json_string: str) -> str:
        """
        Minify JSON string (remove whitespace)
        
        Args:
            json_string: JSON string to minify
            
        Returns:
            Minified JSON string
        """
        return self.format(json_string, compact=True)
    
    def prettify(self, json_string: str) -> str:
        """
        Prettify JSON string with proper formatting
        
        Args:
            json_string: JSON string to prettify
            
        Returns:
            Prettified JSON string
        """
        return self.format(json_string, compact=False)
    
    def validate(self, json_string: str) -> tuple[bool, Optional[str]]:
        """
        Validate JSON string
        
        Args:
            json_string: JSON string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not json_string or not json_string.strip():
            return False, "Empty JSON string"
        
        try:
            json.loads(json_string)
            return True, None
        except json.JSONDecodeError as e:
            return False, str(e)
    
    def extract_json_from_text(self, text: str) -> Optional[str]:
        """
        Extract JSON from text that may contain other content
        
        Args:
            text: Text that may contain JSON
            
        Returns:
            Extracted JSON string or None if not found
        """
        # Try to find JSON objects or arrays
        patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Objects
            r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]',  # Arrays
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                if self.validate(match)[0]:
                    return match
        
        return None
    
    def safe_format(self, json_string: str, fallback: str = None) -> str:
        """
        Safely format JSON string, return original or fallback on error
        
        Args:
            json_string: JSON string to format
            fallback: Fallback string if formatting fails
            
        Returns:
            Formatted JSON string or original/fallback on error
        """
        try:
            return self.format(json_string)
        except Exception:
            return fallback if fallback is not None else json_string
    
    def get_json_size(self, json_string: str) -> int:
        """
        Get size of JSON string in bytes
        
        Args:
            json_string: JSON string
            
        Returns:
            Size in bytes
        """
        return len(json_string.encode('utf-8'))
    
    def get_json_depth(self, json_data: Union[str, Dict, Any]) -> int:
        """
        Calculate the maximum depth of nested JSON structure
        
        Args:
            json_data: JSON string or parsed JSON data
            
        Returns:
            Maximum nesting depth
        """
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError:
                return 0
        
        def _calculate_depth(obj, current_depth=0):
            if isinstance(obj, dict):
                if not obj:
                    return current_depth
                return max(_calculate_depth(value, current_depth + 1) for value in obj.values())
            elif isinstance(obj, list):
                if not obj:
                    return current_depth
                return max(_calculate_depth(item, current_depth + 1) for item in obj)
            else:
                return current_depth
        
        return _calculate_depth(json_data)
    
    def get_json_stats(self, json_string: str) -> Dict[str, Any]:
        """
        Get statistics about JSON structure
        
        Args:
            json_string: JSON string to analyze
            
        Returns:
            Dictionary with JSON statistics
        """
        try:
            parsed = json.loads(json_string)
            
            def count_elements(obj):
                """Count different types of elements in JSON"""
                counts = {
                    'objects': 0,
                    'arrays': 0,
                    'strings': 0,
                    'numbers': 0,
                    'booleans': 0,
                    'nulls': 0,
                    'total_keys': 0
                }
                
                if isinstance(obj, dict):
                    counts['objects'] += 1
                    counts['total_keys'] += len(obj)
                    for value in obj.values():
                        sub_counts = count_elements(value)
                        for key in counts:
                            counts[key] += sub_counts[key]
                
                elif isinstance(obj, list):
                    counts['arrays'] += 1
                    for item in obj:
                        sub_counts = count_elements(item)
                        for key in counts:
                            counts[key] += sub_counts[key]
                
                elif isinstance(obj, str):
                    counts['strings'] += 1
                elif isinstance(obj, (int, float)):
                    counts['numbers'] += 1
                elif isinstance(obj, bool):
                    counts['booleans'] += 1
                elif obj is None:
                    counts['nulls'] += 1
                
                return counts
            
            element_counts = count_elements(parsed)
            
            return {
                'size_bytes': self.get_json_size(json_string),
                'size_formatted': len(self.format(json_string)),
                'size_minified': len(self.minify(json_string)),
                'max_depth': self.get_json_depth(parsed),
                'is_valid': True,
                **element_counts
            }
            
        except json.JSONDecodeError as e:
            return {
                'size_bytes': len(json_string.encode('utf-8')),
                'size_formatted': 0,
                'size_minified': 0,
                'max_depth': 0,
                'is_valid': False,
                'error': str(e),
                'objects': 0,
                'arrays': 0,
                'strings': 0,
                'numbers': 0,
                'booleans': 0,
                'nulls': 0,
                'total_keys': 0
            }
    
    def compare_json(self, json1: str, json2: str) -> Dict[str, Any]:
        """
        Compare two JSON strings for structural equality
        
        Args:
            json1: First JSON string
            json2: Second JSON string
            
        Returns:
            Dictionary with comparison results
        """
        try:
            parsed1 = json.loads(json1)
            parsed2 = json.loads(json2)
            
            # Deep comparison
            are_equal = parsed1 == parsed2
            
            # Get stats for both
            stats1 = self.get_json_stats(json1)
            stats2 = self.get_json_stats(json2)
            
            return {
                'are_equal': are_equal,
                'both_valid': stats1['is_valid'] and stats2['is_valid'],
                'json1_stats': stats1,
                'json2_stats': stats2,
                'size_difference': stats2['size_bytes'] - stats1['size_bytes'],
                'depth_difference': stats2['max_depth'] - stats1['max_depth']
            }
            
        except json.JSONDecodeError as e:
            return {
                'are_equal': False,
                'both_valid': False,
                'error': str(e),
                'json1_stats': self.get_json_stats(json1),
                'json2_stats': self.get_json_stats(json2)
            }
    
    def escape_json_string(self, text: str) -> str:
        """
        Properly escape a string for use in JSON
        
        Args:
            text: String to escape
            
        Returns:
            Escaped string suitable for JSON
        """
        return json.dumps(text)[1:-1]  # Remove surrounding quotes
    
    def unescape_json_string(self, escaped_text: str) -> str:
        """
        Unescape a JSON string
        
        Args:
            escaped_text: Escaped JSON string
            
        Returns:
            Unescaped string
        """
        try:
            return json.loads(f'"{escaped_text}"')
        except json.JSONDecodeError:
            return escaped_text
    
    def flatten_json(self, json_data: Union[str, Dict, Any], separator: str = '.') -> Dict[str, Any]:
        """
        Flatten nested JSON structure into dot-notation keys
        
        Args:
            json_data: JSON string or parsed JSON data
            separator: Separator to use between nested keys
            
        Returns:
            Flattened dictionary
        """
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError:
                return {}
        
        def _flatten(obj, parent_key=''):
            """Recursively flatten the object"""
            items = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{parent_key}{separator}{key}" if parent_key else key
                    items.extend(_flatten(value, new_key).items())
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    new_key = f"{parent_key}{separator}{i}" if parent_key else str(i)
                    items.extend(_flatten(value, new_key).items())
            else:
                return {parent_key: obj}
            
            return dict(items)
        
        return _flatten(json_data)
