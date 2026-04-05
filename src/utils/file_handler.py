"""
File handling utilities for jmAgent.

Provides functions for reading, writing, and manipulating files with
proper error handling and validation.
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Any, Dict


def read_file(file_path: str) -> Optional[str]:
    """
    Read content from a file.

    Args:
        file_path: Path to the file to read

    Returns:
        File content as string, or None if file doesn't exist
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        return path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def write_file(file_path: str, content: str) -> bool:
    """
    Write content to a file.

    Args:
        file_path: Path to the file to write
        content: Content to write

    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        return False


def file_exists(file_path: str) -> bool:
    """
    Check if a file exists.

    Args:
        file_path: Path to check

    Returns:
        True if file exists, False otherwise
    """
    return Path(file_path).exists()


def get_file_size(file_path: str) -> Optional[int]:
    """
    Get file size in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes, or None if file doesn't exist
    """
    try:
        return Path(file_path).stat().st_size
    except Exception:
        return None


def find_files(directory: str, pattern: str = "*") -> List[str]:
    """
    Find files matching a pattern in directory.

    Args:
        directory: Directory to search
        pattern: File pattern (e.g., "*.py")

    Returns:
        List of matching file paths
    """
    try:
        path = Path(directory)
        return [str(f) for f in path.glob(pattern)]
    except Exception:
        return []


def is_text_file(file_path: str) -> bool:
    """
    Check if file appears to be a text file.

    Args:
        file_path: Path to check

    Returns:
        True if likely text file, False otherwise
    """
    text_extensions = {
        '.py', '.js', '.ts', '.tsx', '.jsx',
        '.java', '.c', '.cpp', '.h', '.hpp',
        '.go', '.rs', '.rb', '.php', '.sh',
        '.yaml', '.yml', '.json', '.xml',
        '.html', '.css', '.sql', '.md', '.txt'
    }

    ext = Path(file_path).suffix.lower()
    return ext in text_extensions


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON from file.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data, or None if error
    """
    try:
        content = read_file(file_path)
        if content is None:
            return None
        return json.loads(content)
    except Exception as e:
        print(f"Error loading JSON from {file_path}: {e}")
        return None


def save_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """
    Save data to JSON file.

    Args:
        file_path: Path to write to
        data: Data to save

    Returns:
        True if successful, False otherwise
    """
    try:
        content = json.dumps(data, indent=2)
        return write_file(file_path, content)
    except Exception as e:
        print(f"Error saving JSON to {file_path}: {e}")
        return False
