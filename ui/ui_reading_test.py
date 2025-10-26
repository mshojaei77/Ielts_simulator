import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import app_logger
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QStackedWidget, 
                             QMessageBox, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QTime, QUrl, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel

class ReadingTestUI(QWidget):
    def __init__(self):
        super().__init__()
        self.module_type = "academic"  # Always academic now
        self.subjects = self.load_subjects()
        self.total_time = 60 * 60  # 60 minutes in seconds
        self.time_remaining = self.total_time
        self.current_passage = 0  # 0, 1, or 2 for the three passages
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_display)
        self.test_id = "IELTS-CBT-" + "".join([str(i) for i in range(10)])  # Test ID like official test
        self.test_started = False
        self.completed_questions = 0
        self.total_questions = 40
        # --- Added: tracker state for passages ---
        self.passage_ranges = [(1, 13), (14, 26), (27, 40)]  # Typical IELTS Reading distribution
        self.reading_answers_by_passage = {0: set(), 1: set(), 2: set()}
        self.answer_poll_timer = QTimer(self)
        self.answer_poll_timer.setInterval(200)
        self.answer_poll_timer.timeout.connect(self.update_completion_count)
        

        
        # Apply a clean, consistent style
        self.apply_ielts_style()
        self.initUI()

    def apply_ielts_style(self):
        # Set clean, minimalist style similar to official IELTS software
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 12px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #c8c8c8;
                padding: 6px 12px;
                border-radius: 3px;
                min-height: 24px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #a0a0a0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:checked {
                background-color: #ffffff;
                border: 1px solid #0066cc;
                color: #0066cc;
            }
            QLabel {
                color: #333333;
                background-color: #f0f0f0;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #c8c8c8;
                padding: 4px 8px;
                border-radius: 3px;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #0066cc;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 5px;
            }
        """)

    def load_subjects(self, cambridge_book="Cambridge 20"):
        """Load available reading tests based on txt files in the directory"""
        # Map Cambridge book names to directory names
        book_mapping = {
            "Cambridge 20": "Cambridge20",
            "Cambridge 19": "Cambridge19"
        }
        
        book_dir = book_mapping.get(cambridge_book, "Cambridge20")
        reading_dir = f"resources/{book_dir}/reading"
        
        # Check for available test files
        available_tests = []
        try:
            if os.path.exists(reading_dir):
                files = os.listdir(reading_dir)
                # Look for Test-X-Passage-Y.html files
                test_numbers = set()
                for file in files:
                    if file.startswith("Test-") and file.endswith(".html"):
                        parts = file.split("-")
                        if len(parts) >= 2:
                            test_num = parts[1]
                            test_numbers.add(test_num)
                
                # Create test list
                for test_num in sorted(test_numbers):
                    available_tests.append(f"Test {test_num}")
            
            # If no tests found, provide defaults
            if not available_tests:
                available_tests = ["Test 1", "Test 2", "Test 3", "Test 4"]
                
        except Exception as e:
            app_logger.debug(f"Error scanning reading directory: {e}")
            available_tests = ["Test 1", "Test 2", "Test 3", "Test 4"]
        
        return {"reading_subjects": available_tests}

    def initUI(self):
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Unified Top Bar ---
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #d0d0d0;")
        top_bar.setFixedHeight(50)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(15, 0, 15, 0)
        top_bar_layout.setSpacing(15)

        # Left section - Test info
        test_info_label = QLabel("Cambridge IELTS Academic Reading Test")
        test_info_label.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #f0f0f0;")
        
        # Cambridge book selection
        book_label = QLabel("Book:")
        book_label.setStyleSheet("background-color: #f0f0f0;")
        self.book_combo = QComboBox()
        self.book_combo.addItems(["Cambridge 20", "Cambridge 19"])
        self.book_combo.setMinimumWidth(120)
        self.book_combo.currentTextChanged.connect(self.update_subject_options)
        
        # Subject selection
        test_label = QLabel("Test:")
        test_label.setStyleSheet("background-color: #f0f0f0;")
        self.subject_combo = QComboBox()
        self.subject_combo.setMinimumWidth(100)
        
        # Center section - Passage tabs
        tab_widget = QWidget()
        tab_widget.setStyleSheet("background-color: #f0f0f0;")
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(2)
        
        self.passage_tabs = []
        for i in range(3):
            tab = QPushButton(f"Passage {i+1}")
            tab.setCheckable(True)
            tab.setMinimumWidth(90)
            tab.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #c0c0c0;
                    border-radius: 3px;
                    padding: 8px 12px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #ffffff;
                    border: 2px solid #0066cc;
                    color: #0066cc;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """)
            self.passage_tabs.append(tab)
            tab.clicked.connect(lambda checked, idx=i: self.switch_passage(idx))
            tab_layout.addWidget(tab)
        
        self.passage_tabs[0].setChecked(True)
        
        # Right section - Timer and controls
        self.completion_label = QLabel("Completed: 0/40")
        self.completion_label.setStyleSheet("font-size: 12px; background-color: #f0f0f0; color: #666;")
        
        self.timer_label = QLabel("60:00")
        self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #f0f0f0; color: #333; padding: 0 10px;")
        self.timer_label.setAlignment(Qt.AlignCenter)
        
        # Start/End test button
        self.start_test_button = QPushButton("Start Test")
        self.start_test_button.clicked.connect(self.toggle_test)
        self.start_test_button.setMinimumWidth(100)
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
        
        # Layout top bar
        top_bar_layout.addWidget(test_info_label)
        top_bar_layout.addWidget(book_label)
        top_bar_layout.addWidget(self.book_combo)
        top_bar_layout.addWidget(test_label)
        top_bar_layout.addWidget(self.subject_combo)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(tab_widget)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.completion_label)
        top_bar_layout.addWidget(self.timer_label)
        top_bar_layout.addWidget(self.start_test_button)
        
        main_layout.addWidget(top_bar)

        # --- Main Content Area with Protection Overlay ---
        self.content_stack = QStackedWidget()
        
        # Create protection overlay
        self.protection_overlay = self.create_protection_overlay()
        
        # Create main test content widget with QWebEngineView
        self.test_content_widget = QWidget()
        test_content_layout = QVBoxLayout(self.test_content_widget)
        test_content_layout.setContentsMargins(0, 0, 0, 0)
        test_content_layout.setSpacing(0)
        
        # Web engine view for HTML content
        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("border: none;")
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set up web channel for JavaScript communication
        self.web_channel = QWebChannel()
        self.web_view.page().setWebChannel(self.web_channel)
        # --- Added: refresh tracker after page loads ---
        self.web_view.loadFinished.connect(self.on_page_loaded)
        
        test_content_layout.addWidget(self.web_view)
        
        # Add widgets to content stack
        self.content_stack.addWidget(self.protection_overlay)
        self.content_stack.addWidget(self.test_content_widget)
        
        # Start with protection overlay visible
        self.content_stack.setCurrentWidget(self.protection_overlay)
        
        main_layout.addWidget(self.content_stack)

        # --- Question Tracker UI ---
        self.build_question_tracker(main_layout)

        # --- Bottom Navigation Bar ---
        nav_bar = QWidget()
        nav_bar.setFixedHeight(50)
        nav_bar.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #d0d0d0;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(15, 0, 15, 0)
        
        # Left side - status info
        status_label = QLabel("Use the passage tabs above to navigate between sections")
        status_label.setStyleSheet("font-style: italic; color: #666; background-color: #f0f0f0;")
        
        # Right side - navigation buttons
        nav_buttons_widget = QWidget()
        nav_buttons_widget.setStyleSheet("background-color: #f0f0f0;")
        nav_buttons_layout = QHBoxLayout(nav_buttons_widget)
        nav_buttons_layout.setContentsMargins(0, 0, 0, 0)
        nav_buttons_layout.setSpacing(10)
        
        self.back_button = QPushButton("◀ Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover:enabled {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                color: #999;
                background-color: #f5f5f5;
            }
        """)
        
        self.next_button = QPushButton("Next ▶")
        self.next_button.clicked.connect(self.go_next)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: 1px solid #0052a3;
                padding: 8px 16px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
        """)
        
        nav_buttons_layout.addWidget(self.back_button)
        nav_buttons_layout.addWidget(self.next_button)
        
        nav_layout.addWidget(status_label)
        nav_layout.addStretch()
        nav_layout.addWidget(nav_buttons_widget)
        
        main_layout.addWidget(nav_bar)
        
        # Set the main layout
        self.setLayout(main_layout)
        
        # Initialize with sample content
        self.update_subject_options()
        self.subject_combo.currentIndexChanged.connect(self.load_selected_subject)
        
        # Load first passage initially
        self.load_passage_content()

    def create_protection_overlay(self):
        """Create the protection overlay with guidance card"""
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
        card.setMaximumWidth(600)
        card.setMaximumHeight(500)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        
        # Title
        title = QLabel("IELTS Academic Reading Test")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c5aa0; background-color: white;")
        title.setAlignment(Qt.AlignCenter)
        
        # Test information
        info_text = """
        <div style="font-size: 14px; line-height: 1.6; color: #333;">
        <p><strong>Test Duration:</strong> 60 minutes</p>
        <p><strong>Number of Passages:</strong> 3 reading passages</p>
        <p><strong>Total Questions:</strong> 40 questions</p>
        <p><strong>Question Types:</strong> Multiple choice, gap-fill, matching, true/false/not given</p>
        
        <hr style="margin: 20px 0; border: 1px solid #e0e0e0;">
        
        <p><strong>Instructions:</strong></p>
        <ul>
        <li>Read each passage carefully before answering questions</li>
        <li>Use the passage tabs to navigate between sections</li>
        <li>All answers must be based on the information in the passages</li>
        <li>Manage your time effectively - approximately 20 minutes per passage</li>
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
        start_button = QPushButton("Start Reading Test")
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
        card_layout.addStretch()
        card_layout.addWidget(start_button, alignment=Qt.AlignCenter)
        
        layout.addWidget(card, alignment=Qt.AlignCenter)
        
        return overlay

    def start_actual_test(self):
        """Start the actual test from protection overlay"""
        # Reuse the same logic as the top-bar "Start Test" button
        # so the countdown timer and test state start immediately.
        self.toggle_test()

    def switch_passage(self, index):
        """Switch between reading passages"""
        self.current_passage = index
        
        # Update tab states
        for idx, tab in enumerate(self.passage_tabs):
            tab.setChecked(idx == index)
        
        # Update navigation buttons
        self.back_button.setEnabled(index > 0)
        self.next_button.setText("Next ▶" if index < 2 else "Finish")
        
        # Load the passage content
        self.load_passage_content()

    def go_back(self):
        """Navigate to previous passage"""
        if self.current_passage > 0:
            self.switch_passage(self.current_passage - 1)

    def go_next(self):
        """Navigate to next passage or finish test"""
        if self.current_passage < 2:
            self.switch_passage(self.current_passage + 1)
        else:
            self.finish_test()

    def finish_test(self):
        """Finish the test"""
        reply = QMessageBox.question(self, "Finish Test", 
                                   "Are you sure you want to finish the Reading test?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.timer.stop()
            # --- Added: stop live tracker polling ---
            try:
                if hasattr(self, 'answer_poll_timer'):
                    self.answer_poll_timer.stop()
            except Exception:
                pass
            self.test_started = False
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
            self.content_stack.setCurrentWidget(self.protection_overlay)
            QMessageBox.information(self, "Test Completed", "Your Reading test has been completed and submitted.")

    def on_page_loaded(self, ok: bool):
        """Called when the passage HTML finishes loading; refresh completion state and stretch content to the edges."""
        try:
            self.inject_full_width_styles()
        except Exception as e:
            app_logger.debug(f"Error injecting full-width styles: {e}")
        try:
            self.update_completion_count()
        except Exception as e:
            app_logger.debug(f"Error updating completion after page load: {e}")

    def inject_full_width_styles(self):
        """Inject CSS/JS into the loaded page to remove margins/padding and make content full-width."""
        js = r"""
        (function() {
            try {
                // Ensure a meta viewport exists for proper sizing
                var meta = document.querySelector('meta[name=viewport]');
                if (!meta) {
                    meta = document.createElement('meta');
                    meta.name = 'viewport';
                    meta.content = 'width=device-width, initial-scale=1, maximum-scale=1';
                    document.head.appendChild(meta);
                }
                // Create style element
                var style = document.createElement('style');
                style.setAttribute('data-ielts-full-bleed', 'true');
                style.textContent = `
                    html, body { margin:0 !important; padding:0 !important; width:100% !important; height:100% !important; }
                    body, body * { box-sizing: border-box; }
                    .container, .content, .main, .wrapper, .page, .reading-container, .ielts-container, .root, .app, .layout {
                        max-width: none !important; width: 100% !important; margin: 0 !important;
                    }
                `;
                document.head.appendChild(style);
                // Also adjust common wrappers directly under body
                var selectors = ['body > div', 'body > main', 'body > section'];
                selectors.forEach(function(sel){
                    var nodes = document.querySelectorAll(sel);
                    nodes.forEach(function(el){
                        el.style.margin = '0';
                        el.style.padding = '0';
                        el.style.maxWidth = 'none';
                        el.style.width = '100%';
                    });
                });
                // Avoid horizontal scrollbars
                document.documentElement.style.overflowX = 'hidden';
                document.body.style.overflowX = 'hidden';
                return true;
            } catch (e) {
                return e.message;
            }
        })();
        """
        try:
            self.web_view.page().runJavaScript(js)
        except Exception as e:
            app_logger.debug(f"Error applying full-bleed styles: {e}")

    def update_completion_count(self):
        """Update completion count and question tracker for current section"""
        if hasattr(self, 'web_view') and self.web_view.page():
            # Execute JavaScript to count filled inputs and collect answered indices
            js_code = r"""
            (function() {
                try {
                    var inputs = document.querySelectorAll('input[type="text"], input:not([type]), input[type="search"], input[type="email"], input[type="number"], input[type="radio"], input[type="checkbox"], textarea, select, span[contenteditable="true"], div[contenteditable="true"]');
                    var completed = 0;
                    var total = inputs.length;
                    var answered_indices = [];
                    
                    function isFilled(input) {
                        var tag = (input.tagName || '').toLowerCase();
                        var type = (input.type || '').toLowerCase();
                        if (type === 'radio' || type === 'checkbox') return input.checked;
                        if (tag === 'select') return input.value !== '' && input.value !== null;
                        if (input.isContentEditable) {
                            var txt = (input.innerText || input.textContent || '').toString();
                            return txt.length > 0;
                        }
                        // Treat any character as answer, including whitespace
                        return (input.value !== undefined && input.value !== null && String(input.value).length > 0);
                    }
                    
                    function numFrom(input) {
                        // Try data-question attribute first
                        var dataQ = input.getAttribute('data-question');
                        if (dataQ) {
                            var match = dataQ.match(/(\d{1,2})/);
                            if (match) return parseInt(match[1]);
                        }
                        
                        // Try name attribute
                        var name = input.getAttribute('name');
                        if (name) {
                            var match = name.match(/q(\d{1,2})/i);
                            if (match) return parseInt(match[1]);
                            match = name.match(/(\d{1,2})/);
                            if (match) return parseInt(match[1]);
                        }
                        
                        // Try id attribute
                        var id = input.getAttribute('id');
                        if (id) {
                            var match = id.match(/q(\d{1,2})/i);
                            if (match) return parseInt(match[1]);
                            match = id.match(/(\d{1,2})/);
                            if (match) return parseInt(match[1]);
                        }
                        
                        // Look up the nearest label containing a number
                        var label = input.closest('label');
                        if (label) {
                            var t = label.textContent || '';
                            var match = t.match(/(\d{1,2})/);
                            if (match) return parseInt(match[1]);
                        }
                        
                        return null;
                    }
                    
                    inputs.forEach(function(input) {
                        var questionNum = numFrom(input);
                        var filled = isFilled(input);
                        
                        if (filled && questionNum >= 1 && questionNum <= 40) {
                            completed++;
                            answered_indices.push(questionNum);
                        }
                    });
                    
                    return {
                        completed: completed, 
                        total: inputs.length, 
                        answered_indices: answered_indices, 
                        success: true
                    };
                } catch (error) {
                    return {
                        completed: 0, 
                        total: 0, 
                        answered_indices: [], 
                        success: false, 
                        error: error.message
                    };
                }
            })();
            """
            
            def handle_result(result):
                try:
                    if result and isinstance(result, dict) and result.get('success', False):
                        answered = result.get('answered_indices', [])
                        
                        # Filter to current passage range and persist
                        start, end = self.passage_ranges[self.current_passage]
                        current_set = {q for q in answered if start <= q <= end}
                        self.reading_answers_by_passage[self.current_passage] = current_set
                        
                        # Union across passages
                        union_set = set().union(*self.reading_answers_by_passage.values())
                        self.completed_questions = len(union_set)
                        self.completion_label.setText(f"Completed: {self.completed_questions}/40 (Passage {self.current_passage + 1})")
                        
                        # Refresh tracker with all answered questions
                        self.refresh_question_tracker(list(union_set))
                    else:
                        error_msg = result.get('error', 'Unknown error') if result else 'No result'
                        app_logger.debug(f"JavaScript execution error: {error_msg}")
                        # Fallback: preserve previous count
                        union_set = set().union(*self.reading_answers_by_passage.values())
                        self.completed_questions = len(union_set)
                        self.completion_label.setText(f"Completed: {self.completed_questions}/40 (Passage {self.current_passage + 1})")
                        self.refresh_question_tracker(list(union_set))
                except Exception as e:
                    app_logger.debug(f"Error handling JavaScript result: {e}")
                    # Fallback: preserve previous count
                    union_set = set().union(*self.reading_answers_by_passage.values())
                    self.completed_questions = len(union_set)
                    self.completion_label.setText(f"Completed: {self.completed_questions}/40 (Passage {self.current_passage + 1})")
                    self.refresh_question_tracker(list(union_set))
            
            try:
                self.web_view.page().runJavaScript(js_code, handle_result)
            except Exception as e:
                # Fallback if JavaScript execution fails
                app_logger.debug(f"Failed to execute JavaScript: {e}")
                union_set = set().union(*self.reading_answers_by_passage.values())
                self.completed_questions = len(union_set)
                self.completion_label.setText(f"Completed: {self.completed_questions}/40 (Passage {self.current_passage + 1})")
                self.refresh_question_tracker(list(union_set))
        else:
            # Fallback if page not ready
            union_set = set().union(*self.reading_answers_by_passage.values())
            self.completed_questions = len(union_set)
            self.completion_label.setText(f"Completed: {self.completed_questions}/40 (Passage {self.current_passage + 1})")
            self.refresh_question_tracker(list(union_set))

    def toggle_test(self):
        """Start or stop the test"""
        if not self.test_started:
            # Start the test
            self.test_started = True
            self.time_remaining = self.total_time
            self.timer.start(1000)  # Update every second
            self.start_test_button.setText("End Test")
            self.start_test_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #d32f2f;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            
            # Disable subject selection during test
            self.book_combo.setEnabled(False)
            self.subject_combo.setEnabled(False)
            
            # Switch to test content if on overlay
            if self.content_stack.currentWidget() == self.protection_overlay:
                self.content_stack.setCurrentWidget(self.test_content_widget)
                self.load_passage_content()
            # --- Added: start live completion polling ---
            try:
                self.answer_poll_timer.start()
            except Exception:
                pass
        else:
            # End the test
            self.finish_test()

    def update_subject_options(self):
        """Update reading subject options based on selected Cambridge book"""
        # Get selected Cambridge book
        selected_book = self.book_combo.currentText()
        
        # Reload subjects for the selected book
        self.subjects = self.load_subjects(selected_book)
        
        self.subject_combo.clear()
        reading_subjects = self.subjects.get("reading_subjects", [])
        
        # Add subjects for the selected Cambridge book
        if not reading_subjects:
            # Default subjects if file not found
            placeholder_subjects = [
                f"Test 1 - {selected_book}",
                f"Test 2 - {selected_book}",
                f"Test 3 - {selected_book}",
                f"Test 4 - {selected_book}"
            ]
            self.subject_combo.addItems(placeholder_subjects)
        else:
            self.subject_combo.addItems(reading_subjects)
        
        # Load the first subject
        if self.subject_combo.count() > 0:
            self.load_selected_subject()

    def load_selected_subject(self):
        """Load the selected reading subject"""
        self.load_passage_content()

    def load_passage_content(self):
        """Load the passage content into the web view"""
        current_subject = self.subject_combo.currentText()
        if not current_subject:
            return
            
        # Extract test number from subject text (e.g., "Test 1" -> "1")
        test_num = current_subject.split()[-1] if current_subject else "1"
        cambridge_book = self.book_combo.currentText()
        
        # Map Cambridge book names to directory names
        book_mapping = {
            "Cambridge 20": "Cambridge20",
            "Cambridge 19": "Cambridge19"
        }
        
        book_dir = book_mapping.get(cambridge_book, "Cambridge20")
        passage_num = self.current_passage + 1
        
        # Construct file path
        html_file = f"resources/{book_dir}/reading/Test-{test_num}-Passage-{passage_num}.html"
        
        if os.path.exists(html_file):
            # Load the HTML file
            file_url = QUrl.fromLocalFile(os.path.abspath(html_file))
            self.web_view.load(file_url)
        else:
            # Load placeholder content
            placeholder_html = self.create_placeholder_html(passage_num)
            self.web_view.setHtml(placeholder_html)

    def create_placeholder_html(self, passage_num):
        """Create placeholder HTML content when file is not found"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>IELTS Reading Test - Passage {passage_num}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .container {{
                    width: 100%;
                    max-width: none;
                    margin: 0;
                    background-color: white;
                    border-radius: 0;
                    overflow: hidden;
                    box-shadow: none;
                }}
                .header {{
                    background-color: #2c5aa0;
                    color: white;
                    padding: 15px 20px;
                    font-size: 18px;
                    font-weight: bold;
                }}
                .content {{
                    display: flex;
                    min-height: 600px;
                }}
                .passage-panel {{
                    flex: 1;
                    padding: 20px;
                    border-right: 2px solid #e0e0e0;
                    background-color: #fafafa;
                }}
                .questions-panel {{
                    flex: 1;
                    padding: 20px;
                    background-color: white;
                }}
                .placeholder {{
                    text-align: center;
                    color: #666;
                    font-style: italic;
                    margin: 50px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    Reading Passage {passage_num}
                </div>
                <div class="content">
                    <div class="passage-panel">
                        <div class="placeholder">
                            <h3>Passage {passage_num} Content</h3>
                            <p>The reading passage content will appear here.</p>
                            <p>Please ensure the HTML file exists in the resources directory.</p>
                        </div>
                    </div>
                    <div class="questions-panel">
                        <div class="placeholder">
                            <h3>Questions {(passage_num-1)*13 + 1}-{passage_num*13}</h3>
                            <p>The questions for this passage will appear here.</p>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    def show_help(self):
        """Show help dialog"""
        help_text = """
        IELTS Academic Reading Test Help
        
        Navigation:
        • Use the passage tabs to switch between reading passages
        • Use Next/Back buttons to navigate sequentially
        • Monitor your time using the timer in the top-right corner
        
        Answering Questions:
        • Read each passage carefully before attempting questions
        • All answers must be based on information in the passages
        • Follow the word limits specified in the instructions
        • You can return to previous passages at any time
        
        Time Management:
        • You have 60 minutes for the entire test
        • Aim to spend approximately 20 minutes per passage
        • Warnings will appear at 10 and 5 minutes remaining
        """
        
        QMessageBox.information(self, "Help", help_text)

    def build_question_tracker(self, main_layout):
        """Create the bottom question tracker UI with 40 buttons grouped by passage."""
        self.question_buttons = {}
        tracker = QWidget()
        tracker.setObjectName("question_tracker")
        layout = QHBoxLayout(tracker)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(12)
        
        for p_idx in range(3):
            part_widget = QWidget()
            part_layout = QHBoxLayout(part_widget)
            part_layout.setContentsMargins(0, 0, 0, 0)
            part_layout.setSpacing(6)
            
            part_label = QLabel(f"Passage {p_idx + 1}")
            part_label.setObjectName("part_label")
            part_layout.addWidget(part_label)
            
            numbers_container = QWidget()
            nums_layout = QHBoxLayout(numbers_container)
            nums_layout.setContentsMargins(6, 0, 0, 0)
            nums_layout.setSpacing(4)
            
            start, end = self.passage_ranges[p_idx]
            for q in range(start, end + 1):
                btn = QPushButton(f"{q:02d}")
                btn.setObjectName("question_cell")
                btn.setFixedSize(32, 24)
                btn.clicked.connect(lambda checked, num=q: self.on_question_cell_clicked(num))
                self.question_buttons[q] = btn
                nums_layout.addWidget(btn)
            
            part_layout.addWidget(numbers_container)
            layout.addWidget(part_widget)
        
        tracker.setStyleSheet(
            """
            QWidget#question_tracker { background-color: #ffffff; border-top: 1px solid #dee2e6; }
            QLabel#part_label { color: #6c757d; font-size: 11px; font-style: italic; min-width: 70px; }
            QPushButton#question_cell { background-color: #000000; color: #ffffff; border: 1px solid #333333; padding: 2px; border-radius: 2px; min-width: 28px; min-height: 20px; }
            QPushButton#question_cell[answered="true"] { background-color: #007bff; border-color: #0056b3; }
            QPushButton#question_cell:disabled { background-color: #222222; color: #777777; border-color: #444444; }
            """
        )
        
        main_layout.addWidget(tracker)
        # Initialize all cells to black (unanswered)
        self.refresh_question_tracker([])

    def refresh_question_tracker(self, answered_global_numbers):
        """Refresh the tracker buttons based on the union of answered question numbers."""
        if not hasattr(self, 'question_buttons') or not self.question_buttons:
            return
        
        union_set = set(answered_global_numbers or [])
        if not union_set:
            union_set = set().union(*self.reading_answers_by_passage.values())
        
        for q in range(1, 41):
            btn = self.question_buttons.get(q)
            if not btn:
                continue
            btn.setProperty('answered', q in union_set)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

    def on_question_cell_clicked(self, qnum: int):
        """Navigate to the passage containing qnum, then scroll to the matching input."""
        target_idx = None
        for idx, (s, e) in enumerate(self.passage_ranges):
            if s <= qnum <= e:
                target_idx = idx
                break
        if target_idx is None:
            return
        
        if target_idx != self.current_passage:
            self.switch_passage(target_idx)
            QTimer.singleShot(600, lambda: self.scroll_to_question(qnum))
        else:
            self.scroll_to_question(qnum)

    def scroll_to_question(self, qnum: int):
        """Scroll the web page to the element corresponding to qnum."""
        js = f"""
        (function(q) {{
            try {{
                var selectors = [
                    '[data-question="' + q + '"]',
                    '[name*="q' + q + '"]',
                    '[name="' + q + '"]',
                    '#q' + q,
                    '[id*="q' + q + '"]'
                ];
                var el = null;
                for (var i = 0; i < selectors.length; i++) {{
                    el = document.querySelector(selectors[i]);
                    if (el) break;
                }}
                if (!el) {{
                    var candidates = Array.from(document.querySelectorAll('label, p, span, h1, h2, h3, h4'));
                    for (var j = 0; j < candidates.length; j++) {{
                        var t = candidates[j].textContent || '';
                        if (t.match(new RegExp('\\b' + q + '\\b'))) {{
                            el = candidates[j];
                            break;
                        }}
                    }}
                }}
                if (el) {{
                    el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    if (el.focus) el.focus();
                    return {{ success: true }};
                }} else {{
                    return {{ success: false, error: 'Question not found' }};
                }}
            }} catch (e) {{
                return {{ success: false, error: e.message }};
            }}
        }}))({qnum});
        """
        try:
            self.web_view.page().runJavaScript(js)
        except Exception as e:
            app_logger.debug(f"Error scrolling to question {qnum}: {e}")

    def update_timer_display(self):
        """Update the timer display and handle end-of-test logic."""
        if self.time_remaining > 0:
            self.time_remaining -= 1
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            time_display = f"{minutes:02d}:{seconds:02d}"
            self.timer_label.setText(time_display)
            
            # Warning colors at different thresholds
            if self.time_remaining <= 300:  # 5 minutes left
                self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: red; background-color: #f0f0f0; padding: 0 10px;")
            elif self.time_remaining <= 600:  # 10 minutes left
                self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: orange; background-color: #f0f0f0; padding: 0 10px;")
                
            # Show warning at specific times
            if self.time_remaining == 600:  # 10 minutes left
                QMessageBox.warning(self, "Time Alert", "10 minutes remaining for the Reading test.")
            elif self.time_remaining == 300:  # 5 minutes left
                QMessageBox.warning(self, "Time Alert", "5 minutes remaining for the Reading test.")
        else:
            self.timer.stop()
            try:
                if hasattr(self, 'answer_poll_timer'):
                    self.answer_poll_timer.stop()
            except Exception:
                pass
            self.timer_label.setText("00:00")
            self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: red; background-color: #f0f0f0; padding: 0 10px;")
            
            # Alert user
            QMessageBox.critical(self, "Time's Up", "Your Reading test time has ended. Your responses have been saved.")
            
            # Reset test state
            self.test_started = False
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
            self.content_stack.setCurrentWidget(self.protection_overlay)