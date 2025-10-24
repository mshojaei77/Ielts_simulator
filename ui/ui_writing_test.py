import json
import os
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
    def __init__(self):
        super().__init__()
        self.module_type = "academic"  # Always academic now
        self.subjects = self.load_subjects()
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

    def load_subjects(self, cambridge_book="Cambridge 20"):
        # Map Cambridge book names to directory names
        book_mapping = {
            "Cambridge 20": "Cambridge20",
            "Cambridge 19": "Cambridge19"
        }
        
        book_dir = book_mapping.get(cambridge_book, "Cambridge20")
        writing_dir = f"resources/{book_dir}/writing"
        
        task1_subjects = []
        task2_subjects = []
        
        try:
            if os.path.exists(writing_dir):
                # Scan for html files in the writing directory
                for filename in os.listdir(writing_dir):
                    if filename.endswith('.html'):
                        # Extract test number and task from filename
                        # Expected format: Test-X-Task-Y.html
                        parts = filename.replace('.html', '').split('-')
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
            print(f"Error loading writing subjects: {str(e)}")
            # Return default structure
            return {
                "task1_subjects": [f"Test {i}" for i in range(1, 5)],
                "task2_subjects": [f"Test {i}" for i in range(1, 5)]
            }

    def load_task_content(self, test_name, task_num):
        """Load task content from html file"""
        # Extract test number from test name (e.g., "Test 1" -> "1")
        test_num = test_name.split()[-1] if test_name else "1"
        cambridge_book = self.book_combo.currentText()
        
        # Map Cambridge book names to directory names
        book_mapping = {
            "Cambridge 20": "Cambridge20",
            "Cambridge 19": "Cambridge19"
        }
        
        book_dir = book_mapping.get(cambridge_book, "Cambridge20")
        filename = f"resources/{book_dir}/writing/Test-{test_num}-Task-{task_num}.html"
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            return content.strip()
        except FileNotFoundError:
            print(f"Writing content file not found: {filename}")
            return self.get_default_content(task_num)
        except Exception as e:
            print(f"Error loading writing content: {str(e)}")
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
        
        self.book_combo = QComboBox()
        self.book_combo.addItems(["Cambridge 20", "Cambridge 19"])
        self.book_combo.setMinimumWidth(120)
        self.book_combo.currentTextChanged.connect(self.update_task_options)

        left_layout.addWidget(book_label)
        left_layout.addWidget(self.book_combo)

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
        
        # Test selection for current task
        selection_widget = QWidget()
        selection_layout = QHBoxLayout(selection_widget)
        selection_layout.setContentsMargins(0, 0, 0, 0)
        
        test_label = QLabel("Select test:")
        test_label.setStyleSheet("font-weight: bold; background-color: white;")
        
        self.test_combo = QComboBox()
        self.test_combo.setMinimumWidth(100)
        self.test_combo.currentIndexChanged.connect(self.update_task_content)
        
        selection_layout.addWidget(test_label)
        selection_layout.addWidget(self.test_combo)
        selection_layout.addStretch()
        
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
        
        answer_layout.addWidget(selection_widget)
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
        overlay.setStyleSheet("background-color: #f0f0f0;")
        
        layout = QVBoxLayout(overlay)
        layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title = QLabel("IELTS Academic Writing Test")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; background-color: #f0f0f0;")
        title.setAlignment(Qt.AlignCenter)
        
        # Instructions
        instructions = QLabel("""
        <div style="text-align: center; line-height: 1.6;">
        <h3>Test Instructions:</h3>
        <p>• This test consists of 2 tasks</p>
        <p>• Task 1: 20 minutes, minimum 150 words</p>
        <p>• Task 2: 40 minutes, minimum 250 words</p>
        <p>• Total time: 60 minutes</p>
        <br>
        <p><strong>Click "Start Test" to begin</strong></p>
        </div>
        """)
        instructions.setStyleSheet("font-size: 14px; color: #34495e; background-color: #f0f0f0;")
        instructions.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(instructions)
        
        return overlay

    def update_task_options(self):
        """Update task options when Cambridge book changes"""
        self.subjects = self.load_subjects(self.book_combo.currentText())
        self.update_task_content()

    def switch_task(self, task_index):
        """Switch between Task 1 and Task 2"""
        self.current_task = task_index
        self.current_passage = task_index
        
        # Update tab states
        self.task1_tab.setChecked(task_index == 0)
        self.task2_tab.setChecked(task_index == 1)
        
        # Update test combo options
        if task_index == 0:
            self.test_combo.clear()
            self.test_combo.addItems(self.subjects.get("task1_subjects", []))
        else:
            self.test_combo.clear()
            self.test_combo.addItems(self.subjects.get("task2_subjects", []))
        
        # Update navigation buttons
        self.back_button.setEnabled(task_index > 0)
        self.next_button.setText("Next →" if task_index < 1 else "End Test")
        
        # Load content
        self.update_task_content()
        self.update_word_count()

    def update_task_content(self):
        """Update the web view with current task content"""
        if self.test_combo.currentText():
            task_num = self.current_task + 1
            test_name = self.test_combo.currentText()
            
            # Extract test number from test name (e.g., "Test 1" -> "1")
            test_num = test_name.split()[-1] if test_name else "1"
            cambridge_book = self.book_combo.currentText()
            
            # Map Cambridge book names to directory names
            book_mapping = {
                "Cambridge 20": "Cambridge20",
                "Cambridge 19": "Cambridge19"
            }
            
            book_dir = book_mapping.get(cambridge_book, "Cambridge20")
            filename = f"resources/{book_dir}/writing/Test-{test_num}-Task-{task_num}.html"
            
            # Check if file exists and load it directly
            if os.path.exists(filename):
                file_url = QUrl.fromLocalFile(os.path.abspath(filename))
                self.web_view.load(file_url)
            else:
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
