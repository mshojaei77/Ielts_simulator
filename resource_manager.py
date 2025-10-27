"""
Dynamic Resource Manager for IELTS Test Simulator

This module provides automatic detection and management of test resources
from the resources directory, supporting any book or test material structure.
"""

import os
import re
import time
import threading
from typing import Dict, List, Set, Optional, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path
import json
from logger import app_logger


@dataclass
class TestResource:
    """Represents a single test resource file."""
    book_name: str
    test_type: str  # listening, reading, writing, speaking
    test_number: int
    part_or_task: str  # Part-1, Part-2, Task-1, Passage-1, etc.
    file_path: str
    display_name: str


@dataclass
class BookStructure:
    """Represents the complete structure of a test book."""
    name: str
    display_name: str
    directory_path: str
    test_types: Set[str]
    listening_tests: Dict[int, List[str]]  # test_num -> [Part-1, Part-2, ...]
    reading_tests: Dict[int, List[str]]    # test_num -> [Passage-1, Passage-2, ...]
    writing_tests: Dict[int, List[str]]    # test_num -> [Task-1, Task-2]
    speaking_tests: Dict[int, List[str]]   # test_num -> [Part-1, Part-2, Part-3]
    css_files: Dict[str, str]             # test_type -> css_file_path
    audio_files: Dict[str, str]           # test_identifier -> audio_file_path


class ResourceManager:
    """
    Automatically discovers and manages all test resources in the resources directory.
    
    This class provides a robust, extensible system for loading any test materials
    without requiring code changes when new books or tests are added.
    """
    
    def __init__(self, resources_base_path: str = None):
        """
        Initialize the resource manager.
        
        Args:
            resources_base_path: Path to the resources directory. 
                               If None, uses default relative path.
        """
        if resources_base_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            resources_base_path = os.path.join(base_dir, 'resources')
        
        self.resources_path = Path(resources_base_path)
        self.books: Dict[str, BookStructure] = {}
        self._change_callbacks: List[Callable] = []
        self._watcher_thread = None
        self._stop_watching = False
        self._last_scan_time = 0
        self._scan_resources()
        self._start_file_watcher()
    
    def _scan_resources(self) -> None:
        """Scan the resources directory and build the complete resource map."""
        app_logger.info(f"Scanning resources directory: {self.resources_path}")
        
        if not self.resources_path.exists():
            app_logger.warning(f"Resources directory not found: {self.resources_path}")
            return
        
        # Scan each subdirectory as a potential book
        for book_dir in self.resources_path.iterdir():
            if book_dir.is_dir():
                book_structure = self._scan_book_directory(book_dir)
                if book_structure:
                    self.books[book_structure.name] = book_structure
                    app_logger.info(f"Loaded book: {book_structure.display_name}")
        
        app_logger.info(f"Successfully loaded {len(self.books)} books")
    
    def _scan_book_directory(self, book_path: Path) -> Optional[BookStructure]:
        """
        Scan a book directory and extract its structure.
        
        Args:
            book_path: Path to the book directory
            
        Returns:
            BookStructure object or None if invalid structure
        """
        book_name = book_path.name
        display_name = self._format_display_name(book_name)
        
        book_structure = BookStructure(
            name=book_name,
            display_name=display_name,
            directory_path=str(book_path),
            test_types=set(),
            listening_tests={},
            reading_tests={},
            writing_tests={},
            speaking_tests={},
            css_files={},
            audio_files={}
        )
        
        # Scan each test type directory
        for test_type_dir in book_path.iterdir():
            if test_type_dir.is_dir():
                test_type = test_type_dir.name.lower()
                if test_type in ['listening', 'reading', 'writing', 'speaking']:
                    book_structure.test_types.add(test_type)
                    self._scan_test_type_directory(test_type_dir, test_type, book_structure)
        
        # Only return the book structure if it has valid content
        if book_structure.test_types:
            return book_structure
        return None
    
    def _scan_test_type_directory(self, test_dir: Path, test_type: str, 
                                 book_structure: BookStructure) -> None:
        """
        Scan a test type directory (listening, reading, etc.) for resources.
        
        Args:
            test_dir: Path to the test type directory
            test_type: Type of test (listening, reading, writing, speaking)
            book_structure: BookStructure to populate
        """
        # Get the appropriate test dictionary
        if test_type == 'listening':
            tests_dict = book_structure.listening_tests
        elif test_type == 'reading':
            tests_dict = book_structure.reading_tests
        elif test_type == 'writing':
            tests_dict = book_structure.writing_tests
        elif test_type == 'speaking':
            tests_dict = book_structure.speaking_tests
        else:
            return
        
        # Scan files in the directory
        for file_path in test_dir.iterdir():
            if file_path.is_file():
                filename = file_path.name
                
                # Check for CSS files
                if filename.endswith('.css'):
                    book_structure.css_files[test_type] = str(file_path)
                    continue
                
                # Check for audio files
                if filename.endswith(('.mp3', '.wav', '.m4a')):
                    audio_key = f"{test_type}-{filename}"
                    book_structure.audio_files[audio_key] = str(file_path)
                    continue
                
                # Check for HTML test files
                if filename.endswith('.html'):
                    test_info = self._parse_test_filename(filename)
                    if test_info:
                        test_num, part_or_task = test_info
                        
                        if test_num not in tests_dict:
                            tests_dict[test_num] = []
                        
                        tests_dict[test_num].append(part_or_task)
        
        # Sort parts/tasks for each test
        for test_num in tests_dict:
            tests_dict[test_num] = sorted(tests_dict[test_num], 
                                        key=self._sort_key_for_parts)
    
    def _parse_test_filename(self, filename: str) -> Optional[Tuple[int, str]]:
        """
        Parse a test filename to extract test number and part/task information.
        
        Expected formats:
        - Test-1-Part-1.html
        - Test-2-Task-1.html
        - Test-3-Passage-1.html
        
        Args:
            filename: The filename to parse
            
        Returns:
            Tuple of (test_number, part_or_task) or None if invalid
        """
        # Remove .html extension
        name_without_ext = filename.replace('.html', '')
        
        # Pattern to match Test-X-Type-Y format
        pattern = r'Test-(\d+)-(Part|Task|Passage)-(\d+)'
        match = re.match(pattern, name_without_ext)
        
        if match:
            test_num = int(match.group(1))
            part_type = match.group(2)
            part_num = int(match.group(3))
            part_or_task = f"{part_type}-{part_num}"
            return test_num, part_or_task
        
        return None
    
    def _sort_key_for_parts(self, part_name: str) -> Tuple[str, int]:
        """
        Generate a sort key for part/task names to ensure proper ordering.
        
        Args:
            part_name: Name like "Part-1", "Task-2", "Passage-3"
            
        Returns:
            Tuple for sorting
        """
        if '-' in part_name:
            part_type, part_num_str = part_name.split('-', 1)
            try:
                part_num = int(part_num_str)
                return (part_type, part_num)
            except ValueError:
                pass
        
        return (part_name, 0)
    
    def _format_display_name(self, book_name: str) -> str:
        """
        Format a book directory name into a user-friendly display name.
        
        Args:
            book_name: Directory name like "Cambridge20"
            
        Returns:
            Formatted display name like "Cambridge 20"
        """
        # Handle Cambridge books
        cambridge_match = re.match(r'Cambridge(\d+)', book_name)
        if cambridge_match:
            return f"Cambridge {cambridge_match.group(1)}"
        
        # Handle other formats - add spaces before numbers
        formatted = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', book_name)
        return formatted
    
    def get_available_books(self) -> List[str]:
        """
        Get list of available book display names.
        
        Returns:
            List of book display names sorted alphabetically
        """
        return sorted([book.display_name for book in self.books.values()])
    
    def get_book_by_display_name(self, display_name: str) -> Optional[BookStructure]:
        """
        Get book structure by display name.
        
        Args:
            display_name: Display name like "Cambridge 20"
            
        Returns:
            BookStructure or None if not found
        """
        for book in self.books.values():
            if book.display_name == display_name:
                return book
        return None
    
    def get_available_tests(self, book_display_name: str, test_type: str) -> List[int]:
        """
        Get available test numbers for a specific book and test type.
        
        Args:
            book_display_name: Display name of the book
            test_type: Type of test (listening, reading, writing, speaking)
            
        Returns:
            List of available test numbers
        """
        book = self.get_book_by_display_name(book_display_name)
        if not book:
            return []
        
        test_type = test_type.lower()
        if test_type == 'listening':
            return sorted(book.listening_tests.keys())
        elif test_type == 'reading':
            return sorted(book.reading_tests.keys())
        elif test_type == 'writing':
            return sorted(book.writing_tests.keys())
        elif test_type == 'speaking':
            return sorted(book.speaking_tests.keys())
        
        return []
    
    def get_available_test_files(self, book_display_name: str, test_type: str) -> List[str]:
        """
        Get available test filenames for a specific book and test type.
        
        Args:
            book_display_name: Display name of the book
            test_type: Type of test (listening, reading, writing, speaking)
            
        Returns:
            List of available test filenames
        """
        book = self.get_book_by_display_name(book_display_name)
        if not book:
            return []
        
        test_type = test_type.lower()
        all_files = []
        
        if test_type == 'listening':
            for test_num, parts in book.listening_tests.items():
                for part in parts:
                    all_files.append(part)
        elif test_type == 'reading':
            for test_num, parts in book.reading_tests.items():
                for part in parts:
                    all_files.append(part)
        elif test_type == 'writing':
            for test_num, parts in book.writing_tests.items():
                for part in parts:
                    all_files.append(part)
        elif test_type == 'speaking':
            for test_num, parts in book.speaking_tests.items():
                for part in parts:
                    all_files.append(part)
        
        return sorted(all_files)
    
    def get_test_parts(self, book_display_name: str, test_type: str, 
                      test_number: int) -> List[str]:
        """
        Get available parts/tasks for a specific test.
        
        Args:
            book_display_name: Display name of the book
            test_type: Type of test
            test_number: Test number
            
        Returns:
            List of part/task names
        """
        book = self.get_book_by_display_name(book_display_name)
        if not book:
            return []
        
        test_type = test_type.lower()
        if test_type == 'listening':
            return book.listening_tests.get(test_number, [])
        elif test_type == 'reading':
            return book.reading_tests.get(test_number, [])
        elif test_type == 'writing':
            return book.writing_tests.get(test_number, [])
        elif test_type == 'speaking':
            return book.speaking_tests.get(test_number, [])
        
        return []
    
    def get_resource_path(self, book_display_name: str, test_type: str, 
                         test_number: int, part_or_task: str) -> Optional[str]:
        """
        Get the file path for a specific test resource.
        
        Args:
            book_display_name: Display name of the book
            test_type: Type of test
            test_number: Test number
            part_or_task: Part or task identifier
            
        Returns:
            Relative path to the resource file or None if not found
        """
        book = self.get_book_by_display_name(book_display_name)
        if not book:
            return None
        
        filename = f"Test-{test_number}-{part_or_task}.html"
        resource_path = os.path.join("resources", book.name, test_type.lower(), filename)
        
        # Verify the file exists
        full_path = os.path.join(os.path.dirname(__file__), resource_path)
        if os.path.exists(full_path):
            return resource_path
        
        return None
    
    def get_css_path(self, book_display_name: str, test_type: str) -> Optional[str]:
        """
        Get the CSS file path for a specific test type.
        
        Args:
            book_display_name: Display name of the book
            test_type: Type of test
            
        Returns:
            Path to CSS file or None if not found
        """
        book = self.get_book_by_display_name(book_display_name)
        if not book:
            return None
        
        return book.css_files.get(test_type.lower())
    
    def get_audio_files(self, book_display_name: str, test_type: str = 'listening') -> Dict[str, str]:
        """
        Get available audio files for a book and test type.
        
        Args:
            book_display_name: Display name of the book
            test_type: Type of test (usually 'listening')
            
        Returns:
            Dictionary mapping audio identifiers to file paths
        """
        book = self.get_book_by_display_name(book_display_name)
        if not book:
            return {}
        
        # Filter audio files by test type
        audio_files = {}
        prefix = f"{test_type.lower()}-"
        
        for key, path in book.audio_files.items():
            if key.startswith(prefix):
                audio_files[key] = path
        
        return audio_files
    
    def refresh_resources(self) -> None:
        """Refresh the resource cache by re-scanning the directory."""
        self.books.clear()
        self._scan_resources()
        self._last_scan_time = time.time()
        app_logger.info("Resource cache refreshed")
    
    def get_resource_summary(self) -> Dict:
        """
        Get a summary of all available resources.
        
        Returns:
            Dictionary containing resource summary information
        """
        summary = {
            'total_books': len(self.books),
            'books': {}
        }
        
        for book_name, book in self.books.items():
            book_summary = {
                'display_name': book.display_name,
                'test_types': list(book.test_types),
                'total_tests': {
                    'listening': len(book.listening_tests),
                    'reading': len(book.reading_tests),
                    'writing': len(book.writing_tests),
                    'speaking': len(book.speaking_tests)
                },
                'css_files': len(book.css_files),
                'audio_files': len(book.audio_files)
            }
            summary['books'][book_name] = book_summary
        
        return summary
    
    def _start_file_watcher(self) -> None:
        """Start the file watcher thread for monitoring resource changes."""
        if self._watcher_thread is None or not self._watcher_thread.is_alive():
            self._stop_watching = False
            self._watcher_thread = threading.Thread(target=self._watch_resources, daemon=True)
            self._watcher_thread.start()
            app_logger.info("File watcher started for resource monitoring")
    
    def _watch_resources(self) -> None:
        """Monitor the resources directory for changes."""
        while not self._stop_watching:
            try:
                current_time = time.time()
                
                # Check if resources directory has been modified
                if self.resources_path.exists():
                    # Get the latest modification time of any file in the resources directory
                    latest_mod_time = self._get_latest_modification_time(self.resources_path)
                    
                    # If modification time is newer than last scan, refresh resources
                    if latest_mod_time > self._last_scan_time:
                        app_logger.info("Resource changes detected, refreshing...")
                        old_books = set(self.books.keys())
                        self.refresh_resources()
                        new_books = set(self.books.keys())
                        
                        # Notify callbacks about changes
                        if old_books != new_books:
                            self._notify_change_callbacks()
                        
                        self._last_scan_time = current_time
                
                # Sleep for 2 seconds before next check
                time.sleep(2)
                
            except Exception as e:
                app_logger.error(f"Error in file watcher: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _get_latest_modification_time(self, directory: Path) -> float:
        """Get the latest modification time of any file in the directory tree."""
        latest_time = 0
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        mod_time = os.path.getmtime(file_path)
                        latest_time = max(latest_time, mod_time)
                    except (OSError, IOError):
                        continue  # Skip files that can't be accessed
        except Exception:
            pass  # Return 0 if directory can't be accessed
        return latest_time
    
    def add_change_callback(self, callback: Callable) -> None:
        """
        Add a callback function to be called when resources change.
        
        Args:
            callback: Function to call when resources are updated
        """
        if callback not in self._change_callbacks:
            self._change_callbacks.append(callback)
            app_logger.debug(f"Added resource change callback: {callback.__name__}")
    
    def remove_change_callback(self, callback: Callable) -> None:
        """
        Remove a callback function from the change notification list.
        
        Args:
            callback: Function to remove from callbacks
        """
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
            app_logger.debug(f"Removed resource change callback: {callback.__name__}")
    
    def _notify_change_callbacks(self) -> None:
        """Notify all registered callbacks about resource changes."""
        for callback in self._change_callbacks:
            try:
                callback()
                app_logger.debug(f"Notified callback: {callback.__name__}")
            except Exception as e:
                app_logger.error(f"Error calling change callback {callback.__name__}: {e}")
    
    def stop_file_watcher(self) -> None:
        """Stop the file watcher thread."""
        self._stop_watching = True
        if self._watcher_thread and self._watcher_thread.is_alive():
            self._watcher_thread.join(timeout=5)
            app_logger.info("File watcher stopped")


# Global resource manager instance
_resource_manager = None


def get_resource_manager() -> ResourceManager:
    """
    Get the global resource manager instance.
    
    Returns:
        ResourceManager instance
    """
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager


def refresh_resources() -> None:
    """Refresh the global resource manager cache."""
    global _resource_manager
    if _resource_manager is not None:
        _resource_manager.refresh_resources()


if __name__ == "__main__":
    # Demo usage
    rm = ResourceManager()
    summary = rm.get_resource_summary()
    
    print("=== IELTS Resource Manager Summary ===")
    print(f"Total books found: {summary['total_books']}")
    print()
    
    for book_name, book_info in summary['books'].items():
        print(f"📚 {book_info['display_name']}")
        print(f"   Test types: {', '.join(book_info['test_types'])}")
        for test_type, count in book_info['total_tests'].items():
            if count > 0:
                print(f"   {test_type.title()}: {count} tests")
        print(f"   CSS files: {book_info['css_files']}")
        print(f"   Audio files: {book_info['audio_files']}")
        print()