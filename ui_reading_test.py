import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QSplitter, QComboBox, QPushButton, QStackedWidget, 
                             QMessageBox, QFrame, QSizePolicy, QFileDialog,
                             QCheckBox, QRadioButton, QButtonGroup, QScrollArea,
                             QGroupBox, QLineEdit, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QFont, QColor, QTextCursor, QPalette, QTextFormat

class ReadingTestUI(QWidget):
    def __init__(self):
        super().__init__()
        self.subjects = self.load_subjects()
        self.total_time = 60 * 60  # 60 minutes in seconds
        self.time_remaining = self.total_time
        self.current_passage = 0  # 0, 1, or 2 for the three passages
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_display)
        self.test_id = "IELTS-CBT-" + "".join([str(i) for i in range(10)])  # Test ID like official test
        self.test_started = False
        self.module_type = "general"  # Default to general module
        
        # Apply a clean, consistent style
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
            QScrollArea {
                border: 1px solid #c0c0c0;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #c0c0c0;
            }
        """)

    def load_subjects(self, filename="subjects.json"):
        try:
            with open(filename, 'r') as f:
                subjects_data = json.load(f)
            # Ensure reading section exists with defaults
            if "reading_subjects" not in subjects_data:
                subjects_data["reading_subjects"] = {"academic": [], "general": []}
            if "academic" not in subjects_data["reading_subjects"]:
                subjects_data["reading_subjects"]["academic"] = []
            if "general" not in subjects_data["reading_subjects"]:
                subjects_data["reading_subjects"]["general"] = []
            return subjects_data
        except FileNotFoundError:
            print(f"Error: {filename} not found.")
            # Return default structure on error
            return {"reading_subjects": {"academic": [], "general": []}}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {filename}.")
            # Return default structure on error
            return {"reading_subjects": {"academic": [], "general": []}}

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
        
        # Passage tabs in the center
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(1)
        
        self.passage_tabs = []
        for i in range(3):
            tab = QPushButton(f"Passage {i+1}")
            tab.setCheckable(True)
            tab.setMinimumWidth(100)
            tab.setStyleSheet("""
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
            self.passage_tabs.append(tab)
            tab.clicked.connect(lambda checked, idx=i: self.switch_passage(idx))
            tab_layout.addWidget(tab)
        
        self.passage_tabs[0].setChecked(True)
        
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

        # --- Module selection bar ---
        module_bar = QWidget()
        module_bar.setStyleSheet("background-color: #e8e8e8;")
        module_bar.setFixedHeight(40)
        module_layout = QHBoxLayout(module_bar)
        
        # Module selection
        module_label = QLabel("Select module:")
        self.module_academic = QRadioButton("Academic")
        self.module_general = QRadioButton("General Training")
        self.module_general.setChecked(True)
        
        module_group = QButtonGroup(self)
        module_group.addButton(self.module_academic)
        module_group.addButton(self.module_general)
        
        # Subject selection
        subject_label = QLabel("Select reading test:")
        self.subject_combo = QComboBox()
        self.subject_combo.setMinimumWidth(300)
        
        # Connect module selection to update type
        self.module_academic.toggled.connect(self.update_module_type)
        
        module_layout.addWidget(module_label)
        module_layout.addWidget(self.module_academic)
        module_layout.addWidget(self.module_general)
        module_layout.addSpacing(20)
        module_layout.addWidget(subject_label)
        module_layout.addWidget(self.subject_combo)
        module_layout.addStretch()
        
        main_layout.addWidget(module_bar)

        # --- Main Content Area ---
        self.passages_stack = QStackedWidget()
        main_layout.addWidget(self.passages_stack)

        # --- Create Passage Widgets ---
        for passage_idx in range(3):
            passage_widget = QWidget()
            passage_layout = QHBoxLayout(passage_widget)
            passage_layout.setContentsMargins(10, 10, 10, 10)
            
            # Create a splitter for adjustable panes
            splitter = QSplitter(Qt.Horizontal)
            
            # Left pane - Reading passage
            passage_area = QScrollArea()
            passage_area.setWidgetResizable(True)
            passage_area.setStyleSheet("background-color: white;")
            
            passage_content = QWidget()
            passage_content_layout = QVBoxLayout(passage_content)
            
            # Placeholder for passage title
            passage_title = QLabel(f"Passage {passage_idx + 1}")
            passage_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
            
            # Placeholder for passage text
            passage_text = QTextEdit()
            passage_text.setReadOnly(True)
            passage_text.setStyleSheet("""
                QTextEdit {
                    font-family: 'Times New Roman', serif;
                    font-size: 14px;
                    line-height: 1.5;
                    color: #333;
                    padding: 10px;
                }
            """)
            passage_text.setFixedWidth(500)  # Fixed width for consistent reading experience
            
            # Store references to text widgets for later population
            setattr(self, f"passage_title_{passage_idx}", passage_title)
            setattr(self, f"passage_text_{passage_idx}", passage_text)
            
            passage_content_layout.addWidget(passage_title)
            passage_content_layout.addWidget(passage_text)
            passage_area.setWidget(passage_content)
            
            # Right pane - Questions
            questions_area = QScrollArea()
            questions_area.setWidgetResizable(True)
            questions_area.setStyleSheet("background-color: white;")
            
            questions_content = QWidget()
            questions_layout = QVBoxLayout(questions_content)
            
            # Questions container
            questions_group = QWidget()
            questions_group_layout = QVBoxLayout(questions_group)
            questions_group_layout.setContentsMargins(0, 0, 0, 0)
            
            # Add placeholder questions
            for q_idx in range(13):  # Typically 13-14 questions per passage
                q_number = q_idx + 1 + (passage_idx * 13)
                q_container = QWidget()
                q_layout = QVBoxLayout(q_container)
                q_layout.setContentsMargins(0, 5, 0, 5)
                
                q_text = QLabel(f"Question {q_number}: [Question will appear here]")
                q_text.setWordWrap(True)
                q_text.setStyleSheet("font-weight: bold; margin-top: 10px;")
                
                q_input = QLineEdit()
                q_input.setPlaceholderText("Your answer")
                
                q_layout.addWidget(q_text)
                q_layout.addWidget(q_input)
                
                # Store references for later access
                setattr(self, f"q_text_{passage_idx}_{q_idx}", q_text)
                setattr(self, f"q_input_{passage_idx}_{q_idx}", q_input)
                
                questions_group_layout.addWidget(q_container)
            
            questions_layout.addWidget(questions_group)
            questions_area.setWidget(questions_content)
            
            # Add panes to splitter
            splitter.addWidget(passage_area)
            splitter.addWidget(questions_area)
            splitter.setSizes([500, 500])  # Initial 50/50 split
            
            passage_layout.addWidget(splitter)
            self.passages_stack.addWidget(passage_widget)
        
        # --- Bottom Status Bar ---
        status_bar = QWidget()
        status_bar.setFixedHeight(30)
        status_bar.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #d0d0d0;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(10, 0, 10, 0)
        
        # Completion status
        self.completion_label = QLabel("Completed: 0/40 questions")
        self.completion_label.setStyleSheet("color: #666;")
        
        # Navigation hints
        nav_label = QLabel("Use the tabs above to navigate between passages")
        nav_label.setStyleSheet("font-style: italic; color: #666;")
        nav_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        status_layout.addWidget(self.completion_label)
        status_layout.addStretch()
        status_layout.addWidget(nav_label)
        
        main_layout.addWidget(status_bar)
        
        # Set the main layout
        self.setLayout(main_layout)
        
        # Initialize with sample content
        self.update_subject_options()
        self.subject_combo.currentIndexChanged.connect(self.load_selected_subject)
        
        # Show first passage initially
        self.switch_passage(0)

    def switch_passage(self, index):
        """Switch between reading passages"""
        self.passages_stack.setCurrentIndex(index)
        self.current_passage = index
        
        # Update tab states
        for idx, tab in enumerate(self.passage_tabs):
            tab.setChecked(idx == index)
            
        # Update completion count
        self.update_completion_count()

    def update_completion_count(self):
        """Update the completion count based on filled answers"""
        filled_count = 0
        total_count = 39  # Typical IELTS reading test has 40 questions
        
        # Iterate through all question inputs
        for passage_idx in range(3):
            for q_idx in range(13):
                q_input = getattr(self, f"q_input_{passage_idx}_{q_idx}", None)
                if q_input and q_input.text().strip():
                    filled_count += 1
        
        self.completion_label.setText(f"Completed: {filled_count}/{total_count} questions")

    def update_timer_display(self):
        """Update the timer display"""
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
                QMessageBox.warning(self, "Time Alert", "10 minutes remaining for the Reading test.")
            elif self.time_remaining == 300:  # 5 minutes left
                QMessageBox.warning(self, "Time Alert", "5 minutes remaining for the Reading test.")
        else:
            self.timer.stop()
            self.timer_label.setText("00:00")
            self.timer_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
            
            # Disable editing when time is up
            for passage_idx in range(3):
                for q_idx in range(13):
                    q_input = getattr(self, f"q_input_{passage_idx}_{q_idx}", None)
                    if q_input:
                        q_input.setReadOnly(True)
            
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
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)

    def update_module_type(self):
        """Update module type (Academic/General)"""
        if self.module_academic.isChecked():
            self.module_type = "academic"
        else:
            self.module_type = "general"
        
        # Update subject options
        self.update_subject_options()

    def update_subject_options(self):
        """Update reading subject options based on module type"""
        self.subject_combo.clear()
        reading_subjects = self.subjects.get("reading_subjects", {}).get(self.module_type, [])
        
        # Add placeholder if no subjects available
        if not reading_subjects:
            placeholder_subjects = [
                "Climate Change and its Effects",
                "The History of Transportation",
                "Urbanization in Modern Society"
            ] if self.module_type == "academic" else [
                "Community Center Activities",
                "Job Application Process",
                "Vacation Accommodation Guide"
            ]
            self.subject_combo.addItems(placeholder_subjects)
        else:
            self.subject_combo.addItems(reading_subjects)
        
        # Load the first subject
        if self.subject_combo.count() > 0:
            self.load_selected_subject()

    def load_selected_subject(self):
        """Load the selected reading subject"""
        current_subject = self.subject_combo.currentText()
        if not current_subject:
            return
            
        # For now we'll generate placeholder content
        # In a real app, you would load the actual content from a database or file
        
        # Generate sample passage content for each passage
        for passage_idx in range(3):
            passage_title = getattr(self, f"passage_title_{passage_idx}")
            passage_text = getattr(self, f"passage_text_{passage_idx}")
            
            # Set passage title
            subject_parts = current_subject.split(" - ") if " - " in current_subject else [current_subject]
            if len(subject_parts) > passage_idx:
                title = subject_parts[passage_idx]
            else:
                title = f"Passage {passage_idx + 1}: {current_subject}"
            
            passage_title.setText(title)
            
            # Set placeholder passage text
            sample_text = f"""
            <h3>Passage {passage_idx + 1}: {title}</h3>
            <p>This is a sample reading passage for the IELTS {self.module_type.capitalize()} Reading test.</p>
            <p>In a real test, this would contain approximately 700-800 words of authentic text.</p>
            <p>The passage would include several paragraphs with headings and possibly some visuals like tables or graphs.</p>
            <p>For the purposes of this simulator, imagine this is a detailed article about {current_subject.lower()}.</p>
            <p>It would discuss various aspects such as:</p>
            <ul>
                <li>Historical background</li>
                <li>Current situation</li>
                <li>Future implications</li>
                <li>Different perspectives</li>
                <li>Statistical data</li>
            </ul>
            <p>The text would be challenging but accessible, similar to what you would find in newspapers, journals, magazines, or books.</p>
            <p>It would be designed to test your reading comprehension skills, including:</p>
            <ul>
                <li>Understanding main ideas</li>
                <li>Identifying specific information</li>
                <li>Recognizing writers' opinions</li>
                <li>Following the development of an argument</li>
                <li>Understanding logical connections</li>
            </ul>
            <p>The passage would be followed by 13-14 questions of various types, such as:</p>
            <ul>
                <li>Multiple choice</li>
                <li>Matching headings</li>
                <li>True/False/Not Given</li>
                <li>Sentence completion</li>
                <li>Summary completion</li>
                <li>Diagram labeling</li>
                <li>Short-answer questions</li>
            </ul>
            """
            
            passage_text.setHtml(sample_text)
            
            # Update the questions for this passage
            for q_idx in range(13):
                q_number = q_idx + 1 + (passage_idx * 13)
                q_text = getattr(self, f"q_text_{passage_idx}_{q_idx}")
                
                # Generate a sample question
                question_types = [
                    "True/False/Not Given: ",
                    "Complete the sentence: ",
                    "Choose the correct letter (A, B, C or D): ",
                    "Fill in the gap with ONE WORD ONLY: ",
                    "Answer the question with NO MORE THAN THREE WORDS: "
                ]
                question_type = question_types[q_idx % len(question_types)]
                question_content = f"According to the passage, what is the main aspect of {current_subject.lower()}?"
                
                q_text.setText(f"Question {q_number}: {question_type}{question_content}")

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
            self.subject_combo.setEnabled(False)
            
            # Show confirmation
            QMessageBox.information(self, "Test Started", 
                                   "The IELTS Reading test has started. You have 60 minutes to complete all three passages.")
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
                self.subject_combo.setEnabled(True)
                
                # Show test completion message
                self.show_test_summary()

    def show_test_summary(self):
        """Show a summary of the test when completed"""
        completed_count = 0
        total_count = 39
        
        # Count completed questions
        for passage_idx in range(3):
            for q_idx in range(13):
                q_input = getattr(self, f"q_input_{passage_idx}_{q_idx}", None)
                if q_input and q_input.text().strip():
                    completed_count += 1
        
        # Prepare summary message
        summary = f"Reading Test Completed\n\n"
        summary += f"Questions Answered: {completed_count}/{total_count}\n\n"
        summary += "Your responses have been saved.\n"
        summary += "In the official test, your answers would now be submitted for marking."
        
        QMessageBox.information(self, "Test Summary", summary)

    def show_help(self):
        """Show help information about the test"""
        help_text = """
IELTS Reading Test Help

Test Duration: 60 minutes total
- 3 reading passages, each with 13-14 questions
- 40 questions total
- No extra time for transferring answers

Navigation:
- Use the Passage tabs to switch between the three reading passages
- All passages and questions must be completed within the 60-minute time limit

Reading Strategies:
- Skim the questions before reading the passage
- Use the highlighting feature (right-click on text) to mark key information
- Answer easier questions first to build confidence
- Watch the timer carefully

Question Types:
- Multiple choice
- Identifying information (True/False/Not Given)
- Matching information
- Matching headings
- Matching features
- Matching sentence endings
- Sentence completion
- Summary/note/table/flow-chart completion
- Diagram label completion
- Short-answer questions

Academic vs. General Training:
- Academic: Three long passages with more complex vocabulary
- General Training: More passages (up to 5) with increasing difficulty

Note: In the real test, you can write on the question paper, but final answers
must be entered in the answer boxes.
"""
        QMessageBox.information(self, "Help", help_text)

    def export_answers(self):
        """Export answers to a text file"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Reading Test Answers", 
            f"IELTS_Reading_Test_{self.test_id}.txt",
            "Text Files (*.txt)", options=options)
            
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    module = "Academic" if self.module_type == "academic" else "General Training"
                    f.write(f"IELTS READING TEST - {module}\n")
                    f.write(f"Test ID: {self.test_id}\n")
                    f.write(f"Subject: {self.subject_combo.currentText()}\n\n")
                    
                    for passage_idx in range(3):
                        passage_title = getattr(self, f"passage_title_{passage_idx}")
                        f.write(f"PASSAGE {passage_idx + 1}: {passage_title.text()}\n\n")
                        
                        for q_idx in range(13):
                            q_number = q_idx + 1 + (passage_idx * 13)
                            q_text = getattr(self, f"q_text_{passage_idx}_{q_idx}")
                            q_input = getattr(self, f"q_input_{passage_idx}_{q_idx}")
                            
                            question = q_text.text().replace("Question ", "", 1)
                            answer = q_input.text()
                            
                            f.write(f"{q_number}. {question}\n")
                            f.write(f"   Answer: {answer}\n\n")
                
                QMessageBox.information(self, "Export Successful", f"Answers saved to {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error saving file: {str(e)}") 