"""
File operation utilities for the API testing application
"""

import os
import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import zipfile
import tempfile
import shutil
from datetime import datetime

class FileOperations:
    """Utility class for file operations"""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """
        Ensure directory exists, create if it doesn't
        
        Args:
            path: Directory path
            
        Returns:
            Path object of the directory
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def safe_write_json(file_path: Union[str, Path], data: Any, backup: bool = True) -> bool:
        """
        Safely write JSON data to file with optional backup
        
        Args:
            file_path: Path to write the file
            data: Data to write
            backup: Whether to create backup of existing file
            
        Returns:
            True if successful, False otherwise
        """
        file_path = Path(file_path)
        
        try:
            # Create backup if file exists and backup is requested
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
                shutil.copy2(file_path, backup_path)
            
            # Write to temporary file first
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Move temporary file to final location
            temp_path.replace(file_path)
            return True
            
        except Exception as e:
            print(f"Error writing JSON file {file_path}: {e}")
            # Clean up temporary file if it exists
            temp_path = file_path.with_suffix('.tmp')
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    @staticmethod
    def safe_read_json(file_path: Union[str, Path], default: Any = None) -> Any:
        """
        Safely read JSON data from file
        
        Args:
            file_path: Path to read the file
            default: Default value if file doesn't exist or can't be read
            
        Returns:
            Parsed JSON data or default value
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading JSON file {file_path}: {e}")
            return default
    
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], file_path: Union[str, Path], 
                     fieldnames: Optional[List[str]] = None) -> bool:
        """
        Export data to CSV file
        
        Args:
            data: List of dictionaries to export
            file_path: Path to write CSV file
            fieldnames: List of field names (keys) to include
            
        Returns:
            True if successful, False otherwise
        """
        if not data:
            return False
        
        file_path = Path(file_path)
        
        try:
            # Determine fieldnames if not provided
            if fieldnames is None:
                fieldnames = list(data[0].keys()) if data else []
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in data:
                    # Filter row to only include specified fieldnames
                    filtered_row = {k: v for k, v in row.items() if k in fieldnames}
                    writer.writerow(filtered_row)
            
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV {file_path}: {e}")
            return False
    
    @staticmethod
    def import_from_csv(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Import data from CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of dictionaries representing CSV rows
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return []
        
        try:
            data = []
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(dict(row))
            return data
            
        except Exception as e:
            print(f"Error importing from CSV {file_path}: {e}")
            return []
    
    @staticmethod
    def export_to_xml(data: Dict[str, Any], file_path: Union[str, Path], 
                     root_name: str = "root") -> bool:
        """
        Export data to XML file
        
        Args:
            data: Dictionary to export
            file_path: Path to write XML file
            root_name: Name of the root XML element
            
        Returns:
            True if successful, False otherwise
        """
        file_path = Path(file_path)
        
        try:
            def dict_to_xml(parent, data_dict):
                """Convert dictionary to XML elements"""
                for key, value in data_dict.items():
                    # Clean key name for XML
                    clean_key = str(key).replace(' ', '_').replace('-', '_')
                    
                    if isinstance(value, dict):
                        child = ET.SubElement(parent, clean_key)
                        dict_to_xml(child, value)
                    elif isinstance(value, list):
                        for item in value:
                            child = ET.SubElement(parent, clean_key)
                            if isinstance(item, dict):
                                dict_to_xml(child, item)
                            else:
                                child.text = str(item)
                    else:
                        child = ET.SubElement(parent, clean_key)
                        child.text = str(value)
            
            root = ET.Element(root_name)
            dict_to_xml(root, data)
            
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)  # Pretty print
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            
            return True
            
        except Exception as e:
            print(f"Error exporting to XML {file_path}: {e}")
            return False
    
    @staticmethod
    def create_archive(source_paths: List[Union[str, Path]], 
                      archive_path: Union[str, Path],
                      compression: str = 'zip') -> bool:
        """
        Create archive from multiple files/directories
        
        Args:
            source_paths: List of paths to include in archive
            archive_path: Path for the created archive
            compression: Type of compression ('zip' or 'tar')
            
        Returns:
            True if successful, False otherwise
        """
        archive_path = Path(archive_path)
        
        try:
            if compression.lower() == 'zip':
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for source_path in source_paths:
                        source_path = Path(source_path)
                        if source_path.is_file():
                            zipf.write(source_path, source_path.name)
                        elif source_path.is_dir():
                            for file_path in source_path.rglob('*'):
                                if file_path.is_file():
                                    arcname = file_path.relative_to(source_path.parent)
                                    zipf.write(file_path, arcname)
            else:
                import tarfile
                mode = 'w:gz' if compression.lower() == 'tar' else 'w'
                with tarfile.open(archive_path, mode) as tarf:
                    for source_path in source_paths:
                        source_path = Path(source_path)
                        if source_path.exists():
                            tarf.add(source_path, source_path.name)
            
            return True
            
        except Exception as e:
            print(f"Error creating archive {archive_path}: {e}")
            return False
    
    @staticmethod
    def extract_archive(archive_path: Union[str, Path], 
                       extract_to: Union[str, Path]) -> bool:
        """
        Extract archive to specified directory
        
        Args:
            archive_path: Path to archive file
            extract_to: Directory to extract to
            
        Returns:
            True if successful, False otherwise
        """
        archive_path = Path(archive_path)
        extract_to = Path(extract_to)
        
        if not archive_path.exists():
            return False
        
        try:
            FileOperations.ensure_directory(extract_to)
            
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(extract_to)
            else:
                import tarfile
                with tarfile.open(archive_path, 'r') as tarf:
                    tarf.extractall(extract_to)
            
            return True
            
        except Exception as e:
            print(f"Error extracting archive {archive_path}: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get detailed information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {'exists': False}
        
        try:
            stat = file_path.stat()
            return {
                'exists': True,
                'name': file_path.name,
                'size': stat.st_size,
                'size_human': FileOperations.format_file_size(stat.st_size),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'is_file': file_path.is_file(),
                'is_dir': file_path.is_dir(),
                'extension': file_path.suffix,
                'parent': str(file_path.parent),
                'absolute_path': str(file_path.absolute())
            }
            
        except Exception as e:
            return {
                'exists': True,
                'error': str(e)
            }
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """
        Clean filename by removing invalid characters
        
        Args:
            filename: Original filename
            
        Returns:
            Cleaned filename safe for filesystem
        """
        import re
        
        # Remove invalid characters
        cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove extra spaces and dots
        cleaned = re.sub(r'\s+', ' ', cleaned.strip())
        cleaned = re.sub(r'\.+', '.', cleaned)
        
        # Ensure it's not too long
        if len(cleaned) > 200:
            name, ext = os.path.splitext(cleaned)
            cleaned = name[:200-len(ext)] + ext
        
        return cleaned
    
    @staticmethod
    def find_files(directory: Union[str, Path], pattern: str = "*", 
                  recursive: bool = True) -> List[Path]:
        """
        Find files matching pattern in directory
        
        Args:
            directory: Directory to search in
            pattern: File pattern to match
            recursive: Whether to search recursively
            
        Returns:
            List of matching file paths
        """
        directory = Path(directory)
        
        if not directory.exists() or not directory.is_dir():
            return []
        
        try:
            if recursive:
                return list(directory.rglob(pattern))
            else:
                return list(directory.glob(pattern))
                
        except Exception as e:
            print(f"Error finding files in {directory}: {e}")
            return []
    
    @staticmethod
    def copy_file_safe(source: Union[str, Path], destination: Union[str, Path], 
                      overwrite: bool = False) -> bool:
        """
        Safely copy file with error handling
        
        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing file
            
        Returns:
            True if successful, False otherwise
        """
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            print(f"Source file does not exist: {source}")
            return False
        
        if destination.exists() and not overwrite:
            print(f"Destination file exists and overwrite=False: {destination}")
            return False
        
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            return True
            
        except Exception as e:
            print(f"Error copying file from {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def get_temp_file(suffix: str = "", prefix: str = "api_tester_") -> Path:
        """
        Get a temporary file path
        
        Args:
            suffix: File suffix/extension
            prefix: File prefix
            
        Returns:
            Path to temporary file
        """
        with tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, delete=False) as tmp:
            return Path(tmp.name)
    
    @staticmethod
    def cleanup_temp_files(pattern: str = "api_tester_*"):
        """
        Clean up temporary files matching pattern
        
        Args:
            pattern: Pattern to match for cleanup
        """
        temp_dir = Path(tempfile.gettempdir())
        try:
            for file_path in temp_dir.glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")
