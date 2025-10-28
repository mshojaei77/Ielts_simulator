import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import app_logger
from resource_manager import get_resource_manager
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QSplitter, QComboBox, QPushButton, QStackedWidget,
                             QMessageBox, QFrame, QSizePolicy, QFileDialog,
                             QCheckBox, QRadioButton, QButtonGroup, QDialog,
                             QTabWidget, QScrollArea, QApplication, QSpacerItem)
from PyQt5.QtCore import Qt, QTimer, QTime, QUrl, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCursor, QPalette, QTextFormat, QIcon
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from datetime import datetime

class WritingTestUI(QWidget):
    def __init__(self, selected_book: str = None, selected_test: int = None):
        super().__init__()
        self.module_type = "academic"  # Always academic now
        
        # Initialize resource manager
        self.resource_manager = get_resource_manager()
        
        # Fixed selection context (no in-app switching)
        self.selected_book = selected_book
        self.selected_test = int(selected_test) if selected_test is not None else None
        
        self.subjects = self.load_subjects(self.selected_book)
        self.task1_time = 20 * 60  # 20 minutes in seconds
        self.task2_time = 40 * 60  # 40 minutes in seconds
        self.total_time = self.task1_time + self.task2_time  # 60 minutes total
        self.time_remaining = self.total_time
        self.current_task = 0  # 0 for Task 1, 1 for Task 2
        self.current_passage = 0  # For navigation
        self.total_passages = 2  # Task 1 and Task 2
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_display)
        self.test_started = False
        self.completed_tasks = set()  # Track completed tasks
        
        # Separate storage for Task 1 and Task 2 answers
        self.task_answers = {
            0: "",  # Task 1 answer
            1: ""   # Task 2 answer
        }
        
        # Set application-wide style to match IELTS CBT
        self.apply_ielts_style()
        self.initUI()

    def apply_ielts_style(self):
        # Set clean, minimalist style similar to official IELTS software
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f8f8;
                font-family: Arial;
                font-size: 12px;
            }
            QPushButton {
                background-color: #e6e6e6;
                border: 1px solid #c8c8c8;
                padding: 6px 12px;
                border-radius: 3px;
                min-height: 24px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #d8d8d8;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #45a049;
            }
            QLabel {
                color: #333333;
                background-color: #f0f0f0;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #c8c8c8;
                padding: 4px 8px;
                border-radius: 3px;
                min-height: 20px;
            }
            QComboBox:hover {
                border: 1px solid #a0a0a0;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)

    def load_subjects(self, cambridge_book=None):
        if cambridge_book is None:
            cambridge_book = getattr(self, 'selected_book', None)
        
        if not cambridge_book or cambridge_book == "No books found":
            # Return default structure
            return {
                "task1_subjects": [f"Test {i}" for i in range(1, 5)],
                "task2_subjects": [f"Test {i}" for i in range(1, 5)]
            }
        
        task1_subjects = []
        task2_subjects = []
        
        try:
            # Get available writing tests from resource manager
            available_tests = self.resource_manager.get_available_test_files(cambridge_book, 'writing')
            
            for test_file in available_tests:
                # Extract test number and task from filename
                # Expected format: Test-X-Task-Y.html
                parts = test_file.replace('.html', '').split('-')
                if len(parts) >= 4 and parts[0] == 'Test' and parts[2] == 'Task':
                    test_num = parts[1]
                    task_num = parts[3]
                    
                    if task_num == '1':
                        task1_subjects.append(f"Test {test_num}")
                    elif task_num == '2':
                        task2_subjects.append(f"Test {test_num}")
            
            # Remove duplicates and sort
            task1_subjects = sorted(list(set(task1_subjects)), key=lambda x: int(x.split()[-1]))
            task2_subjects = sorted(list(set(task2_subjects)), key=lambda x: int(x.split()[-1]))
            
            # If no files found, provide defaults
            if not task1_subjects:
                task1_subjects = [f"Test {i}" for i in range(1, 5)]
            if not task2_subjects:
                task2_subjects = [f"Test {i}" for i in range(1, 5)]
                
            return {
                "task1_subjects": task1_subjects,
                "task2_subjects": task2_subjects
            }
            
        except Exception as e:
            app_logger.error("Error loading writing subjects", exc_info=True)
            # Return default structure
            return {
                "task1_subjects": [f"Test {i}" for i in range(1, 5)],
                "task2_subjects": [f"Test {i}" for i in range(1, 5)]
            }

    def load_task_content(self, test_name, task_num):
        """Load task content from html file (fixed selection)"""
        # Extract test number from test name (e.g., "Test 1" -> "1")
        test_num = test_name.split()[-1] if test_name else "1"
        cambridge_book = self.selected_book
        
        if not cambridge_book or cambridge_book == "No books found":
            return self.get_default_content(task_num)
        
        # Construct filename
        filename = f"Test-{test_num}-Task-{task_num}.html"
        
        try:
            # Get file path from resource manager
            file_path = self.resource_manager.get_resource_path(cambridge_book, 'writing', filename)
            
            if file_path:
                full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_path)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return content.strip()
                else:
                    app_logger.warning(f"Writing content file not found: {full_path}")
            
            return self.get_default_content(task_num)
                
        except Exception as e:
            app_logger.error("Error loading writing content", exc_info=True)
            return self.get_default_content(task_num)

    def get_default_content(self, task_num):
        """Return default content if file not found"""
        if task_num == 1:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
                    .task-header { background-color: #3498db; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                    .task-title { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
                    .task-info { font-size: 14px; opacity: 0.9; }
                </style>
            </head>
            <body>
                <div class="task-header">
                    <div class="task-title">IELTS Academic Writing Task 1</div>
                    <div class="task-info">Time: 20 minutes | Minimum words: 150</div>
                </div>
                <p>Task content will be loaded here...</p>
            </body>
            </html>
            """
        else:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
                    .task-header { background-color: #e74c3c; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                    .task-title { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
                    .task-info { font-size: 14px; opacity: 0.9; }
                </style>
            </head>
            <body>
                <div class="task-header">
                    <div class="task-title">IELTS Academic Writing Task 2</div>
                    <div class="task-info">Time: 40 minutes | Minimum words: 250</div>
                </div>
                <p>Task content will be loaded here...</p>
            </body>
            </html>
            """

    def initUI(self):
        """Initialize the user interface with comprehensive error handling."""
        app_logger.info("Initializing Writing Test UI")
        
        try:
            # Create main layout with no margins for full-width display
            try:
                main_layout = QVBoxLayout()
                main_layout.setContentsMargins(0, 0, 0, 0)
                main_layout.setSpacing(0)
                app_logger.debug("Main layout created successfully")
            except Exception as e:
                app_logger.error(f"Failed to create main layout: {e}", exc_info=True)
                QMessageBox.critical(self, "Layout Error", 
                                   f"Failed to create main layout: {e}")
                # Create minimal fallback layout
                main_layout = QVBoxLayout()
                app_logger.debug("Created fallback main layout")

            # --- Unified Top Bar ---
            try:
                top_bar = QWidget()
                top_bar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #d0d0d0;")
                top_bar.setFixedHeight(50)
                top_bar_layout = QHBoxLayout(top_bar)
                top_bar_layout.setContentsMargins(15, 5, 15, 5)
                app_logger.debug("Top bar created successfully")
            except Exception as e:
                app_logger.error(f"Failed to create top bar: {e}", exc_info=True)
                QMessageBox.warning(self, "Top Bar Error", 
                                  f"Failed to create top bar: {e}")
                # Create minimal fallback top bar
                try:
                    top_bar = QWidget()
                    top_bar_layout = QHBoxLayout(top_bar)
                    app_logger.debug("Created fallback top bar")
                except Exception as fallback_error:
                    app_logger.error(f"Fallback top bar creation failed: {fallback_error}", exc_info=True)
                    top_bar = None

            # Left section: Cambridge book and test selection
            try:
                left_section = QWidget()
                left_layout = QHBoxLayout(left_section)
                left_layout.setContentsMargins(0, 0, 0, 0)
                left_layout.setSpacing(10)

                # Cambridge book selection
                try:
                    book_label = QLabel("IELTS Academic Writing Test")
                    book_label.setStyleSheet("font-weight: bold; font-size: 13px; background-color: #f0f0f0;")
                    app_logger.debug("Book label created successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to create book label: {e}", exc_info=True)
                    book_label = QLabel("Writing Test")  # Fallback
                
                # Fixed selection display (no in-app switching)
                try:
                    book_value_label = QLabel(self.selected_book or "No book selected")
                    book_value_label.setStyleSheet("font-size: 12px; background-color: #f0f0f0;")
                    app_logger.debug("Book value label created successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to create book value label: {e}", exc_info=True)
                    book_value_label = QLabel("Unknown")  # Fallback
                
                try:
                    left_layout.addWidget(book_label)
                    left_layout.addWidget(book_value_label)
                except Exception as e:
                    app_logger.warning(f"Failed to add book labels to layout: {e}", exc_info=True)
                
                # Fixed test display
                try:
                    test_value_label = QLabel(f"Test: {self.selected_test if self.selected_test is not None else '-'}")
                    test_value_label.setStyleSheet("font-weight: bold; font-size: 12px; background-color: #f0f0f0;")
                    left_layout.addWidget(test_value_label)
                    app_logger.debug("Test value label created and added successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to create test value label: {e}", exc_info=True)
                
                app_logger.debug("Left section created successfully")
            except Exception as e:
                app_logger.error(f"Failed to create left section: {e}", exc_info=True)
                # Create minimal fallback left section
                try:
                    left_section = QWidget()
                    app_logger.debug("Created fallback left section")
                except Exception as fallback_error:
                    app_logger.error(f"Fallback left section creation failed: {fallback_error}", exc_info=True)
                    left_section = None

            # Center section: Task navigation tabs
            try:
                center_section = QWidget()
                center_layout = QHBoxLayout(center_section)
                center_layout.setContentsMargins(0, 0, 0, 0)
                center_layout.setSpacing(2)
                
                try:
                    self.task1_tab = QPushButton("Task 1")
                    self.task2_tab = QPushButton("Task 2")
                    app_logger.debug("Task tab buttons created successfully")
                except Exception as e:
                    app_logger.error(f"Failed to create task tab buttons: {e}", exc_info=True)
                    # Create fallback buttons
                    self.task1_tab = QPushButton("T1")
                    self.task2_tab = QPushButton("T2")
                
                try:
                    for btn in [self.task1_tab, self.task2_tab]:
                        btn.setCheckable(True)
                        btn.setMinimumWidth(80)
                        btn.setStyleSheet("""
                            QPushButton {
                                background-color: #e0e0e0;
                                border: 1px solid #c0c0c0;
                                padding: 8px 16px;
                                font-size: 12px;
                                font-weight: bold;
                            }
                            QPushButton:checked {
                                background-color: #4CAF50;
                                color: white;
                                border: 1px solid #45a049;
                            }
                            QPushButton:hover {
                                background-color: #d0d0d0;
                            }
                            QPushButton:checked:hover {
                                background-color: #45a049;
                            }
                        """)
                        center_layout.addWidget(btn)
                    app_logger.debug("Task tab buttons configured and added successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to configure task tab buttons: {e}", exc_info=True)
                
                try:
                    self.task1_tab.setChecked(True)
                    self.task1_tab.clicked.connect(lambda: self.switch_task(0))
                    self.task2_tab.clicked.connect(lambda: self.switch_task(1))
                    app_logger.debug("Task tab button connections established successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to connect task tab buttons: {e}", exc_info=True)
                
                app_logger.debug("Center section created successfully")
            except Exception as e:
                app_logger.error(f"Failed to create center section: {e}", exc_info=True)
                # Create minimal fallback center section
                try:
                    center_section = QWidget()
                    self.task1_tab = QPushButton("Task 1")
                    self.task2_tab = QPushButton("Task 2")
                    app_logger.debug("Created fallback center section")
                except Exception as fallback_error:
                    app_logger.error(f"Fallback center section creation failed: {fallback_error}", exc_info=True)
                    center_section = None

            # Right section: Timer, completion counter, and controls
            try:
                right_section = QWidget()
                right_layout = QHBoxLayout(right_section)
                right_layout.setContentsMargins(0, 0, 0, 0)
                right_layout.setSpacing(15)

                # Completion counter
                try:
                    self.completion_label = QLabel("Completed: 0/2")
                    self.completion_label.setStyleSheet("font-size: 12px; font-weight: bold; background-color: #f0f0f0;")
                    app_logger.debug("Completion label created successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to create completion label: {e}", exc_info=True)
                    self.completion_label = QLabel("0/2")  # Fallback
                
                # Timer display
                try:
                    self.timer_label = QLabel("60:00")
                    self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; background-color: #f0f0f0;")
                    app_logger.debug("Timer label created successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to create timer label: {e}", exc_info=True)
                    self.timer_label = QLabel("60:00")  # Fallback
                
                # Start/End test button
                try:
                    self.start_test_button = QPushButton("Start Test")
                    self.start_test_button.clicked.connect(self.toggle_test)
                    self.start_test_button.setMinimumWidth(90)
                    self.start_test_button.setStyleSheet("""
                        QPushButton {
                            background-color: #4CAF50;
                            color: white;
                            font-weight: bold;
                            font-size: 12px;
                            padding: 8px 16px;
                        }
                        QPushButton:hover {
                            background-color: #45a049;
                        }
                    """)
                    app_logger.debug("Start test button created successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to create start test button: {e}", exc_info=True)
                    self.start_test_button = QPushButton("Start")  # Fallback

                try:
                    right_layout.addWidget(self.completion_label)
                    right_layout.addWidget(self.timer_label)
                    right_layout.addWidget(self.start_test_button)
                    app_logger.debug("Right section widgets added successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to add widgets to right section: {e}", exc_info=True)
                
                app_logger.debug("Right section created successfully")
            except Exception as e:
                app_logger.error(f"Failed to create right section: {e}", exc_info=True)
                # Create minimal fallback right section
                try:
                    right_section = QWidget()
                    self.completion_label = QLabel("0/2")
                    self.timer_label = QLabel("60:00")
                    self.start_test_button = QPushButton("Start")
                    app_logger.debug("Created fallback right section")
                except Exception as fallback_error:
                    app_logger.error(f"Fallback right section creation failed: {fallback_error}", exc_info=True)
                    right_section = None

            # Add sections to top bar
            try:
                if top_bar and hasattr(self, 'top_bar_layout') or 'top_bar_layout' in locals():
                    if left_section:
                        top_bar_layout.addWidget(left_section)
                    top_bar_layout.addStretch()
                    if center_section:
                        top_bar_layout.addWidget(center_section)
                    top_bar_layout.addStretch()
                    if right_section:
                        top_bar_layout.addWidget(right_section)
                    app_logger.debug("Sections added to top bar successfully")
                else:
                    app_logger.warning("Top bar layout not available, skipping section addition")
            except Exception as e:
                app_logger.warning(f"Failed to add sections to top bar: {e}", exc_info=True)
            
            # Add top bar to main layout
            try:
                if top_bar:
                    main_layout.addWidget(top_bar)
                    app_logger.debug("Top bar added to main layout successfully")
                else:
                    app_logger.warning("Top bar not available, skipping addition to main layout")
            except Exception as e:
                app_logger.warning(f"Failed to add top bar to main layout: {e}", exc_info=True)

            # --- Main Content Area with Protection Overlay ---
            try:
                self.content_stack = QStackedWidget()
                app_logger.debug("Content stack created successfully")
                
                # Create protection overlay
                try:
                    self.protection_overlay = self.create_protection_overlay()
                    app_logger.debug("Protection overlay created successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to create protection overlay: {e}", exc_info=True)
                    # Create minimal fallback overlay
                    self.protection_overlay = QWidget()
                
                # Create main test content widget
                try:
                    self.test_content_widget = QWidget()
                    test_content_layout = QVBoxLayout(self.test_content_widget)
                    test_content_layout.setContentsMargins(0, 0, 0, 0)
                    test_content_layout.setSpacing(0)
                    app_logger.debug("Test content widget created successfully")
                except Exception as e:
                    app_logger.error(f"Failed to create test content widget: {e}", exc_info=True)
                    self.test_content_widget = QWidget()  # Fallback
                
                # Content area with QWebEngineView for full-width HTML display
                try:
                    content_area = QWidget()
                    content_layout = QHBoxLayout(content_area)
                    content_layout.setContentsMargins(0, 0, 0, 0)
                    content_layout.setSpacing(0)
                    
                    # Left side: Task content (QWebEngineView) - 50% width
                    try:
                        self.web_view = QWebEngineView()
                        self.web_view.setStyleSheet("border: none;")
                        app_logger.debug("Web view created successfully")
                    except Exception as e:
                        app_logger.warning(f"Failed to create web view: {e}", exc_info=True)
                        # Create fallback label instead of web view
                        self.web_view = QLabel("Task content will appear here")
                        self.web_view.setAlignment(Qt.AlignCenter)
                    
                    # Right side: Answer area - 50% width
                    try:
                        answer_area = QWidget()
                        answer_area.setStyleSheet("background-color: white; border-left: 1px solid #d0d0d0;")
                        answer_layout = QVBoxLayout(answer_area)
                        answer_layout.setContentsMargins(15, 15, 15, 15)
                        answer_layout.setSpacing(10)
                        
                        # Answer text area
                        try:
                            answer_label = QLabel("Your answer:")
                            answer_label.setStyleSheet("""
                                font-family: 'Segoe UI', 'Arial', sans-serif;
                                font-weight: bold; 
                                font-size: 16px; 
                                color: #2c3e50;
                                background-color: white;
                                margin-bottom: 5px;
                            """)
                            app_logger.debug("Answer label created successfully")
                        except Exception as e:
                            app_logger.warning(f"Failed to create answer label: {e}", exc_info=True)
                            answer_label = QLabel("Your answer:")  # Fallback
                        
                        try:
                            self.answer_text = QTextEdit()
                            self.answer_text.setStyleSheet("""
                                QTextEdit {
                                    background-color: white;
                                    border: 1px solid #c0c0c0;
                                    font-family: 'Segoe UI', 'Arial', sans-serif;
                                    font-size: 18px;
                                    line-height: 1.6;
                                    padding: 12px;
                                    color: #333333;
                                }
                                QTextEdit:focus {
                                    border: 2px solid #4CAF50;
                                    outline: none;
                                }
                            """)
                            self.answer_text.textChanged.connect(self.update_word_count)
                            self.answer_text.textChanged.connect(self.save_current_answer)
                            app_logger.debug("Answer text area created successfully")
                        except Exception as e:
                            app_logger.error(f"Failed to create answer text area: {e}", exc_info=True)
                            self.answer_text = QTextEdit()  # Fallback
                        
                        # Word count display
                        try:
                            self.word_count_label = QLabel("Words: 0")
                            self.word_count_label.setStyleSheet("""
                                font-family: 'Segoe UI', 'Arial', sans-serif;
                                font-size: 15px;
                                font-weight: 500;
                                padding: 8px 12px;
                                background-color: #f8f9fa;
                                border: 1px solid #dee2e6;
                                border-radius: 4px;
                            """)
                            app_logger.debug("Word count label created successfully")
                        except Exception as e:
                            app_logger.warning(f"Failed to create word count label: {e}", exc_info=True)
                            self.word_count_label = QLabel("Words: 0")  # Fallback
                        
                        try:
                            answer_layout.addWidget(answer_label)
                            answer_layout.addWidget(self.answer_text)
                            answer_layout.addWidget(self.word_count_label)
                            app_logger.debug("Answer area widgets added successfully")
                        except Exception as e:
                            app_logger.warning(f"Failed to add widgets to answer area: {e}", exc_info=True)
                        
                        app_logger.debug("Answer area created successfully")
                    except Exception as e:
                        app_logger.error(f"Failed to create answer area: {e}", exc_info=True)
                        # Create minimal fallback answer area
                        answer_area = QWidget()
                        self.answer_text = QTextEdit()
                        self.word_count_label = QLabel("Words: 0")
                    
                    # Add to content layout with equal widths
                    try:
                        content_layout.addWidget(self.web_view, 1)
                        content_layout.addWidget(answer_area, 1)
                        app_logger.debug("Content layout widgets added successfully")
                    except Exception as e:
                        app_logger.warning(f"Failed to add widgets to content layout: {e}", exc_info=True)
                    
                    try:
                        test_content_layout.addWidget(content_area)
                        app_logger.debug("Content area added to test content layout successfully")
                    except Exception as e:
                        app_logger.warning(f"Failed to add content area to test content layout: {e}", exc_info=True)
                    
                    app_logger.debug("Content area created successfully")
                except Exception as e:
                    app_logger.error(f"Failed to create content area: {e}", exc_info=True)
                
                # Add widgets to content stack
                try:
                    self.content_stack.addWidget(self.protection_overlay)
                    self.content_stack.addWidget(self.test_content_widget)
                    
                    # Start with protection overlay visible
                    self.content_stack.setCurrentWidget(self.protection_overlay)
                    app_logger.debug("Content stack widgets added and configured successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to configure content stack: {e}", exc_info=True)
                
                try:
                    main_layout.addWidget(self.content_stack)
                    app_logger.debug("Content stack added to main layout successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to add content stack to main layout: {e}", exc_info=True)
                
                app_logger.debug("Main content area created successfully")
            except Exception as e:
                app_logger.error(f"Failed to create main content area: {e}", exc_info=True)
                QMessageBox.warning(self, "Content Area Error", 
                                  f"Failed to create content area: {e}")
                # Create minimal fallback content
                try:
                    self.content_stack = QStackedWidget()
                    self.protection_overlay = QWidget()
                    self.test_content_widget = QWidget()
                    self.answer_text = QTextEdit()
                    self.word_count_label = QLabel("Words: 0")
                    main_layout.addWidget(self.content_stack)
                    app_logger.debug("Created fallback content area")
                except Exception as fallback_error:
                    app_logger.error(f"Fallback content area creation failed: {fallback_error}", exc_info=True)

            # --- Navigation Buttons (Bottom-right corner) ---
            try:
                nav_widget = QWidget()
                nav_widget.setFixedHeight(60)
                nav_widget.setStyleSheet("background-color: #f8f8f8; border-top: 1px solid #d0d0d0;")
                nav_layout = QHBoxLayout(nav_widget)
                nav_layout.setContentsMargins(15, 10, 15, 10)
                
                # Left side: Status info
                try:
                    status_label = QLabel("Use the tabs above to switch between tasks")
                    status_label.setStyleSheet("color: #666; font-style: italic; background-color: #f8f8f8;")
                    app_logger.debug("Status label created successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to create status label: {e}", exc_info=True)
                    status_label = QLabel("Status")  # Fallback
                
                # Right side: Navigation buttons
                try:
                    nav_buttons = QWidget()
                    nav_buttons_layout = QHBoxLayout(nav_buttons)
                    nav_buttons_layout.setContentsMargins(0, 0, 0, 0)
                    nav_buttons_layout.setSpacing(10)
                    
                    try:
                        self.back_button = QPushButton("← Back")
                        self.back_button.clicked.connect(self.go_back)
                        self.back_button.setEnabled(False)  # Disabled initially
                        app_logger.debug("Back button created successfully")
                    except Exception as e:
                        app_logger.warning(f"Failed to create back button: {e}", exc_info=True)
                        self.back_button = QPushButton("Back")  # Fallback
                    
                    try:
                        self.next_button = QPushButton("Next →")
                        self.next_button.clicked.connect(self.go_next)
                        app_logger.debug("Next button created successfully")
                    except Exception as e:
                        app_logger.warning(f"Failed to create next button: {e}", exc_info=True)
                        self.next_button = QPushButton("Next")  # Fallback
                    
                    try:
                        for btn in [self.back_button, self.next_button]:
                            btn.setMinimumWidth(80)
                            btn.setStyleSheet("""
                                QPushButton {
                                    background-color: #2196F3;
                                    color: white;
                                    font-weight: bold;
                                    padding: 8px 16px;
                                }
                                QPushButton:hover {
                                    background-color: #1976D2;
                                }
                                QPushButton:disabled {
                                    background-color: #cccccc;
                                    color: #666666;
                                }
                            """)
                        app_logger.debug("Navigation button styles applied successfully")
                    except Exception as e:
                        app_logger.warning(f"Failed to apply navigation button styles: {e}", exc_info=True)
                    
                    try:
                        nav_buttons_layout.addWidget(self.back_button)
                        nav_buttons_layout.addWidget(self.next_button)
                        app_logger.debug("Navigation buttons added to layout successfully")
                    except Exception as e:
                        app_logger.warning(f"Failed to add navigation buttons to layout: {e}", exc_info=True)
                    
                    app_logger.debug("Navigation buttons widget created successfully")
                except Exception as e:
                    app_logger.error(f"Failed to create navigation buttons widget: {e}", exc_info=True)
                    # Create minimal fallback navigation buttons
                    nav_buttons = QWidget()
                    self.back_button = QPushButton("Back")
                    self.next_button = QPushButton("Next")
                
                try:
                    nav_layout.addWidget(status_label)
                    nav_layout.addStretch()
                    nav_layout.addWidget(nav_buttons)
                    app_logger.debug("Navigation layout configured successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to configure navigation layout: {e}", exc_info=True)
                
                try:
                    main_layout.addWidget(nav_widget)
                    app_logger.debug("Navigation widget added to main layout successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to add navigation widget to main layout: {e}", exc_info=True)
                
                app_logger.debug("Navigation section created successfully")
            except Exception as e:
                app_logger.error(f"Failed to create navigation section: {e}", exc_info=True)
                QMessageBox.warning(self, "Navigation Error", 
                                  f"Failed to create navigation section: {e}")
                # Create minimal fallback navigation
                try:
                    self.back_button = QPushButton("Back")
                    self.next_button = QPushButton("Next")
                    app_logger.debug("Created fallback navigation buttons")
                except Exception as fallback_error:
                    app_logger.error(f"Fallback navigation creation failed: {fallback_error}", exc_info=True)
            
            # Set the main layout
            try:
                self.setLayout(main_layout)
                app_logger.debug("Main layout set successfully")
            except Exception as e:
                app_logger.error(f"Failed to set main layout: {e}", exc_info=True)
                QMessageBox.critical(self, "Layout Error", 
                                   f"Failed to set main layout: {e}")
        
            # Initialize task subjects and content
            try:
                self.update_task_options()
                app_logger.debug("Task options updated successfully")
            except Exception as e:
                app_logger.warning(f"Failed to update task options: {e}", exc_info=True)
            
            try:
                self.switch_task(0)  # Start with Task 1
                app_logger.debug("Switched to first task successfully")
            except Exception as e:
                app_logger.warning(f"Failed to switch to first task: {e}", exc_info=True)
            
            app_logger.info("initUI method completed successfully")
        
        except Exception as e:
            app_logger.error(f"Critical error in initUI: {e}", exc_info=True)
            QMessageBox.critical(self, "Initialization Error", 
                               f"Critical error during UI initialization: {e}\n\n"
                               "The application may not function correctly.")
            # Attempt emergency cleanup
            try:
                # Ensure essential attributes exist
                if not hasattr(self, 'answer_text'):
                    self.answer_text = QTextEdit()
                if not hasattr(self, 'word_count_label'):
                    self.word_count_label = QLabel("Words: 0")
                if not hasattr(self, 'back_button'):
                    self.back_button = QPushButton("Back")
                if not hasattr(self, 'next_button'):
                    self.next_button = QPushButton("Next")
                if not hasattr(self, 'status_label'):
                    self.status_label = QLabel("")
                if not hasattr(self, 'completion_label'):
                    self.completion_label = QLabel("Completion: 0%")
                if not hasattr(self, 'timer_label'):
                    self.timer_label = QLabel("60:00")
                if not hasattr(self, 'start_test_button'):
                    self.start_test_button = QPushButton("Start Test")
                app_logger.debug("Emergency cleanup completed")
            except Exception as cleanup_error:
                app_logger.error(f"Emergency cleanup failed: {cleanup_error}", exc_info=True)

    def create_protection_overlay(self):
        """Create protection overlay shown before test starts"""
        overlay = QWidget()
        overlay.setStyleSheet("background-color: #f8f8f8;")
        
        layout = QVBoxLayout(overlay)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Main guidance card
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 30px;
            }
        """)
        card.setMaximumWidth(650)
        card.setMinimumHeight(600)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        
        # Title
        title = QLabel("IELTS Academic Writing Test")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c5aa0; background-color: white;")
        title.setAlignment(Qt.AlignCenter)
        
        # Test information
        info_text = """
        <div style="font-size: 14px; line-height: 1.6; color: #333;">
        <p><strong>Test Duration:</strong> 60 minutes</p>
        <p><strong>Number of Tasks:</strong> 2 writing tasks</p>
        <p><strong>Task 1:</strong> 20 minutes, minimum 150 words</p>
        <p><strong>Task 2:</strong> 40 minutes, minimum 250 words</p>
        
        <hr style="margin: 20px 0; border: 1px solid #e0e0e0;">
        
        <p><strong>Instructions:</strong></p>
        <ul>
        <li>Complete both tasks within the allocated time</li>
        <li>Task 1: Describe visual information (graph, chart, diagram)</li>
        <li>Task 2: Write an essay in response to a point of view or argument</li>
        <li>Use the task tabs to navigate between Task 1 and Task 2</li>
        <li>Monitor your word count to meet minimum requirements</li>
        <li>Review your answers before submitting</li>
        </ul>
        
        <p style="margin-top: 20px;"><strong>Good luck with your test!</strong></p>
        </div>
        """
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("background-color: white;")
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignLeft)
        
        # Start button
        start_button = QPushButton("Start Writing Test")
        start_button.clicked.connect(self.start_actual_test)
        start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        start_button.setMinimumHeight(50)
        
        card_layout.addWidget(title)
        card_layout.addWidget(info_label)
        card_layout.addSpacing(20)
        card_layout.addWidget(start_button, alignment=Qt.AlignCenter)
        
        layout.addWidget(card, alignment=Qt.AlignCenter)
        
        return overlay

    def update_task_options(self):
        """Deprecated in fixed selection mode: no dynamic task options"""
        return

    def switch_task(self, task_index):
        """Switch between Task 1 and Task 2"""
        try:
            app_logger.info(f"Switching to task {task_index}")
            
            # Validate task_index
            if not isinstance(task_index, int) or task_index not in [0, 1]:
                app_logger.error(f"Invalid task_index: {task_index}. Must be 0 or 1")
                QMessageBox.warning(self, "Task Switch Error", 
                                  f"Invalid task index: {task_index}. Must be 0 or 1.")
                return
            
            # Validate task_answers exists
            if not hasattr(self, 'task_answers'):
                app_logger.warning("task_answers not found - initializing empty dictionary")
                self.task_answers = {}
            
            try:
                # Save current answer before switching (if not the first time)
                if hasattr(self, 'answer_text') and hasattr(self, 'current_task'):
                    try:
                        current_text = self.answer_text.toPlainText()
                        self.task_answers[self.current_task] = current_text
                        app_logger.debug(f"Saved answer for task {self.current_task} ({len(current_text)} characters)")
                    except Exception as e:
                        app_logger.error(f"Failed to save current answer: {e}", exc_info=True)
                        QMessageBox.warning(self, "Save Error", 
                                          f"Failed to save current answer: {e}")
                else:
                    app_logger.debug("No current answer to save (first time or missing components)")
                
                # Update current task
                try:
                    self.current_task = task_index
                    self.current_passage = task_index
                    app_logger.debug(f"Updated current_task and current_passage to {task_index}")
                except Exception as e:
                    app_logger.error(f"Failed to update task indices: {e}", exc_info=True)
                    QMessageBox.warning(self, "Task Update Error", 
                                      f"Failed to update task indices: {e}")
                    return
                
                # Update tab states
                try:
                    if hasattr(self, 'task1_tab') and hasattr(self, 'task2_tab'):
                        self.task1_tab.setChecked(task_index == 0)
                        self.task2_tab.setChecked(task_index == 1)
                        app_logger.debug(f"Updated tab states - Task1: {task_index == 0}, Task2: {task_index == 1}")
                    else:
                        app_logger.warning("Task tabs not found - skipping tab state update")
                except Exception as e:
                    app_logger.warning(f"Failed to update tab states: {e}", exc_info=True)
                
                # Update navigation buttons
                try:
                    if hasattr(self, 'back_button') and hasattr(self, 'next_button'):
                        self.back_button.setEnabled(task_index > 0)
                        next_text = "Next →" if task_index < 1 else "End Test"
                        self.next_button.setText(next_text)
                        app_logger.debug(f"Updated navigation buttons - Back enabled: {task_index > 0}, Next text: {next_text}")
                    else:
                        app_logger.warning("Navigation buttons not found - skipping button update")
                except Exception as e:
                    app_logger.warning(f"Failed to update navigation buttons: {e}", exc_info=True)
                
                # Load content
                try:
                    if hasattr(self, 'update_task_content'):
                        self.update_task_content()
                        app_logger.debug("Task content updated successfully")
                    else:
                        app_logger.error("update_task_content method not found")
                        QMessageBox.warning(self, "Content Error", 
                                          "Cannot load task content. Method not available.")
                except Exception as e:
                    app_logger.error(f"Failed to update task content: {e}", exc_info=True)
                    QMessageBox.warning(self, "Content Error", 
                                      f"Failed to load task content: {e}")
                
                # Load the saved answer for this task
                try:
                    if hasattr(self, 'answer_text'):
                        saved_answer = self.task_answers.get(task_index, "")
                        self.answer_text.setPlainText(saved_answer)
                        app_logger.debug(f"Loaded saved answer for task {task_index} ({len(saved_answer)} characters)")
                    else:
                        app_logger.warning("answer_text not found - cannot load saved answer")
                except Exception as e:
                    app_logger.warning(f"Failed to load saved answer: {e}", exc_info=True)
                
                # Update word count
                try:
                    if hasattr(self, 'update_word_count'):
                        self.update_word_count()
                        app_logger.debug("Word count updated successfully")
                    else:
                        app_logger.warning("update_word_count method not found")
                except Exception as e:
                    app_logger.warning(f"Failed to update word count: {e}", exc_info=True)
                
                app_logger.info(f"Successfully switched to task {task_index}")
                
            except Exception as e:
                app_logger.error(f"Failed to switch task: {e}", exc_info=True)
                QMessageBox.warning(self, "Task Switch Error", 
                                  f"Failed to switch to task {task_index}: {e}")
                
        except Exception as e:
            app_logger.error(f"Critical error in switch_task: {e}", exc_info=True)
            QMessageBox.critical(self, "Critical Task Switch Error", 
                               f"Critical error switching tasks: {e}\n\n"
                               "Task switching may not function correctly.")

    def save_current_answer(self):
        """Save the current answer to the task_answers dictionary"""
        if hasattr(self, 'answer_text') and hasattr(self, 'current_task'):
            current_text = self.answer_text.toPlainText()
            self.task_answers[self.current_task] = current_text

    def on_test_selection_changed(self):
        """Deprecated in fixed selection mode: no in-app test switching"""
        return

    def update_task_content(self):
        """Update the web view with current task content (fixed selection)"""
        task_num = self.current_task + 1
        test_num = self.selected_test if self.selected_test is not None else 1
        cambridge_book = self.selected_book
        try:
            # Use resource manager to get the correct file path
            book = self.resource_manager.get_book_by_display_name(cambridge_book)
            if book:
                part_or_task = f"Task-{task_num}"
                file_path = self.resource_manager.get_resource_path(book.display_name, "writing", int(test_num), part_or_task)
                
                if file_path:
                    full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_path)
                    if os.path.exists(full_path):
                        file_url = QUrl.fromLocalFile(os.path.abspath(full_path))
                        self.web_view.load(file_url)
                        app_logger.info(f"Loaded writing content: {full_path}")
                        return
                    else:
                        app_logger.warning(f"Writing file not found: {full_path}")
                else:
                    app_logger.warning(f"Writing resource not found: Test {test_num} Task {task_num} for book {book.display_name}")
            else:
                app_logger.warning(f"Book not found: {cambridge_book}")
                
        except Exception as e:
            app_logger.error("Error loading writing content", exc_info=True)
            # Fallback to setHtml with default content
            content = self.get_default_content(task_num)
            self.web_view.setHtml(content)

    def update_word_count(self):
        """Update word count display"""
        try:
            app_logger.debug("Starting word count update")
            
            # Validate answer_text widget exists
            if not hasattr(self, 'answer_text') or self.answer_text is None:
                app_logger.error("answer_text widget not found")
                return
            
            # Get text content safely
            try:
                text = self.answer_text.toPlainText()
                if text is None:
                    text = ""
                app_logger.debug(f"Retrieved text content: {len(text)} characters")
            except Exception as e:
                app_logger.error(f"Failed to get text from answer_text widget: {e}", exc_info=True)
                text = ""
            
            # Calculate word count safely
            try:
                word_count = len(text.split()) if text and text.strip() else 0
                app_logger.debug(f"Calculated word count: {word_count}")
            except Exception as e:
                app_logger.error(f"Failed to calculate word count: {e}", exc_info=True)
                word_count = 0
            
            # Determine minimum words based on current task
            try:
                current_task = getattr(self, 'current_task', 0)
                if not isinstance(current_task, (int, float)):
                    app_logger.warning(f"Invalid current_task type: {type(current_task)}, defaulting to 0")
                    current_task = 0
                
                min_words = 150 if current_task == 0 else 250
                app_logger.debug(f"Minimum words for task {current_task}: {min_words}")
            except Exception as e:
                app_logger.error(f"Failed to determine minimum words: {e}", exc_info=True)
                min_words = 150  # Default to task 1 minimum
            
            # Prepare display styling and text
            try:
                if word_count < min_words:
                    color = "#e74c3c"  # Red
                    bg_color = "#fdf2f2"  # Light red background
                    border_color = "#f5c6cb"  # Light red border
                    words_needed = min_words - word_count
                    status = f"Words: {word_count} (need {words_needed} more)"
                else:
                    color = "#27ae60"  # Green
                    bg_color = "#f0f9f0"  # Light green background
                    border_color = "#c3e6cb"  # Light green border
                    status = f"Words: {word_count} ✓"
                
                app_logger.debug(f"Prepared status text: {status}")
            except Exception as e:
                app_logger.error(f"Failed to prepare display styling: {e}", exc_info=True)
                # Fallback styling
                color = "#333333"
                bg_color = "#ffffff"
                border_color = "#cccccc"
                status = f"Words: {word_count}"
            
            # Update word count label
            try:
                if not hasattr(self, 'word_count_label') or self.word_count_label is None:
                    app_logger.error("word_count_label not found")
                    return
                
                # Set text
                try:
                    self.word_count_label.setText(status)
                    app_logger.debug("Word count label text updated successfully")
                except Exception as e:
                    app_logger.error(f"Failed to set word count label text: {e}", exc_info=True)
                    return
                
                # Set stylesheet
                try:
                    stylesheet = f"""
                        font-family: 'Segoe UI', 'Arial', sans-serif;
                        font-size: 15px;
                        color: {color};
                        font-weight: bold;
                        padding: 8px 12px;
                        background-color: {bg_color};
                        border: 1px solid {border_color};
                        border-radius: 4px;
                    """
                    self.word_count_label.setStyleSheet(stylesheet)
                    app_logger.debug("Word count label stylesheet updated successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to set word count label stylesheet: {e}", exc_info=True)
                    # Continue without styling
                    
            except Exception as e:
                app_logger.error(f"Failed to update word count label: {e}", exc_info=True)
                return
            
            # Update completion status
            try:
                if hasattr(self, 'update_completion_counter'):
                    self.update_completion_counter()
                    app_logger.debug("Completion counter updated successfully")
                else:
                    app_logger.warning("update_completion_counter method not found")
            except Exception as e:
                app_logger.warning(f"Failed to update completion counter: {e}", exc_info=True)
            
            app_logger.debug("Word count update completed successfully")
            
        except Exception as e:
            app_logger.error(f"Critical error in update_word_count: {e}", exc_info=True)

    def update_completion_counter(self):
        """Update the completion counter in real-time"""
        try:
            app_logger.debug("Starting completion counter update")
            
            # Ensure current answer is saved
            try:
                if hasattr(self, 'save_current_answer'):
                    self.save_current_answer()
                    app_logger.debug("Current answer saved before completion check")
                else:
                    app_logger.warning("save_current_answer method not found")
            except Exception as e:
                app_logger.warning(f"Failed to save current answer: {e}", exc_info=True)
            
            # Validate task_answers exists
            if not hasattr(self, 'task_answers'):
                app_logger.warning("task_answers not found - initializing empty dictionary")
                self.task_answers = {}
            
            # Validate completed_tasks exists
            if not hasattr(self, 'completed_tasks'):
                app_logger.warning("completed_tasks not found - initializing empty set")
                self.completed_tasks = set()
            
            # Check completion status for both tasks
            try:
                self.completed_tasks.clear()
                app_logger.debug("Cleared completed_tasks set")
            except Exception as e:
                app_logger.error(f"Failed to clear completed_tasks: {e}", exc_info=True)
                self.completed_tasks = set()
            
            # Check Task 1 (150 words minimum)
            try:
                task1_text = self.task_answers.get(0, "")
                if task1_text is None:
                    task1_text = ""
                
                try:
                    task1_word_count = len(task1_text.split()) if task1_text and task1_text.strip() else 0
                except Exception as e:
                    app_logger.warning(f"Failed to calculate Task 1 word count: {e}", exc_info=True)
                    task1_word_count = 0
                
                if task1_word_count >= 150:
                    self.completed_tasks.add(0)
                    app_logger.debug(f"Task 1 completed with {task1_word_count} words")
                else:
                    app_logger.debug(f"Task 1 incomplete with {task1_word_count} words (need 150)")
                    
            except Exception as e:
                app_logger.error(f"Failed to check Task 1 completion: {e}", exc_info=True)
            
            # Check Task 2 (250 words minimum)
            try:
                task2_text = self.task_answers.get(1, "")
                if task2_text is None:
                    task2_text = ""
                
                try:
                    task2_word_count = len(task2_text.split()) if task2_text and task2_text.strip() else 0
                except Exception as e:
                    app_logger.warning(f"Failed to calculate Task 2 word count: {e}", exc_info=True)
                    task2_word_count = 0
                
                if task2_word_count >= 250:
                    self.completed_tasks.add(1)
                    app_logger.debug(f"Task 2 completed with {task2_word_count} words")
                else:
                    app_logger.debug(f"Task 2 incomplete with {task2_word_count} words (need 250)")
                    
            except Exception as e:
                app_logger.error(f"Failed to check Task 2 completion: {e}", exc_info=True)
            
            # Calculate completed count
            try:
                completed_count = len(self.completed_tasks)
                app_logger.debug(f"Total completed tasks: {completed_count}/2")
            except Exception as e:
                app_logger.error(f"Failed to calculate completed count: {e}", exc_info=True)
                completed_count = 0
            
            # Update completion label
            try:
                if not hasattr(self, 'completion_label') or self.completion_label is None:
                    app_logger.error("completion_label not found")
                    return
                
                # Set text
                try:
                    completion_text = f"Completed: {completed_count}/2"
                    self.completion_label.setText(completion_text)
                    app_logger.debug(f"Completion label text updated: {completion_text}")
                except Exception as e:
                    app_logger.error(f"Failed to set completion label text: {e}", exc_info=True)
                    return
                
                # Determine color coding
                try:
                    if completed_count == 2:
                        color = "#27ae60"  # Green
                    elif completed_count == 1:
                        color = "#f39c12"  # Orange
                    else:
                        color = "#e74c3c"  # Red
                    
                    app_logger.debug(f"Selected color for {completed_count} completed tasks: {color}")
                except Exception as e:
                    app_logger.warning(f"Failed to determine color coding: {e}", exc_info=True)
                    color = "#333333"  # Default color
                
                # Set stylesheet
                try:
                    stylesheet = f"""
                        font-size: 12px; 
                        font-weight: bold; 
                        color: {color}; 
                        background-color: #f0f0f0;
                    """
                    self.completion_label.setStyleSheet(stylesheet)
                    app_logger.debug("Completion label stylesheet updated successfully")
                except Exception as e:
                    app_logger.warning(f"Failed to set completion label stylesheet: {e}", exc_info=True)
                    # Continue without styling
                    
            except Exception as e:
                app_logger.error(f"Failed to update completion label: {e}", exc_info=True)
                return
            
            app_logger.debug("Completion counter update completed successfully")
            
        except Exception as e:
            app_logger.error(f"Critical error in update_completion_counter: {e}", exc_info=True)

    def go_back(self):
        """Navigate to previous task"""
        if self.current_task > 0:
            self.switch_task(self.current_task - 1)

    def go_next(self):
        """Navigate to next task or end test"""
        if self.current_task < 1:
            self.switch_task(self.current_task + 1)
        else:
            self.end_test()

    def end_test(self):
        """End the test"""
        reply = QMessageBox.question(self, 'End Test', 
                                   'Are you sure you want to end the test?',
                                   QMessageBox.Yes | QMessageBox.No, 
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.timer.stop()
            self.test_started = False
            self.start_test_button.setText("Start Test")
            
            # Save current answer to preserve work
            self.save_current_answer()
            
            QMessageBox.information(self, 'Test Completed', 'Your test has been completed!')



    def start_actual_test(self):
        """Start the actual test from protection overlay"""
        try:
            app_logger.info("Starting actual test from protection overlay")
            
            # Validate essential components exist
            if not hasattr(self, 'content_stack'):
                app_logger.error("Content stack not found - cannot start test")
                QMessageBox.critical(self, "Test Error", 
                                   "Test interface not properly initialized. Cannot start test.")
                return
            
            if not hasattr(self, 'test_content_widget'):
                app_logger.error("Test content widget not found - cannot start test")
                QMessageBox.critical(self, "Test Error", 
                                   "Test content not available. Cannot start test.")
                return
            
            # Reuse the same logic as the top-bar "Start Test" button
            # so the countdown timer and test state start immediately.
            try:
                self.toggle_test()
                app_logger.debug("Test toggled successfully from protection overlay")
            except Exception as e:
                app_logger.error(f"Failed to toggle test from protection overlay: {e}", exc_info=True)
                QMessageBox.warning(self, "Test Start Error", 
                                  f"Failed to start test: {e}")
                
        except Exception as e:
            app_logger.error(f"Critical error in start_actual_test: {e}", exc_info=True)
            QMessageBox.critical(self, "Critical Test Error", 
                               f"Critical error starting test: {e}\n\n"
                               "Please restart the application.")

    def toggle_test(self):
        """Start or pause the test"""
        try:
            app_logger.debug(f"Toggling test - current state: test_started={getattr(self, 'test_started', 'undefined')}")
            
            # Validate test_started attribute exists
            if not hasattr(self, 'test_started'):
                app_logger.warning("test_started attribute not found - initializing to False")
                self.test_started = False
            
            # Validate essential components for test operation
            required_attrs = ['timer', 'start_test_button', 'content_stack']
            missing_attrs = [attr for attr in required_attrs if not hasattr(self, attr)]
            
            if missing_attrs:
                app_logger.error(f"Missing essential test components: {missing_attrs}")
                QMessageBox.warning(self, "Test Error", 
                                  f"Test components not properly initialized: {', '.join(missing_attrs)}")
                return
            
            try:
                if not self.test_started:
                    app_logger.info("Starting test")
                    self.start_test()
                else:
                    app_logger.info("Pausing test")
                    self.pause_test()
                    
                app_logger.debug("Test toggle completed successfully")
            except Exception as e:
                app_logger.error(f"Failed to execute test toggle operation: {e}", exc_info=True)
                QMessageBox.warning(self, "Test Toggle Error", 
                                  f"Failed to toggle test state: {e}")
                
        except Exception as e:
            app_logger.error(f"Critical error in toggle_test: {e}", exc_info=True)
            QMessageBox.critical(self, "Critical Toggle Error", 
                               f"Critical error toggling test: {e}\n\n"
                               "Test state may be inconsistent.")

    def start_test(self):
        """Start the test"""
        try:
            app_logger.info("Starting test - initializing timer and UI state")
            
            # Validate timer exists and is properly configured
            if not hasattr(self, 'timer'):
                app_logger.error("Timer not found - cannot start test")
                QMessageBox.critical(self, "Timer Error", 
                                   "Timer not properly initialized. Cannot start test.")
                return
            
            # Validate time_remaining is set
            if not hasattr(self, 'time_remaining') or self.time_remaining <= 0:
                app_logger.warning("time_remaining not set or invalid - using default 60 minutes")
                self.time_remaining = 3600  # Default 60 minutes
            
            try:
                # Set test state
                self.test_started = True
                app_logger.debug("Test state set to started")
                
                # Start timer
                try:
                    self.timer.start(1000)  # Update every second
                    app_logger.debug("Timer started successfully")
                except Exception as e:
                    app_logger.error(f"Failed to start timer: {e}", exc_info=True)
                    QMessageBox.warning(self, "Timer Error", 
                                      f"Failed to start timer: {e}")
                    self.test_started = False  # Reset state on failure
                    return
                
                # Update start test button
                try:
                    if hasattr(self, 'start_test_button'):
                        self.start_test_button.setText("End Test")
                        self.start_test_button.setStyleSheet("""
                            QPushButton {
                                background-color: #e74c3c;
                                color: white;
                                font-weight: bold;
                                font-size: 12px;
                                padding: 8px 16px;
                            }
                            QPushButton:hover {
                                background-color: #c0392b;
                            }
                        """)
                        app_logger.debug("Start test button updated successfully")
                    else:
                        app_logger.warning("start_test_button not found - skipping button update")
                except Exception as e:
                    app_logger.warning(f"Failed to update start test button: {e}", exc_info=True)
                
                # Switch to test content
                try:
                    if hasattr(self, 'content_stack') and hasattr(self, 'test_content_widget'):
                        self.content_stack.setCurrentWidget(self.test_content_widget)
                        app_logger.debug("Switched to test content successfully")
                    else:
                        app_logger.warning("Content stack or test content widget not found - cannot switch view")
                        QMessageBox.warning(self, "Display Error", 
                                          "Cannot switch to test view. Interface may not display correctly.")
                except Exception as e:
                    app_logger.warning(f"Failed to switch to test content: {e}", exc_info=True)
                    QMessageBox.warning(self, "Display Error", 
                                      f"Failed to switch to test view: {e}")
                
                app_logger.info("Test started successfully")
                
            except Exception as e:
                app_logger.error(f"Failed to start test: {e}", exc_info=True)
                # Reset state on failure
                self.test_started = False
                if hasattr(self, 'timer'):
                    try:
                        self.timer.stop()
                    except:
                        pass
                QMessageBox.warning(self, "Test Start Error", 
                                  f"Failed to start test: {e}")
                
        except Exception as e:
            app_logger.error(f"Critical error in start_test: {e}", exc_info=True)
            QMessageBox.critical(self, "Critical Start Error", 
                               f"Critical error starting test: {e}\n\n"
                               "Test may not function correctly.")

    def pause_test(self):
        """Pause the test"""
        try:
            app_logger.info("Pausing test - calling end_test")
            
            # Validate that end_test method exists
            if not hasattr(self, 'end_test'):
                app_logger.error("end_test method not found - cannot pause test")
                QMessageBox.critical(self, "Method Error", 
                                   "end_test method not available. Cannot pause test.")
                return
            
            try:
                self.end_test()
                app_logger.debug("Test paused successfully via end_test")
            except Exception as e:
                app_logger.error(f"Failed to pause test via end_test: {e}", exc_info=True)
                QMessageBox.warning(self, "Pause Error", 
                                  f"Failed to pause test: {e}")
                
        except Exception as e:
            app_logger.error(f"Critical error in pause_test: {e}", exc_info=True)
            QMessageBox.critical(self, "Critical Pause Error", 
                               f"Critical error pausing test: {e}")

    def update_timer_display(self):
        """Update the timer display"""
        try:
            app_logger.debug("Updating timer display")
            
            # Validate time_remaining attribute exists
            if not hasattr(self, 'time_remaining'):
                app_logger.error("time_remaining attribute not found - cannot update timer")
                return
            
            # Validate timer_label exists
            if not hasattr(self, 'timer_label'):
                app_logger.error("timer_label not found - cannot update timer display")
                return
            
            try:
                if self.time_remaining > 0:
                    # Decrement time
                    self.time_remaining -= 1
                    
                    # Calculate minutes and seconds
                    try:
                        minutes = self.time_remaining // 60
                        seconds = self.time_remaining % 60
                        time_text = f"{minutes:02d}:{seconds:02d}"
                        app_logger.debug(f"Timer updated: {time_text}")
                    except Exception as e:
                        app_logger.error(f"Failed to calculate time display: {e}", exc_info=True)
                        time_text = "00:00"
                    
                    # Update timer label text
                    try:
                        self.timer_label.setText(time_text)
                    except Exception as e:
                        app_logger.error(f"Failed to update timer label text: {e}", exc_info=True)
                    
                    # Update timer label style based on remaining time
                    try:
                        if self.time_remaining <= 300:  # Last 5 minutes
                            style = "font-size: 16px; font-weight: bold; color: #e74c3c; background-color: #f0f0f0;"
                            app_logger.debug("Timer in critical zone (last 5 minutes)")
                        elif self.time_remaining <= 600:  # Last 10 minutes
                            style = "font-size: 16px; font-weight: bold; color: #f39c12; background-color: #f0f0f0;"
                            app_logger.debug("Timer in warning zone (last 10 minutes)")
                        else:
                            # Keep default style for normal time
                            style = None
                        
                        if style:
                            self.timer_label.setStyleSheet(style)
                            
                    except Exception as e:
                        app_logger.warning(f"Failed to update timer label style: {e}", exc_info=True)
                        
                else:
                    # Time's up - handle test completion
                    app_logger.info("Time is up - ending test")
                    
                    try:
                        # Stop timer
                        if hasattr(self, 'timer'):
                            self.timer.stop()
                            app_logger.debug("Timer stopped successfully")
                        else:
                            app_logger.warning("Timer not found when trying to stop")
                        
                        # Update timer display to show 00:00
                        try:
                            self.timer_label.setText("00:00")
                            self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; background-color: #f0f0f0;")
                            app_logger.debug("Timer display updated to 00:00")
                        except Exception as e:
                            app_logger.warning(f"Failed to update timer display to 00:00: {e}", exc_info=True)
                        
                        # Show time up message
                        try:
                            QMessageBox.warning(self, 'Time Up', 'Time is up! Your test has ended.')
                            app_logger.debug("Time up message displayed")
                        except Exception as e:
                            app_logger.warning(f"Failed to show time up message: {e}", exc_info=True)
                        
                        # End the test
                        try:
                            if hasattr(self, 'end_test'):
                                self.end_test()
                                app_logger.debug("Test ended successfully")
                            else:
                                app_logger.error("end_test method not found - cannot end test automatically")
                                QMessageBox.critical(self, "Test End Error", 
                                                   "Cannot end test automatically. Please save your work manually.")
                        except Exception as e:
                            app_logger.error(f"Failed to end test: {e}", exc_info=True)
                            QMessageBox.warning(self, "Test End Error", 
                                              f"Failed to end test automatically: {e}\n\n"
                                              "Please save your work manually.")
                            
                    except Exception as e:
                        app_logger.error(f"Failed to handle time completion: {e}", exc_info=True)
                        QMessageBox.critical(self, "Timer Error", 
                                           f"Error handling time completion: {e}")
                        
            except Exception as e:
                app_logger.error(f"Failed to update timer display: {e}", exc_info=True)
                # Try to show a fallback timer display
                try:
                    if hasattr(self, 'timer_label'):
                        self.timer_label.setText("--:--")
                        self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; background-color: #f0f0f0;")
                except:
                    pass
                
        except Exception as e:
            app_logger.error(f"Critical error in update_timer_display: {e}", exc_info=True)

    def show_help(self):
        """Show help dialog"""
        help_text = """
        <h3>IELTS Academic Writing Test Help</h3>
        <p><strong>Task 1 (20 minutes, 150+ words):</strong></p>
        <ul>
        <li>Describe visual information (charts, graphs, diagrams)</li>
        <li>Summarize main features and trends</li>
        <li>Make comparisons where relevant</li>
        </ul>
        
        <p><strong>Task 2 (40 minutes, 250+ words):</strong></p>
        <ul>
        <li>Write an essay responding to a point of view or argument</li>
        <li>Present a clear position</li>
        <li>Support arguments with examples</li>
        </ul>
        
        <p><strong>Navigation:</strong></p>
        <ul>
        <li>Use the Task 1/Task 2 tabs to switch between tasks</li>
        <li>Use Next/Back buttons for navigation</li>
        <li>Monitor your word count and completion status</li>
        </ul>
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("Help")
        msg.setText(help_text)
        msg.setTextFormat(Qt.RichText)
        msg.exec_()
    
    def refresh_resources(self):
        """Refresh the UI when resources change (fixed selection)."""
        try:
            # Reload subjects and content using fixed selection
            self.subjects = self.load_subjects(self.selected_book)
            self.update_task_content()
        except Exception as e:
            from logger import app_logger
            app_logger.error("Error refreshing writing test resources", exc_info=True)

    def finish_test(self):
        """Finish the test"""
        try:
            app_logger.info("Attempting to finish writing test")
            
            # Show confirmation dialog
            try:
                reply = QMessageBox.question(self, "Finish Test", 
                                           "Are you sure you want to finish the Writing test?",
                                           QMessageBox.Yes | QMessageBox.No)
                app_logger.debug(f"User confirmation for finish test: {'Yes' if reply == QMessageBox.Yes else 'No'}")
            except Exception as e:
                app_logger.error(f"Failed to show finish test confirmation dialog: {e}", exc_info=True)
                # Default to Yes if dialog fails
                reply = QMessageBox.Yes
                
            if reply == QMessageBox.Yes:
                try:
                    # Stop timer
                    try:
                        if hasattr(self, 'timer'):
                            self.timer.stop()
                            app_logger.debug("Timer stopped successfully")
                        else:
                            app_logger.warning("Timer not found when trying to stop")
                    except Exception as e:
                        app_logger.warning(f"Failed to stop timer: {e}", exc_info=True)
                    
                    # Update test state
                    try:
                        self.test_started = False
                        app_logger.debug("Test state set to not started")
                    except Exception as e:
                        app_logger.warning(f"Failed to update test state: {e}", exc_info=True)
                    
                    # Update start test button
                    try:
                        if hasattr(self, 'start_test_button'):
                            self.start_test_button.setText("Start Test")
                            self.start_test_button.setStyleSheet("""
                                QPushButton {
                                    background-color: #4CAF50;
                                    color: white;
                                    font-weight: bold;
                                    border: 1px solid #45a049;
                                    padding: 8px 16px;
                                }
                                QPushButton:hover {
                                    background-color: #45a049;
                                }
                            """)
                            app_logger.debug("Start test button updated successfully")
                        else:
                            app_logger.warning("start_test_button not found - skipping button update")
                    except Exception as e:
                        app_logger.warning(f"Failed to update start test button: {e}", exc_info=True)
                    
                    # Save answers to JSON file
                    try:
                        if hasattr(self, 'save_answers_to_json'):
                            self.save_answers_to_json()
                            app_logger.debug("Answers saved to JSON successfully")
                        else:
                            app_logger.error("save_answers_to_json method not found")
                            QMessageBox.warning(self, "Save Error", 
                                              "Cannot save answers. Save method not available.")
                    except Exception as e:
                        app_logger.error(f"Failed to save answers to JSON: {e}", exc_info=True)
                        QMessageBox.warning(self, "Save Error", 
                                          f"Failed to save test answers: {e}\n\n"
                                          "Your answers may not be saved.")
                    
                    # Show completion message
                    try:
                        QMessageBox.information(self, "Test Complete", 
                                              "Your writing test has been completed.")
                        app_logger.debug("Test completion message displayed")
                    except Exception as e:
                        app_logger.warning(f"Failed to show test completion message: {e}", exc_info=True)
                    
                    app_logger.info("Writing test finished successfully")
                    
                except Exception as e:
                    app_logger.error(f"Failed to finish test: {e}", exc_info=True)
                    QMessageBox.warning(self, "Finish Test Error", 
                                      f"Error finishing test: {e}\n\n"
                                      "Test may not be properly completed.")
            else:
                app_logger.debug("User cancelled test finish")
                
        except Exception as e:
            app_logger.error(f"Critical error in finish_test: {e}", exc_info=True)
            QMessageBox.critical(self, "Critical Finish Error", 
                               f"Critical error finishing test: {e}\n\n"
                               "Test completion may not function correctly.")

    def save_answers_to_json(self):
        """Save test answers to JSON file for grading"""
        try:
            app_logger.info("Starting to save writing test answers to JSON")
            
            # Validate required attributes
            required_attrs = ['selected_book', 'selected_test']
            for attr in required_attrs:
                if not hasattr(self, attr) or getattr(self, attr) is None:
                    app_logger.error(f"Required attribute '{attr}' not found or is None")
                    QMessageBox.warning(self, "Save Error", 
                                      f"Cannot save answers: {attr} not available.")
                    return
            
            try:
                # Create results directory if it doesn't exist
                try:
                    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results', 'writing')
                    os.makedirs(results_dir, exist_ok=True)
                    app_logger.debug(f"Results directory ensured: {results_dir}")
                except Exception as e:
                    app_logger.error(f"Failed to create results directory: {e}", exc_info=True)
                    QMessageBox.warning(self, "Directory Error", 
                                      f"Failed to create results directory: {e}")
                    return
                
                # Generate filename with timestamp
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    # Sanitize book name for filename
                    safe_book_name = str(self.selected_book).replace(' ', '_').replace('/', '_')
                    filename = f"writing_test_{safe_book_name}_test{self.selected_test}_{timestamp}.json"
                    filepath = os.path.join(results_dir, filename)
                    app_logger.debug(f"Generated filepath: {filepath}")
                except Exception as e:
                    app_logger.error(f"Failed to generate filename: {e}", exc_info=True)
                    QMessageBox.warning(self, "Filename Error", 
                                      f"Failed to generate filename: {e}")
                    return
                
                # Ensure current answer is saved
                try:
                    if hasattr(self, 'save_current_answer'):
                        self.save_current_answer()
                        app_logger.debug("Current answer saved before JSON export")
                    else:
                        app_logger.warning("save_current_answer method not found")
                except Exception as e:
                    app_logger.warning(f"Failed to save current answer: {e}", exc_info=True)
                
                # Validate task_answers exists
                if not hasattr(self, 'task_answers'):
                    app_logger.warning("task_answers not found - initializing empty dictionary")
                    self.task_answers = {}
                
                # Collect answers from task_answers dictionary
                try:
                    task1_answer = self.task_answers.get(0, "")
                    task2_answer = self.task_answers.get(1, "")
                    app_logger.debug(f"Collected answers - Task1: {len(task1_answer)} chars, Task2: {len(task2_answer)} chars")
                except Exception as e:
                    app_logger.error(f"Failed to collect answers: {e}", exc_info=True)
                    task1_answer = ""
                    task2_answer = ""
                
                # Prepare test data with validation
                try:
                    # Get time values with fallbacks
                    total_time = getattr(self, 'total_time', 3600)  # Default 60 minutes
                    time_remaining = getattr(self, 'time_remaining', 0)
                    current_task = getattr(self, 'current_task', 0)
                    completed_tasks = getattr(self, 'completed_tasks', set())
                    
                    # Calculate word counts safely
                    try:
                        task1_word_count = len(task1_answer.split()) if task1_answer and task1_answer.strip() else 0
                        task2_word_count = len(task2_answer.split()) if task2_answer and task2_answer.strip() else 0
                    except Exception as e:
                        app_logger.warning(f"Failed to calculate word counts: {e}", exc_info=True)
                        task1_word_count = 0
                        task2_word_count = 0
                    
                    test_data = {
                        "test_type": "writing",
                        "book": str(self.selected_book),
                        "test_number": int(self.selected_test),
                        "timestamp": datetime.now().isoformat(),
                        "total_time_seconds": int(total_time),
                        "time_remaining_seconds": int(time_remaining),
                        "answers": {
                            "task1": {
                                "text": str(task1_answer),
                                "word_count": task1_word_count,
                                "character_count": len(task1_answer) if task1_answer else 0
                            },
                            "task2": {
                                "text": str(task2_answer),
                                "word_count": task2_word_count,
                                "character_count": len(task2_answer) if task2_answer else 0
                            }
                        },
                        "metadata": {
                             "task1_minimum_words": 150,
                             "task2_minimum_words": 250,
                             "current_task": int(current_task),
                             "time_spent_seconds": int(total_time - time_remaining),
                             "completed_tasks": list(completed_tasks) if completed_tasks else []
                         }
                    }
                    app_logger.debug("Test data prepared successfully")
                    
                except Exception as e:
                    app_logger.error(f"Failed to prepare test data: {e}", exc_info=True)
                    QMessageBox.warning(self, "Data Error", 
                                      f"Failed to prepare test data: {e}")
                    return
                
                # Save to JSON file
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(test_data, f, indent=2, ensure_ascii=False)
                    
                    # Verify file was created and has content
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                        app_logger.info(f"Writing test answers saved successfully to: {filepath}")
                        QMessageBox.information(self, "Save Success", 
                                              f"Test answers saved successfully to:\n{filename}")
                    else:
                        app_logger.error(f"File was not created or is empty: {filepath}")
                        QMessageBox.warning(self, "Save Error", 
                                          "File was created but appears to be empty.")
                        
                except PermissionError as e:
                    app_logger.error(f"Permission denied saving to {filepath}: {e}", exc_info=True)
                    QMessageBox.warning(self, "Permission Error", 
                                      f"Permission denied saving to file:\n{e}\n\n"
                                      "Please check file permissions or try a different location.")
                except OSError as e:
                    app_logger.error(f"OS error saving to {filepath}: {e}", exc_info=True)
                    QMessageBox.warning(self, "File System Error", 
                                      f"File system error saving answers:\n{e}")
                except Exception as e:
                    app_logger.error(f"Failed to save JSON file: {e}", exc_info=True)
                    QMessageBox.warning(self, "Save Error", 
                                      f"Failed to save JSON file: {e}")
                    
            except Exception as e:
                app_logger.error(f"Failed to save answers to JSON: {e}", exc_info=True)
                QMessageBox.warning(self, "Save Error", 
                                  f"Failed to save test answers: {e}")
                
        except Exception as e:
            app_logger.error(f"Critical error in save_answers_to_json: {e}", exc_info=True)
            QMessageBox.critical(self, "Critical Save Error", 
                               f"Critical error saving answers: {e}\n\n"
                               "Your answers may not be saved.")
