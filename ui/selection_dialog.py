import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Optional, List
from logger import app_logger
from resource_manager import ResourceManager, get_resource_manager
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt

class BookTestSelectionDialog(QDialog):
    """
    Startup dialog to select a book and a test number.
    Ensures the chosen book/test will be used across all sections.
    """
    def __init__(self, resource_manager: Optional[ResourceManager] = None, parent: Optional[QWidget] = None):
        try:
            super().__init__(parent)
            app_logger.debug("Initializing BookTestSelectionDialog")
            
            # Initialize basic dialog properties with error handling
            try:
                self.setWindowTitle("Select Book and Test")
                self.setModal(True)
                self.setMinimumWidth(420)
                app_logger.debug("Dialog properties set successfully")
            except Exception as e:
                app_logger.error(f"Error setting dialog properties: {e}", exc_info=True)
                # Continue with defaults
            
            # Initialize resource manager with validation
            try:
                if resource_manager is not None:
                    self.resource_manager = resource_manager
                    app_logger.debug("Using provided resource manager")
                else:
                    self.resource_manager = get_resource_manager()
                    app_logger.debug("Using default resource manager")
            except Exception as e:
                app_logger.error(f"Error initializing resource manager: {e}", exc_info=True)
                try:
                    self.resource_manager = get_resource_manager()
                    app_logger.warning("Fallback to default resource manager succeeded")
                except Exception as fallback_error:
                    app_logger.critical(f"Failed to initialize any resource manager: {fallback_error}", exc_info=True)
                    QMessageBox.critical(self, "Critical Error", 
                                       "Failed to initialize resource manager. Application cannot continue.")
                    self.reject()
                    return
            
            # Initialize selection attributes
            try:
                self.selected_book: Optional[str] = None
                self.selected_test: Optional[int] = None
                app_logger.debug("Selection attributes initialized")
            except Exception as e:
                app_logger.error(f"Error initializing selection attributes: {e}", exc_info=True)
                self.selected_book = None
                self.selected_test = None
            
            # Initialize UI components
            try:
                self._init_ui()
                app_logger.debug("UI initialization completed")
            except Exception as e:
                app_logger.error(f"Error during UI initialization: {e}", exc_info=True)
                QMessageBox.critical(self, "UI Error", 
                                   "Failed to initialize user interface. Please restart the application.")
                self.reject()
                return
            
            # Populate books data
            try:
                self._populate_books()
                app_logger.debug("Books population completed")
            except Exception as e:
                app_logger.error(f"Error during books population: {e}", exc_info=True)
                QMessageBox.warning(self, "Data Loading Warning", 
                                  "Failed to load book data. Some features may not work correctly.")
                
        except Exception as e:
            app_logger.critical(f"Critical error in BookTestSelectionDialog initialization: {e}", exc_info=True)
            try:
                QMessageBox.critical(self, "Critical Error", 
                                   "Failed to initialize selection dialog. Application will close.")
            except:
                pass  # Even message box failed
            self.reject()

    def _init_ui(self):
        """Initialize the user interface with comprehensive error handling."""
        try:
            app_logger.debug("Starting UI initialization")
            
            # Create main layout with error handling
            try:
                layout = QVBoxLayout(self)
                layout.setContentsMargins(15, 15, 15, 15)
                layout.setSpacing(12)
                app_logger.debug("Main layout created successfully")
            except Exception as e:
                app_logger.error(f"Error creating main layout: {e}", exc_info=True)
                raise
            
            # Create title label with error handling
            try:
                title = QLabel("Choose your IELTS book and test")
                title.setStyleSheet("font-size: 16px; font-weight: bold;")
                layout.addWidget(title)
                app_logger.debug("Title label created successfully")
            except Exception as e:
                app_logger.error(f"Error creating title label: {e}", exc_info=True)
                # Continue without title styling
                try:
                    title = QLabel("Choose your IELTS book and test")
                    layout.addWidget(title)
                except Exception as fallback_error:
                    app_logger.warning(f"Failed to create fallback title: {fallback_error}")
            
            # Create book selection row with error handling
            try:
                book_row = QHBoxLayout()
                book_label = QLabel("Book:")
                book_label.setMinimumWidth(80)
                
                self.book_combo = QComboBox()
                self.book_combo.setMinimumWidth(250)
                
                try:
                    self.book_combo.currentTextChanged.connect(self._on_book_changed)
                    app_logger.debug("Book combo signal connected successfully")
                except Exception as signal_error:
                    app_logger.error(f"Error connecting book combo signal: {signal_error}", exc_info=True)
                    # Continue without signal connection
                
                book_row.addWidget(book_label)
                book_row.addWidget(self.book_combo)
                layout.addLayout(book_row)
                app_logger.debug("Book selection row created successfully")
            except Exception as e:
                app_logger.error(f"Error creating book selection row: {e}", exc_info=True)
                raise
            
            # Create test selection row with error handling
            try:
                test_row = QHBoxLayout()
                test_label = QLabel("Test:")
                test_label.setMinimumWidth(80)
                
                self.test_combo = QComboBox()
                self.test_combo.setMinimumWidth(250)
                
                test_row.addWidget(test_label)
                test_row.addWidget(self.test_combo)
                layout.addLayout(test_row)
                app_logger.debug("Test selection row created successfully")
            except Exception as e:
                app_logger.error(f"Error creating test selection row: {e}", exc_info=True)
                raise
            
            # Create availability note label with error handling
            try:
                self.note_label = QLabel("")
                self.note_label.setWordWrap(True)
                self.note_label.setStyleSheet("color: #666;")
                layout.addWidget(self.note_label)
                app_logger.debug("Note label created successfully")
            except Exception as e:
                app_logger.error(f"Error creating note label: {e}", exc_info=True)
                # Continue without note label styling
                try:
                    self.note_label = QLabel("")
                    self.note_label.setWordWrap(True)
                    layout.addWidget(self.note_label)
                except Exception as fallback_error:
                    app_logger.warning(f"Failed to create fallback note label: {fallback_error}")
                    self.note_label = None
            
            # Create buttons row with error handling
            try:
                btn_row = QHBoxLayout()
                btn_row.addStretch()
                
                cancel_btn = QPushButton("Cancel")
                try:
                    cancel_btn.clicked.connect(self.reject)
                    app_logger.debug("Cancel button signal connected successfully")
                except Exception as signal_error:
                    app_logger.error(f"Error connecting cancel button signal: {signal_error}", exc_info=True)
                
                ok_btn = QPushButton("Start")
                ok_btn.setDefault(True)
                try:
                    ok_btn.clicked.connect(self._on_accept)
                    app_logger.debug("OK button signal connected successfully")
                except Exception as signal_error:
                    app_logger.error(f"Error connecting OK button signal: {signal_error}", exc_info=True)
                
                btn_row.addWidget(cancel_btn)
                btn_row.addWidget(ok_btn)
                layout.addLayout(btn_row)
                app_logger.debug("Buttons row created successfully")
            except Exception as e:
                app_logger.error(f"Error creating buttons row: {e}", exc_info=True)
                raise
                
        except Exception as e:
            app_logger.critical(f"Critical error in UI initialization: {e}", exc_info=True)
            raise

    def _populate_books(self):
        """Populate the books dropdown with comprehensive error handling."""
        try:
            app_logger.debug("Starting books population")
            
            # Validate resource manager
            if not hasattr(self, 'resource_manager') or self.resource_manager is None:
                app_logger.error("Resource manager not available for books population")
                try:
                    if hasattr(self, 'book_combo'):
                        self.book_combo.addItem("Error: No resource manager")
                        self.book_combo.setEnabled(False)
                    if hasattr(self, 'test_combo'):
                        self.test_combo.setEnabled(False)
                    if hasattr(self, 'note_label') and self.note_label is not None:
                        self.note_label.setText("Error: Resource manager not available.")
                except Exception as ui_error:
                    app_logger.error(f"Error updating UI for resource manager error: {ui_error}")
                return
            
            # Get available books with error handling
            try:
                books = self.resource_manager.get_available_books()
                app_logger.debug(f"Retrieved {len(books) if books else 0} books from resource manager")
            except Exception as e:
                app_logger.error(f"Error retrieving books from resource manager: {e}", exc_info=True)
                try:
                    if hasattr(self, 'book_combo'):
                        self.book_combo.addItem("Error loading books")
                        self.book_combo.setEnabled(False)
                    if hasattr(self, 'test_combo'):
                        self.test_combo.setEnabled(False)
                    if hasattr(self, 'note_label') and self.note_label is not None:
                        self.note_label.setText("Error loading books from resources.")
                except Exception as ui_error:
                    app_logger.error(f"Error updating UI for books loading error: {ui_error}")
                return
            
            # Handle empty books list
            if not books:
                app_logger.warning("No books found in resource manager")
                try:
                    if hasattr(self, 'book_combo'):
                        self.book_combo.addItem("No books found")
                        self.book_combo.setEnabled(False)
                    if hasattr(self, 'test_combo'):
                        self.test_combo.setEnabled(False)
                    if hasattr(self, 'note_label') and self.note_label is not None:
                        self.note_label.setText("No IELTS books found in resources directory.")
                except Exception as ui_error:
                    app_logger.error(f"Error updating UI for empty books: {ui_error}")
                return
            
            # Populate book combo box with error handling
            try:
                if hasattr(self, 'book_combo'):
                    self.book_combo.clear()
                    self.book_combo.addItems(books)
                    app_logger.debug("Book combo populated successfully")
                else:
                    app_logger.error("Book combo widget not available")
                    return
            except Exception as e:
                app_logger.error(f"Error populating book combo: {e}", exc_info=True)
                return
            
            # Set default book with error handling
            try:
                default_book = "Cambridge 20" if "Cambridge 20" in books else books[0]
                app_logger.debug(f"Setting default book: {default_book}")
                
                try:
                    self._populate_tests_for_book(default_book)
                    app_logger.debug("Tests populated for default book")
                except Exception as tests_error:
                    app_logger.error(f"Error populating tests for default book: {tests_error}", exc_info=True)
                
                try:
                    self.book_combo.setCurrentText(default_book)
                    app_logger.debug("Default book set successfully")
                except Exception as set_error:
                    app_logger.error(f"Error setting default book: {set_error}", exc_info=True)
                    
            except Exception as e:
                app_logger.error(f"Error setting default book: {e}", exc_info=True)
                
        except Exception as e:
            app_logger.critical(f"Critical error in books population: {e}", exc_info=True)
            try:
                if hasattr(self, 'book_combo'):
                    self.book_combo.addItem("Error loading books")
                    self.book_combo.setEnabled(False)
            except Exception as ui_error:
                app_logger.error(f"Error updating UI for critical books error: {ui_error}")

    def _available_tests_by_type(self, book: str) -> List[List[int]]:
        """Get available tests by type with comprehensive error handling."""
        try:
            app_logger.debug(f"Getting available tests for book: {book}")
            
            # Validate input
            if not book or not isinstance(book, str):
                app_logger.warning(f"Invalid book parameter: {book}")
                return [[], [], [], []]
            
            # Validate resource manager
            if not hasattr(self, 'resource_manager') or self.resource_manager is None:
                app_logger.error("Resource manager not available for tests retrieval")
                return [[], [], [], []]
            
            # Get tests for each type with individual error handling
            test_types = ['listening', 'reading', 'writing', 'speaking']
            results = []
            
            for test_type in test_types:
                try:
                    tests = self.resource_manager.get_available_tests(book, test_type)
                    if tests is None:
                        tests = []
                    results.append(tests)
                    app_logger.debug(f"Retrieved {len(tests)} {test_type} tests for {book}")
                except Exception as e:
                    app_logger.error(f"Error retrieving {test_type} tests for book {book}: {e}", exc_info=True)
                    results.append([])
            
            return results
            
        except Exception as e:
            app_logger.critical(f"Critical error retrieving tests for book {book}: {e}", exc_info=True)
            return [[], [], [], []]

    def _populate_tests_for_book(self, book: str):
        """Populate tests dropdown for selected book with comprehensive error handling."""
        try:
            app_logger.debug(f"Populating tests for book: {book}")
            
            # Validate input
            if not book or not isinstance(book, str):
                app_logger.warning(f"Invalid book parameter for test population: {book}")
                try:
                    if hasattr(self, 'test_combo'):
                        self.test_combo.clear()
                        self.test_combo.addItem("Invalid book selection")
                        self.test_combo.setEnabled(False)
                except Exception as ui_error:
                    app_logger.error(f"Error updating UI for invalid book: {ui_error}")
                return
            
            # Clear test combo with error handling
            try:
                if hasattr(self, 'test_combo'):
                    self.test_combo.clear()
                    app_logger.debug("Test combo cleared successfully")
                else:
                    app_logger.error("Test combo widget not available")
                    return
            except Exception as e:
                app_logger.error(f"Error clearing test combo: {e}", exc_info=True)
                return
            
            # Get tests by type with error handling
            try:
                tests_by_type = self._available_tests_by_type(book)
                app_logger.debug(f"Retrieved tests by type: {[len(t) for t in tests_by_type]}")
            except Exception as e:
                app_logger.error(f"Error getting tests by type: {e}", exc_info=True)
                try:
                    self.test_combo.addItem("Error loading tests")
                    self.test_combo.setEnabled(False)
                    if hasattr(self, 'note_label') and self.note_label is not None:
                        self.note_label.setText("Error loading tests for selected book.")
                except Exception as ui_error:
                    app_logger.error(f"Error updating UI for tests loading error: {ui_error}")
                return
            
            # Compute intersection and union with error handling
            try:
                sets = [set(t) for t in tests_by_type if t]
                if sets:
                    intersection = set.intersection(*sets) if len(sets) > 1 else sets[0]
                else:
                    intersection = set()
                app_logger.debug(f"Test intersection: {sorted(intersection) if intersection else 'empty'}")
            except Exception as e:
                app_logger.error(f"Error computing test intersection: {e}", exc_info=True)
                intersection = set()
            
            # Determine available tests and update note
            try:
                if intersection:
                    tests = sorted(intersection)
                    note_text = "All sections available for selected test."
                    app_logger.debug(f"Using intersection tests: {tests}")
                else:
                    # Fallback to union
                    try:
                        union = set().union(*[set(t) for t in tests_by_type])
                        tests = sorted(union)
                        app_logger.debug(f"Using union tests: {tests}")
                        
                        if tests:
                            # Determine missing sections
                            missing_sections = []
                            names = ['Listening', 'Reading', 'Writing', 'Speaking']
                            for idx, arr in enumerate(tests_by_type):
                                if not arr:
                                    missing_sections.append(names[idx])
                            
                            if missing_sections:
                                note_text = f"Note: Missing sections in this book: {', '.join(missing_sections)}. Some tabs may show placeholders."
                            else:
                                note_text = "Some tests may be missing in specific sections."
                        else:
                            note_text = "No tests found for the selected book."
                    except Exception as union_error:
                        app_logger.error(f"Error computing test union: {union_error}", exc_info=True)
                        tests = []
                        note_text = "Error determining available tests."
                
                # Update note label
                try:
                    if hasattr(self, 'note_label') and self.note_label is not None:
                        self.note_label.setText(note_text)
                        app_logger.debug("Note label updated successfully")
                except Exception as note_error:
                    app_logger.error(f"Error updating note label: {note_error}", exc_info=True)
                    
            except Exception as e:
                app_logger.error(f"Error determining available tests: {e}", exc_info=True)
                tests = []
                note_text = "Error processing test data."
            
            # Populate test combo with error handling
            try:
                for t in tests:
                    try:
                        self.test_combo.addItem(f"Test {t}")
                    except Exception as item_error:
                        app_logger.error(f"Error adding test {t} to combo: {item_error}")
                
                if tests:
                    # Set default test
                    try:
                        default_test = 1 if 1 in tests else tests[0]
                        self.test_combo.setCurrentText(f"Test {default_test}")
                        app_logger.debug(f"Default test set to: {default_test}")
                    except Exception as default_error:
                        app_logger.error(f"Error setting default test: {default_error}", exc_info=True)
                else:
                    try:
                        self.test_combo.addItem("No tests available")
                        self.test_combo.setEnabled(False)
                    except Exception as no_tests_error:
                        app_logger.error(f"Error handling no tests case: {no_tests_error}")
                        
            except Exception as e:
                app_logger.error(f"Error populating test combo: {e}", exc_info=True)
                try:
                    self.test_combo.addItem("Error loading tests")
                    self.test_combo.setEnabled(False)
                except Exception as error_ui_error:
                    app_logger.error(f"Error updating UI for test combo error: {error_ui_error}")
                    
        except Exception as e:
            app_logger.critical(f"Critical error populating tests for book {book}: {e}", exc_info=True)
            try:
                if hasattr(self, 'test_combo'):
                    self.test_combo.addItem("Error loading tests")
                    self.test_combo.setEnabled(False)
            except Exception as ui_error:
                app_logger.error(f"Error updating UI for critical test error: {ui_error}")

    def _on_book_changed(self, book: str):
        """Handle book selection change with comprehensive error handling."""
        try:
            app_logger.debug(f"Book changed to: {book}")
            
            # Validate input
            if not book or not isinstance(book, str):
                app_logger.warning(f"Invalid book parameter in change handler: {book}")
                try:
                    if hasattr(self, 'test_combo'):
                        self.test_combo.clear()
                        self.test_combo.setEnabled(False)
                except Exception as ui_error:
                    app_logger.error(f"Error updating UI for invalid book change: {ui_error}")
                return
            
            # Handle special cases
            if book == "No books found" or book.startswith("Error"):
                app_logger.debug("Handling special book selection case")
                try:
                    if hasattr(self, 'test_combo'):
                        self.test_combo.clear()
                        self.test_combo.setEnabled(False)
                except Exception as ui_error:
                    app_logger.error(f"Error handling special book case: {ui_error}")
                return
            
            # Enable test combo and populate tests
            try:
                if hasattr(self, 'test_combo'):
                    self.test_combo.setEnabled(True)
                    app_logger.debug("Test combo enabled")
                else:
                    app_logger.error("Test combo widget not available")
                    return
            except Exception as e:
                app_logger.error(f"Error enabling test combo: {e}", exc_info=True)
            
            # Populate tests for selected book
            try:
                self._populate_tests_for_book(book)
                app_logger.debug("Tests populated for changed book")
            except Exception as e:
                app_logger.error(f"Error populating tests for changed book: {e}", exc_info=True)
                try:
                    if hasattr(self, 'test_combo'):
                        self.test_combo.clear()
                        self.test_combo.addItem("Error loading tests")
                        self.test_combo.setEnabled(False)
                except Exception as ui_error:
                    app_logger.error(f"Error updating UI for test population error: {ui_error}")
                    
        except Exception as e:
            app_logger.critical(f"Critical error in book change handler: {e}", exc_info=True)

    def _on_accept(self):
        """Handle accept button click with comprehensive error handling."""
        try:
            app_logger.debug("Accept button clicked")
            
            # Get current selections with error handling
            try:
                if hasattr(self, 'book_combo'):
                    book = self.book_combo.currentText()
                    app_logger.debug(f"Selected book: {book}")
                else:
                    app_logger.error("Book combo widget not available")
                    QMessageBox.warning(self, "Selection Error", "Book selection not available.")
                    return
                    
                if hasattr(self, 'test_combo'):
                    test_text = self.test_combo.currentText()
                    app_logger.debug(f"Selected test text: {test_text}")
                else:
                    app_logger.error("Test combo widget not available")
                    QMessageBox.warning(self, "Selection Error", "Test selection not available.")
                    return
            except Exception as e:
                app_logger.error(f"Error getting current selections: {e}", exc_info=True)
                QMessageBox.warning(self, "Selection Error", "Failed to get current selections.")
                return
            
            # Validate selections
            if not book or not test_text:
                app_logger.warning("Empty book or test selection")
                QMessageBox.warning(self, "Selection Required", "Please select both a book and a test.")
                return
            
            # Handle special cases
            if book in ["No books found", "Error loading books"] or test_text in ["No tests available", "Error loading tests"]:
                app_logger.warning("Invalid book or test selection")
                QMessageBox.warning(self, "Invalid Selection", "Please select valid book and test options.")
                return
            
            # Parse test number with error handling
            try:
                test_num = int(test_text.split()[-1])
                app_logger.debug(f"Parsed test number: {test_num}")
            except (ValueError, IndexError, AttributeError) as e:
                app_logger.error(f"Error parsing test number from '{test_text}': {e}", exc_info=True)
                QMessageBox.warning(self, "Selection Error", "Invalid test selection format.")
                return
            except Exception as e:
                app_logger.error(f"Unexpected error parsing test number: {e}", exc_info=True)
                test_num = None
            
            # Validate parsed test number
            if test_num is None or test_num <= 0:
                app_logger.warning(f"Invalid test number: {test_num}")
                QMessageBox.warning(self, "Selection Error", "Invalid test number.")
                return
            
            # Set selections with error handling
            try:
                self.selected_book = book
                self.selected_test = test_num
                app_logger.info(f"Selection confirmed: book='{book}', test={test_num}")
            except Exception as e:
                app_logger.error(f"Error setting selections: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", "Failed to save selections.")
                return
            
            # Accept dialog with error handling
            try:
                self.accept()
                app_logger.debug("Dialog accepted successfully")
            except Exception as e:
                app_logger.error(f"Error accepting dialog: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", "Failed to close dialog.")
                
        except Exception as e:
            app_logger.critical(f"Critical error in accept handler: {e}", exc_info=True)
            try:
                QMessageBox.critical(self, "Critical Error", "An unexpected error occurred. Please try again.")
            except:
                pass  # Even message box failed

    def get_selection(self):
        """Get the current selection with error handling."""
        try:
            app_logger.debug("Getting current selection")
            
            # Validate attributes exist
            if not hasattr(self, 'selected_book'):
                app_logger.warning("selected_book attribute not found")
                self.selected_book = None
            if not hasattr(self, 'selected_test'):
                app_logger.warning("selected_test attribute not found")
                self.selected_test = None
            
            selection = (self.selected_book, self.selected_test)
            app_logger.debug(f"Returning selection: {selection}")
            return selection
            
        except Exception as e:
            app_logger.error(f"Error getting selection: {e}", exc_info=True)
            return (None, None)