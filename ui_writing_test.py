import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QSplitter, QComboBox, QPushButton, QStackedWidget,
                             QMessageBox, QFrame, QSizePolicy, QFileDialog,
                             QCheckBox, QRadioButton, QButtonGroup, QDialog,
                             QTabWidget, QScrollArea, QApplication)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QFont, QColor, QTextCursor, QPalette, QTextFormat
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

class EnhancedTextEdit(QTextEdit):
    """Custom TextEdit with enhanced cursor visibility"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set cursor width for better visibility
        self.setCursorWidth(2)
        # Use a monospace font for better writing experience
        self.setFont(QFont("Courier New", 12))
        # Disable rich text
        self.setAcceptRichText(False)
        # Set background to white like official test
        self.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #c0c0c0;
                selection-background-color: #b3d4fc;
                selection-color: black;
                line-height: 1.5;
            }
        """)
        # Cursor blinks at a rate similar to official test
        self.setCursorWidth(2)
        
    def focusInEvent(self, event):
        # When getting focus, make cursor highly visible
        self.setCursorWidth(3)
        super().focusInEvent(event)
        
    def focusOutEvent(self, event):
        # Reset cursor width on focus out
        self.setCursorWidth(2)
        super().focusOutEvent(event)

class WritingTestUI(QWidget):
    def __init__(self):
        super().__init__()
        self.subjects = self.load_subjects()
        self.task1_time = 20 * 60  # 20 minutes in seconds
        self.task2_time = 40 * 60  # 40 minutes in seconds
        self.total_time = self.task1_time + self.task2_time  # 60 minutes total
        self.time_remaining = self.total_time
        self.current_task = 0  # 0 for Task 1, 1 for Task 2
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_display)
        self.test_id = "IELTS-CBT-" + "".join([str(i) for i in range(10)])  # Test ID like official test
        self.test_started = False
        self.module_type = "general"  # Default to general module
        
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
                padding: 4px 8px;
                border-radius: 2px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #d8d8d8;
            }
            QPushButton:checked {
                background-color: #c0c0c0;
                border: 1px solid #a0a0a0;
            }
            QLabel {
                color: #333333;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background: white;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #c0c0c0;
                padding: 5px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
        """)

    def load_subjects(self, filename="subjects.json"):
        try:
            with open(filename, 'r') as f:
                subjects_data = json.load(f)
            # Ensure keys exist, provide defaults if not
            if "task1_subjects" not in subjects_data:
                subjects_data["task1_subjects"] = {"academic": [], "general": []}
            if "academic" not in subjects_data["task1_subjects"]:
                 subjects_data["task1_subjects"]["academic"] = []
            if "general" not in subjects_data["task1_subjects"]:
                 subjects_data["task1_subjects"]["general"] = []
            if "task2_subjects" not in subjects_data:
                 subjects_data["task2_subjects"] = []
            return subjects_data
        except FileNotFoundError:
            print(f"Error: {filename} not found.")
            # Return default structure on error
            return {"task1_subjects": {"academic": [], "general": []}, "task2_subjects": []}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {filename}.")
             # Return default structure on error
            return {"task1_subjects": {"academic": [], "general": []}, "task2_subjects": []}

    def initUI(self):
        # Create clean, minimal layout similar to official test
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Top Bar - Simplified like IELTS CBT ---
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #d0d0d0;")
        top_bar.setFixedHeight(36)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(10, 0, 10, 0)

        # Test ID label - left aligned
        test_id_label = QLabel(f"Test ID: {self.test_id}")
        test_id_label.setStyleSheet("font-size: 12px; font-weight: normal;")
        
        # Task buttons in the center (like tabs in official test)
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(1)
        
        self.task1_tab = QPushButton("Task 1")
        self.task2_tab = QPushButton("Task 2")
        
        for btn in [self.task1_tab, self.task2_tab]:
            btn.setCheckable(True)
            btn.setMinimumWidth(100)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #c0c0c0;
                    border-bottom: none;
                    border-radius: 2px 2px 0 0;
                    padding: 6px 12px;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: white;
                    border-bottom: 1px solid white;
                }
            """)
            tab_layout.addWidget(btn)
        
        self.task1_tab.setChecked(True)
        self.task1_tab.clicked.connect(lambda: self.switch_task(0))
        self.task2_tab.clicked.connect(lambda: self.switch_task(1))
        
        # Timer display - right aligned like official test
        self.timer_label = QLabel("60:00")
        self.timer_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 0 10px;")
        self.timer_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Start/pause button
        self.start_test_button = QPushButton("Start Test")
        self.start_test_button.clicked.connect(self.toggle_test)
        self.start_test_button.setMinimumWidth(80)
        self.start_test_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        # Help button
        self.help_button = QPushButton("Help")
        self.help_button.clicked.connect(self.show_help)
        
        top_bar_layout.addWidget(test_id_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(tab_widget)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.timer_label)
        top_bar_layout.addWidget(self.help_button)
        top_bar_layout.addWidget(self.start_test_button)
        
        main_layout.addWidget(top_bar)

        # --- Main Content Area ---
        self.task_stack = QStackedWidget()
        main_layout.addWidget(self.task_stack)

        # --- Create Task Widgets ---
        for task_idx in range(2):
            task_widget = QWidget()
            task_layout = QVBoxLayout(task_widget)
            task_layout.setContentsMargins(0, 0, 0, 0)
            task_layout.setSpacing(0)
            
            # --- Task Instructions Bar ---
            instruction_bar = QWidget()
            instruction_bar.setStyleSheet("background-color: #e8e8e8;")
            instruction_bar.setMinimumHeight(70)
            instruction_layout = QHBoxLayout(instruction_bar)
            
            if task_idx == 0:
                # Task 1 Instructions
                instruction_text = QLabel("Task 1: You should spend about 20 minutes on this task. Write at least 150 words.")
                
                # Module selection only for Task 1
                module_widget = QWidget()
                module_layout = QVBoxLayout(module_widget)
                module_layout.setContentsMargins(0, 0, 0, 0)
                
                module_label = QLabel("Select module:")
                self.module_academic = QRadioButton("Academic")
                self.module_general = QRadioButton("General Training")
                self.module_general.setChecked(True)
                
                module_group = QButtonGroup(self)
                module_group.addButton(self.module_academic)
                module_group.addButton(self.module_general)
                
                module_layout.addWidget(module_label)
                module_layout.addWidget(self.module_academic)
                module_layout.addWidget(self.module_general)
                
                # Connect module selection to update type
                self.module_academic.toggled.connect(self.update_module_type)
            else:
                # Task 2 Instructions
                instruction_text = QLabel("Task 2: You should spend about 40 minutes on this task. Write at least 250 words.")
                module_widget = QWidget()  # Empty widget for layout consistency
            
            instruction_text.setWordWrap(True)
            instruction_text.setStyleSheet("font-size: 13px; font-weight: bold;")
            
            instruction_layout.addWidget(instruction_text, 1)
            instruction_layout.addWidget(module_widget)
            
            task_layout.addWidget(instruction_bar)
            
            # --- Task Content Area ---
            content_widget = QWidget()
            content_layout = QHBoxLayout(content_widget)
            content_layout.setContentsMargins(10, 10, 10, 10)
            
            # Left side: Question/Prompt
            prompt_area = QScrollArea()
            prompt_area.setWidgetResizable(True)
            prompt_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            prompt_area.setStyleSheet("""
                QScrollArea {
                    background-color: white;
                    border: 1px solid #d0d0d0;
                }
            """)
            
            prompt_content = QWidget()
            prompt_layout = QVBoxLayout(prompt_content)
            
            # Add subject selector
            subject_label = QLabel("Select question:")
            subject_label.setStyleSheet("font-weight: bold;")
            
            if task_idx == 0:
                self.task1_subject_combo = QComboBox()
                self.task1_subject_combo.currentIndexChanged.connect(self.update_task1_subject_label)
                self.task1_subject_label = QLabel("")
                self.task1_subject_label.setWordWrap(True)
                self.task1_subject_label.setStyleSheet("font-size: 13px; margin: 10px 0; line-height: 1.4;")
                
                prompt_layout.addWidget(subject_label)
                prompt_layout.addWidget(self.task1_subject_combo)
                prompt_layout.addWidget(self.task1_subject_label)
            else:
                self.task2_subject_combo = QComboBox()
                self.task2_subject_combo.currentIndexChanged.connect(self.update_task2_subject_label)
                self.task2_subject_label = QLabel("")
                self.task2_subject_label.setWordWrap(True)
                self.task2_subject_label.setStyleSheet("font-size: 13px; margin: 10px 0; line-height: 1.4;")
                
                prompt_layout.addWidget(subject_label)
                prompt_layout.addWidget(self.task2_subject_combo)
                prompt_layout.addWidget(self.task2_subject_label)
            
            prompt_layout.addStretch()
            prompt_area.setWidget(prompt_content)
            
            # Right side: Answer area
            answer_widget = QWidget()
            answer_layout = QVBoxLayout(answer_widget)
            answer_layout.setContentsMargins(0, 0, 0, 0)
            
            answer_label = QLabel("Your answer:")
            answer_label.setStyleSheet("font-weight: bold;")
            
            # Use enhanced text edit for better cursor visibility
            if task_idx == 0:
                self.task1_text_edit = EnhancedTextEdit()
                self.task1_text_edit.textChanged.connect(self.update_word_count_task1)
                answer_layout.addWidget(answer_label)
                answer_layout.addWidget(self.task1_text_edit)
            else:
                self.task2_text_edit = EnhancedTextEdit()
                self.task2_text_edit.textChanged.connect(self.update_word_count_task2)
                answer_layout.addWidget(answer_label)
                answer_layout.addWidget(self.task2_text_edit)
            
            # Word count label below text edit
            if task_idx == 0:
                self.task1_word_count = QLabel("Words: 0")
            else:
                self.task2_word_count = QLabel("Words: 0")
                
            word_count_style = """
                font-size: 12px;
                color: #666;
                padding: 2px 5px;
                background-color: #f8f8f8;
                border-top: 1px solid #e0e0e0;
            """
            
            if task_idx == 0:
                self.task1_word_count.setStyleSheet(word_count_style)
                answer_layout.addWidget(self.task1_word_count)
            else:
                self.task2_word_count.setStyleSheet(word_count_style)
                answer_layout.addWidget(self.task2_word_count)
            
            # Set prompt area to 30% and answer area to 70% of width
            content_layout.addWidget(prompt_area, 30)
            content_layout.addWidget(answer_widget, 70)
            
            task_layout.addWidget(content_widget)
            
            self.task_stack.addWidget(task_widget)
        
        # --- Bottom Status Bar ---
        status_bar = QWidget()
        status_bar.setFixedHeight(30)
        status_bar.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #d0d0d0;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(10, 0, 10, 0)
        
        # Scratch paper notice
        scratch_notice = QLabel("Note: Physical scratch paper is provided in the official test")
        scratch_notice.setStyleSheet("font-style: italic; color: #666;")
        
        # Keyboard shortcuts reminder
        shortcuts_label = QLabel("Shortcuts: Ctrl+X (Cut), Ctrl+C (Copy), Ctrl+V (Paste), Ctrl+P (Print)")
        shortcuts_label.setStyleSheet("color: #666; font-size: 11px;")
        shortcuts_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        status_layout.addWidget(scratch_notice)
        status_layout.addStretch()
        status_layout.addWidget(shortcuts_label)
        
        main_layout.addWidget(status_bar)
        
        # Set the main layout
        self.setLayout(main_layout)
        
        # Initialize task subjects
        self.update_task1_options()
        self.task2_subject_combo.addItems(self.subjects.get("task2_subjects", []))
        
        # Show Task 1 initially
        self.switch_task(0)

    def switch_task(self, index):
        """Switch between Task 1 and Task 2"""
        self.task_stack.setCurrentIndex(index)
        self.task1_tab.setChecked(index == 0)
        self.task2_tab.setChecked(index == 1)
        self.current_task = index
        
        # Update word count display
        self.update_word_count()

    def update_word_count(self):
        """Update word count based on current task"""
        if self.current_task == 0:
            text = self.task1_text_edit.toPlainText()
            word_count = len(text.split()) if text.strip() else 0
            self.task1_word_count.setText(f"Words: {word_count}")
            
            # Highlight if below minimum
            if word_count < 150:
                self.task1_word_count.setStyleSheet("color: #cc0000; font-weight: bold;")
            else:
                self.task1_word_count.setStyleSheet("color: #008800; font-weight: bold;")
        else:
            text = self.task2_text_edit.toPlainText()
            word_count = len(text.split()) if text.strip() else 0
            self.task2_word_count.setText(f"Words: {word_count}")
            
            # Highlight if below minimum
            if word_count < 250:
                self.task2_word_count.setStyleSheet("color: #cc0000; font-weight: bold;")
            else:
                self.task2_word_count.setStyleSheet("color: #008800; font-weight: bold;")

    def update_word_count_task1(self):
        """Update word count for Task 1"""
        text = self.task1_text_edit.toPlainText()
        word_count = len(text.split()) if text.strip() else 0
        self.task1_word_count.setText(f"Words: {word_count}")
        
        # Highlight if below minimum
        if word_count < 150:
            self.task1_word_count.setStyleSheet("color: #cc0000; font-weight: bold;")
        else:
            self.task1_word_count.setStyleSheet("color: #008800; font-weight: bold;")

    def update_word_count_task2(self):
        """Update word count for Task 2"""
        text = self.task2_text_edit.toPlainText()
        word_count = len(text.split()) if text.strip() else 0
        self.task2_word_count.setText(f"Words: {word_count}")
        
        # Highlight if below minimum
        if word_count < 250:
            self.task2_word_count.setStyleSheet("color: #cc0000; font-weight: bold;")
        else:
            self.task2_word_count.setStyleSheet("color: #008800; font-weight: bold;")

    def update_timer_display(self):
        """Update the timer display - showing total time like official test"""
        if self.time_remaining > 0:
            self.time_remaining -= 1
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            time_display = f"{minutes:02d}:{seconds:02d}"
            self.timer_label.setText(time_display)
            
            # Warning colors at different thresholds
            if self.time_remaining <= 300:  # 5 minutes left
                self.timer_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
            elif self.time_remaining <= 600:  # 10 minutes left
                self.timer_label.setStyleSheet("font-size: 14px; font-weight: bold; color: orange;")
                
            # Show warning at specific times
            if self.time_remaining == 600:  # 10 minutes left
                QMessageBox.warning(self, "Time Alert", "10 minutes remaining for the Writing test.")
            elif self.time_remaining == 300:  # 5 minutes left
                QMessageBox.warning(self, "Time Alert", "5 minutes remaining for the Writing test.")
        else:
            self.timer.stop()
            self.timer_label.setText("00:00")
            self.timer_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
            
            # Disable editing when time is up
            self.task1_text_edit.setReadOnly(True)
            self.task2_text_edit.setReadOnly(True)
            
            # Alert user
            QMessageBox.critical(self, "Time's Up", "Your Writing test time has ended. Your responses have been saved.")
            
            # Reset test state
            self.test_started = False
            self.start_test_button.setText("Start Test")
            self.start_test_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)

    def update_task1_options(self):
        """Update Task 1 subject options based on module type"""
        self.task1_subject_combo.clear()
        task1_subjects = self.subjects.get("task1_subjects", {}).get(self.module_type, [])
        self.task1_subject_combo.addItems(task1_subjects)
        
        if self.task1_subject_combo.count() > 0:
            self.update_task1_subject_label()

    def update_task1_subject_label(self):
        """Update Task 1 subject display"""
        selected_subject = self.task1_subject_combo.currentText()
        if selected_subject:
            self.task1_subject_label.setText(selected_subject)
        else:
            self.task1_subject_label.setText("")

    def update_task2_subject_label(self):
        """Update Task 2 subject display"""
        selected_subject = self.task2_subject_combo.currentText()
        if selected_subject:
            self.task2_subject_label.setText(selected_subject)
        else:
            self.task2_subject_label.setText("")

    def update_module_type(self):
        """Update module type (Academic/General)"""
        if self.module_academic.isChecked():
            self.module_type = "academic"
        else:
            self.module_type = "general"
        
        # Update subject options
        self.update_task1_options()

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
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            
            # Disable module selection
            self.module_academic.setEnabled(False)
            self.module_general.setEnabled(False)
            
            # Show confirmation
            QMessageBox.information(self, "Test Started", 
                                    "The IELTS Writing test has started. You have 60 minutes to complete both tasks.")
        else:
            # Confirm before stopping
            reply = QMessageBox.question(self, "End Test", 
                                        "Are you sure you want to end the test? This would be equivalent to submitting your answers early.",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Stop the test
                self.test_started = False
                self.timer.stop()
                self.start_test_button.setText("Start Test")
                self.start_test_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                
                # Re-enable module selection
                self.module_academic.setEnabled(True)
                self.module_general.setEnabled(True)
                
                # Show test completion message
                self.show_test_summary()

    def show_test_summary(self):
        """Show a summary of the test when completed"""
        task1_words = len(self.task1_text_edit.toPlainText().split()) if self.task1_text_edit.toPlainText().strip() else 0
        task2_words = len(self.task2_text_edit.toPlainText().split()) if self.task2_text_edit.toPlainText().strip() else 0
        
        # Prepare summary message
        summary = f"Writing Test Completed\n\n"
        summary += f"Task 1 Word Count: {task1_words} {'✓' if task1_words >= 150 else '❌'}\n"
        summary += f"Task 2 Word Count: {task2_words} {'✓' if task2_words >= 250 else '❌'}\n\n"
        summary += "Your responses have been saved.\n"
        summary += "In the official test, your answers would now be submitted for marking."
        
        QMessageBox.information(self, "Test Summary", summary)

    def show_help(self):
        """Show help information about the test"""
        help_text = """
IELTS Writing Test Help

Test Duration: 60 minutes total
- Task 1: Suggested 20 minutes, minimum 150 words
- Task 2: Suggested 40 minutes, minimum 250 words

Navigation:
- Use the Task 1 and Task 2 tabs to switch between tasks
- Both tasks must be completed within the 60-minute time limit

Text Editor:
- Basic typing only (no formatting tools)
- Cut, copy, paste available via keyboard shortcuts or right-click menu
- Word count updates automatically as you type

Time Management:
- The timer shows total remaining time for both tasks
- You must manage the recommended time split yourself
- Warnings appear at 10 and 5 minutes remaining

Academic Task 1:
- Describe, summarize or explain visual information 
- Write at least 150 words

General Training Task 1:
- Write a letter for a given situation
- Write at least 150 words

Task 2 (both modules):
- Write an essay in response to a point of view or argument
- Write at least 250 words

Note: In the real test, physical scratch paper is provided for planning.
"""
        QMessageBox.information(self, "Help", help_text)

    def export_answer(self):
        """Export answers to a text file"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Writing Test Answers", 
            f"IELTS_Writing_Test_{self.test_id}.txt",
            "Text Files (*.txt)", options=options)
            
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    module = "Academic" if self.module_type == "academic" else "General Training"
                    f.write(f"IELTS WRITING TEST - {module}\n")
                    f.write(f"Test ID: {self.test_id}\n\n")
                    
                    # Task 1
                    f.write("TASK 1\n")
                    f.write(f"Question: {self.task1_subject_label.text()}\n\n")
                    f.write("Answer:\n")
                    f.write(self.task1_text_edit.toPlainText())
                    f.write(f"\n\nWord count: {len(self.task1_text_edit.toPlainText().split())}\n\n")
                    
                    # Task 2
                    f.write("\nTASK 2\n")
                    f.write(f"Question: {self.task2_subject_label.text()}\n\n")
                    f.write("Answer:\n")
                    f.write(self.task2_text_edit.toPlainText())
                    f.write(f"\n\nWord count: {len(self.task2_text_edit.toPlainText().split())}\n")
                
                QMessageBox.information(self, "Export Successful", f"Answers saved to {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error saving file: {str(e)}")

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_P:
            self.print_answers()
        else:
            super().keyPressEvent(event)
        
    def print_answers(self):
        """Print test answers"""
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            document = QTextDocument()
            module = "Academic" if self.module_type == "academic" else "General Training"
            html = f"<h2>IELTS WRITING TEST - {module}</h2>"
            html += f"<p>Test ID: {self.test_id}</p>"
            
            # Task 1
            html += "<h3>TASK 1</h3>"
            html += f"<p><b>Question:</b> {self.task1_subject_label.text()}</p>"
            html += "<p><b>Answer:</b></p>"
            html += f"<p>{self.task1_text_edit.toPlainText().replace('\\n', '<br>')}</p>"
            html += f"<p>Word count: {len(self.task1_text_edit.toPlainText().split())}</p>"
            
            # Task 2
            html += "<h3>TASK 2</h3>"
            html += f"<p><b>Question:</b> {self.task2_subject_label.text()}</p>"
            html += "<p><b>Answer:</b></p>"
            html += f"<p>{self.task2_text_edit.toPlainText().replace('\\n', '<br>')}</p>"
            html += f"<p>Word count: {len(self.task2_text_edit.toPlainText().split())}</p>"
            
            document.setHtml(html)
            document.print_(printer)
            QMessageBox.information(self, "Print Successful", "Your answers have been sent to the printer.")
