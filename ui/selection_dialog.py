import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Optional, List
from logger import app_logger
from resource_manager import ResourceManager, get_resource_manager
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QWidget
)
from PyQt5.QtCore import Qt

class BookTestSelectionDialog(QDialog):
    """
    Startup dialog to select a book and a test number.
    Ensures the chosen book/test will be used across all sections.
    """
    def __init__(self, resource_manager: Optional[ResourceManager] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Select Book and Test")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.resource_manager = resource_manager or get_resource_manager()
        self.selected_book: Optional[str] = None
        self.selected_test: Optional[int] = None
        self._init_ui()
        self._populate_books()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        title = QLabel("Choose your IELTS book and test")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Book row
        book_row = QHBoxLayout()
        book_label = QLabel("Book:")
        book_label.setMinimumWidth(80)
        self.book_combo = QComboBox()
        self.book_combo.setMinimumWidth(250)
        self.book_combo.currentTextChanged.connect(self._on_book_changed)
        book_row.addWidget(book_label)
        book_row.addWidget(self.book_combo)
        layout.addLayout(book_row)

        # Test row
        test_row = QHBoxLayout()
        test_label = QLabel("Test:")
        test_label.setMinimumWidth(80)
        self.test_combo = QComboBox()
        self.test_combo.setMinimumWidth(250)
        test_row.addWidget(test_label)
        test_row.addWidget(self.test_combo)
        layout.addLayout(test_row)

        # Availability note
        self.note_label = QLabel("")
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet("color: #666;")
        layout.addWidget(self.note_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("Start")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def _populate_books(self):
        try:
            books = self.resource_manager.get_available_books()
            if not books:
                self.book_combo.addItem("No books found")
                self.book_combo.setEnabled(False)
                self.test_combo.setEnabled(False)
                self.note_label.setText("No IELTS books found in resources directory.")
                return
            self.book_combo.clear()
            self.book_combo.addItems(books)
            # Trigger population of tests for the first book
            if books:
                self._populate_tests_for_book(books[0])
                self.book_combo.setCurrentText(books[0])
        except Exception as e:
            app_logger.error(f"Error populating books in selection dialog: {e}")
            self.book_combo.addItem("Error loading books")

    def _available_tests_by_type(self, book: str) -> List[List[int]]:
        try:
            lt = self.resource_manager.get_available_tests(book, 'listening')
            rd = self.resource_manager.get_available_tests(book, 'reading')
            wr = self.resource_manager.get_available_tests(book, 'writing')
            sp = self.resource_manager.get_available_tests(book, 'speaking')
            return [lt, rd, wr, sp]
        except Exception as e:
            app_logger.error(f"Error retrieving tests for book {book}: {e}")
            return [[], [], [], []]

    def _populate_tests_for_book(self, book: str):
        try:
            self.test_combo.clear()
            tests_by_type = self._available_tests_by_type(book)
            # Compute intersection across all sections to ensure smooth experience
            sets = [set(t) for t in tests_by_type if t]
            if sets:
                intersection = set.intersection(*sets) if len(sets) > 1 else sets[0]
            else:
                intersection = set()

            if intersection:
                tests = sorted(intersection)
                self.note_label.setText("All sections available for selected test.")
            else:
                # Fallback to union to allow starting even when some sections are missing
                union = set().union(*[set(t) for t in tests_by_type])
                tests = sorted(union)
                if tests:
                    missing_sections = []
                    names = ['Listening', 'Reading', 'Writing', 'Speaking']
                    for idx, arr in enumerate(tests_by_type):
                        if not arr:
                            missing_sections.append(names[idx])
                    if missing_sections:
                        self.note_label.setText(
                            f"Note: Missing sections in this book: {', '.join(missing_sections)}. Some tabs may show placeholders.")
                    else:
                        self.note_label.setText("Some tests may be missing in specific sections.")
                else:
                    self.note_label.setText("No tests found for the selected book.")

            for t in tests:
                self.test_combo.addItem(f"Test {t}")
            if tests:
                self.test_combo.setCurrentText(f"Test {tests[0]}")
        except Exception as e:
            app_logger.error(f"Error populating tests for book {book}: {e}")
            self.test_combo.addItem("Error loading tests")

    def _on_book_changed(self, book: str):
        if not book or book == "No books found":
            self.test_combo.clear()
            self.test_combo.setEnabled(False)
            return
        self.test_combo.setEnabled(True)
        self._populate_tests_for_book(book)

    def _on_accept(self):
        book = self.book_combo.currentText()
        test_text = self.test_combo.currentText()
        if not book or not test_text:
            return
        try:
            test_num = int(test_text.split()[-1])
        except Exception:
            test_num = None
        self.selected_book = book
        self.selected_test = test_num
        self.accept()

    def get_selection(self):
        return self.selected_book, self.selected_test