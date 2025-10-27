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
            app_logger.debug(f"Error loading writing subjects: {str(e)}")
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
                    app_logger.debug(f"Writing content file not found: {full_path}")
            
            return self.get_default_content(task_num)
                
        except Exception as e:
            app_logger.debug(f"Error loading writing content: {str(e)}")
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
        # Create main layout with no margins for full-width display
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Unified Top Bar ---
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #d0d0d0;")
        top_bar.setFixedHeight(50)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(15, 5, 15, 5)

        # Left section: Cambridge book and test selection
        left_section = QWidget()
        left_layout = QHBoxLayout(left_section)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Cambridge book selection
        book_label = QLabel("Cambridge IELTS Academic Writing Test")
        book_label.setStyleSheet("font-weight: bold; font-size: 13px; background-color: #f0f0f0;")
        
        # Fixed selection display (no in-app switching)
        book_value_label = QLabel(self.selected_book or "No book selected")
        book_value_label.setStyleSheet("font-size: 12px; background-color: #f0f0f0;")
        
        left_layout.addWidget(book_label)
        left_layout.addWidget(book_value_label)
        
        # Fixed test display
        test_value_label = QLabel(f"Test: {self.selected_test if self.selected_test is not None else '-'}")
        test_value_label.setStyleSheet("font-weight: bold; font-size: 12px; background-color: #f0f0f0;")
        
        left_layout.addWidget(test_value_label)

        # Center section: Task navigation tabs
        center_section = QWidget()
        center_layout = QHBoxLayout(center_section)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(2)
        
        self.task1_tab = QPushButton("Task 1")
        self.task2_tab = QPushButton("Task 2")
        
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
        
        self.task1_tab.setChecked(True)
        self.task1_tab.clicked.connect(lambda: self.switch_task(0))
        self.task2_tab.clicked.connect(lambda: self.switch_task(1))

        # Right section: Timer, completion counter, and controls
        right_section = QWidget()
        right_layout = QHBoxLayout(right_section)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        # Completion counter
        self.completion_label = QLabel("Completed: 0/2")
        self.completion_label.setStyleSheet("font-size: 12px; font-weight: bold; background-color: #f0f0f0;")
        
        # Timer display
        self.timer_label = QLabel("60:00")
        self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; background-color: #f0f0f0;")
        
        # Start/End test button
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

        right_layout.addWidget(self.completion_label)
        right_layout.addWidget(self.timer_label)
        right_layout.addWidget(self.start_test_button)

        # Add sections to top bar
        top_bar_layout.addWidget(left_section)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(center_section)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(right_section)
        
        main_layout.addWidget(top_bar)

        # --- Main Content Area with Protection Overlay ---
        self.content_stack = QStackedWidget()
        
        # Create protection overlay
        self.protection_overlay = self.create_protection_overlay()
        
        # Create main test content widget
        self.test_content_widget = QWidget()
        test_content_layout = QVBoxLayout(self.test_content_widget)
        test_content_layout.setContentsMargins(0, 0, 0, 0)
        test_content_layout.setSpacing(0)
        
        # Content area with QWebEngineView for full-width HTML display
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Left side: Task content (QWebEngineView) - 50% width
        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("border: none;")
        
        # Right side: Answer area - 50% width
        answer_area = QWidget()
        answer_area.setStyleSheet("background-color: white; border-left: 1px solid #d0d0d0;")
        answer_layout = QVBoxLayout(answer_area)
        answer_layout.setContentsMargins(15, 15, 15, 15)
        answer_layout.setSpacing(10)
        
        # Test selection is now in the top bar
        
        # Answer text area
        answer_label = QLabel("Your answer:")
        answer_label.setStyleSheet("font-weight: bold; font-size: 13px; background-color: white;")
        
        self.answer_text = QTextEdit()
        self.answer_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #c0c0c0;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.5;
                padding: 10px;
            }
            QTextEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)
        self.answer_text.textChanged.connect(self.update_word_count)
        
        # Word count display
        self.word_count_label = QLabel("Words: 0")
        self.word_count_label.setStyleSheet("""
            font-size: 12px;
            color: #666;
            padding: 5px;
            background-color: #f8f8f8;
            border: 1px solid #e0e0e0;
            border-radius: 3px;
        """)
        
        answer_layout.addWidget(answer_label)
        answer_layout.addWidget(self.answer_text)
        answer_layout.addWidget(self.word_count_label)
        
        # Add to content layout with equal widths
        content_layout.addWidget(self.web_view, 1)
        content_layout.addWidget(answer_area, 1)
        
        test_content_layout.addWidget(content_area)
        
        # Add widgets to content stack
        self.content_stack.addWidget(self.protection_overlay)
        self.content_stack.addWidget(self.test_content_widget)
        
        # Start with protection overlay visible
        self.content_stack.setCurrentWidget(self.protection_overlay)
        
        main_layout.addWidget(self.content_stack)

        # --- Navigation Buttons (Bottom-right corner) ---
        nav_widget = QWidget()
        nav_widget.setFixedHeight(60)
        nav_widget.setStyleSheet("background-color: #f8f8f8; border-top: 1px solid #d0d0d0;")
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(15, 10, 15, 10)
        
        # Left side: Status info
        status_label = QLabel("Use the tabs above to switch between tasks")
        status_label.setStyleSheet("color: #666; font-style: italic; background-color: #f8f8f8;")
        
        # Right side: Navigation buttons
        nav_buttons = QWidget()
        nav_buttons_layout = QHBoxLayout(nav_buttons)
        nav_buttons_layout.setContentsMargins(0, 0, 0, 0)
        nav_buttons_layout.setSpacing(10)
        
        self.back_button = QPushButton("← Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)  # Disabled initially
        
        self.next_button = QPushButton("Next →")
        self.next_button.clicked.connect(self.go_next)
        
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
        
        nav_buttons_layout.addWidget(self.back_button)
        nav_buttons_layout.addWidget(self.next_button)
        
        nav_layout.addWidget(status_label)
        nav_layout.addStretch()
        nav_layout.addWidget(nav_buttons)
        
        main_layout.addWidget(nav_widget)
        
        # Set the main layout
        self.setLayout(main_layout)
        
        # Initialize task subjects and content
        self.update_task_options()
        self.switch_task(0)  # Start with Task 1

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
        self.current_task = task_index
        self.current_passage = task_index
        
        # Update tab states
        self.task1_tab.setChecked(task_index == 0)
        self.task2_tab.setChecked(task_index == 1)
        
        # Test selection is now handled at the top level
        
        # Update navigation buttons
        self.back_button.setEnabled(task_index > 0)
        self.next_button.setText("Next →" if task_index < 1 else "End Test")
        
        # Load content
        self.update_task_content()
        self.update_word_count()

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
            app_logger.error(f"Error loading writing content: {e}")
            # Fallback to setHtml with default content
            content = self.get_default_content(task_num)
            self.web_view.setHtml(content)

    def update_word_count(self):
        """Update word count display"""
        text = self.answer_text.toPlainText()
        word_count = len(text.split()) if text.strip() else 0
        
        # Determine minimum words based on current task
        min_words = 150 if self.current_task == 0 else 250
        
        # Update display with color coding
        if word_count < min_words:
            color = "#e74c3c"  # Red
            status = f"Words: {word_count} (need {min_words - word_count} more)"
        else:
            color = "#27ae60"  # Green
            status = f"Words: {word_count} ✓"
        
        self.word_count_label.setText(status)
        self.word_count_label.setStyleSheet(f"""
            font-size: 12px;
            color: {color};
            font-weight: bold;
            padding: 5px;
            background-color: #f8f8f8;
            border: 1px solid #e0e0e0;
            border-radius: 3px;
        """)
        
        # Update completion status
        self.update_completion_counter()

    def update_completion_counter(self):
        """Update the completion counter in real-time"""
        # Check if current task meets minimum word requirement
        text = self.answer_text.toPlainText()
        word_count = len(text.split()) if text.strip() else 0
        min_words = 150 if self.current_task == 0 else 250
        
        if word_count >= min_words:
            self.completed_tasks.add(self.current_task)
        else:
            self.completed_tasks.discard(self.current_task)
        
        completed_count = len(self.completed_tasks)
        self.completion_label.setText(f"Completed: {completed_count}/2")
        
        # Color coding
        if completed_count == 2:
            color = "#27ae60"  # Green
        elif completed_count == 1:
            color = "#f39c12"  # Orange
        else:
            color = "#e74c3c"  # Red
            
        self.completion_label.setStyleSheet(f"""
            font-size: 12px; 
            font-weight: bold; 
            color: {color}; 
            background-color: #f0f0f0;
        """)

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
            QMessageBox.information(self, 'Test Completed', 'Your test has been completed!')

    def start_actual_test(self):
        """Start the actual test from protection overlay"""
        # Reuse the same logic as the top-bar "Start Test" button
        # so the countdown timer and test state start immediately.
        self.toggle_test()

    def toggle_test(self):
        """Start or pause the test"""
        if not self.test_started:
            self.start_test()
        else:
            self.pause_test()

    def start_test(self):
        """Start the test"""
        self.test_started = True
        self.timer.start(1000)  # Update every second
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
        
        # Switch to test content
        self.content_stack.setCurrentWidget(self.test_content_widget)

    def pause_test(self):
        """Pause the test"""
        self.end_test()

    def update_timer_display(self):
        """Update the timer display"""
        if self.time_remaining > 0:
            self.time_remaining -= 1
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
            
            # Change color when time is running low
            if self.time_remaining <= 300:  # Last 5 minutes
                self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; background-color: #f0f0f0;")
            elif self.time_remaining <= 600:  # Last 10 minutes
                self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f39c12; background-color: #f0f0f0;")
        else:
            # Time's up
            self.timer.stop()
            self.timer_label.setText("00:00")
            self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; background-color: #f0f0f0;")
            QMessageBox.warning(self, 'Time Up', 'Time is up! Your test has ended.')
            self.end_test()

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
            app_logger.error(f"Error refreshing writing test resources: {e}")
