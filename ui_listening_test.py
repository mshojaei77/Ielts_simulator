import json
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QSplitter, QComboBox, QPushButton, QStackedWidget, 
                             QMessageBox, QFrame, QSizePolicy, QFileDialog,
                             QCheckBox, QRadioButton, QButtonGroup, QScrollArea,
                             QGroupBox, QLineEdit, QSlider, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QTime, QUrl
from PyQt5.QtGui import QFont, QColor, QTextCursor, QPalette, QTextFormat
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

class ListeningTestUI(QWidget):
    def __init__(self):
        super().__init__()
        self.subjects = self.load_subjects()
        self.total_time = 40 * 60  # 40 minutes in seconds (includes audio playback + answer time)
        self.time_remaining = self.total_time
        self.current_section = 0  # 0, 1, 2, or 3 for the four sections
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_display)
        self.test_id = "IELTS-CBT-" + "".join([str(i) for i in range(10)])  # Test ID like official test
        self.test_started = False
        
        # Media player for audio playback
        self.media_player = QMediaPlayer()
        self.media_player.stateChanged.connect(self.handle_media_state_change)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        
        # Current audio state
        self.current_audio_file = ""
        self.current_audio_duration = 0
        self.is_playing = False
        
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
            QLineEdit {
                background-color: white;
                border: 1px solid #c0c0c0;
                padding: 2px 4px;
            }
            QProgressBar {
                border: 1px solid #c0c0c0;
                border-radius: 2px;
                text-align: center;
                background: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)

    def load_subjects(self, filename="subjects.json"):
        try:
            with open(filename, 'r') as f:
                subjects_data = json.load(f)
            # Ensure listening section exists with defaults
            if "listening_subjects" not in subjects_data:
                subjects_data["listening_subjects"] = []
            return subjects_data
        except FileNotFoundError:
            print(f"Error: {filename} not found.")
            # Return default structure on error
            return {"listening_subjects": []}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {filename}.")
            # Return default structure on error
            return {"listening_subjects": []}

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
        
        # Section tabs in the center
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(1)
        
        self.section_tabs = []
        for i in range(4):
            tab = QPushButton(f"Section {i+1}")
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
            self.section_tabs.append(tab)
            tab.clicked.connect(lambda checked, idx=i: self.switch_section(idx))
            tab_layout.addWidget(tab)
        
        self.section_tabs[0].setChecked(True)
        
        # Timer display - right aligned like official test
        self.timer_label = QLabel("40:00")
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

        # --- Test selection bar ---
        test_bar = QWidget()
        test_bar.setStyleSheet("background-color: #e8e8e8;")
        test_bar.setFixedHeight(40)
        test_layout = QHBoxLayout(test_bar)
        
        # Test selection
        test_label = QLabel("Select listening test:")
        self.test_combo = QComboBox()
        self.test_combo.setMinimumWidth(300)
        
        # Connect test selection to load content
        self.test_combo.currentIndexChanged.connect(self.load_selected_test)
        
        test_layout.addWidget(test_label)
        test_layout.addWidget(self.test_combo)
        test_layout.addStretch()
        
        main_layout.addWidget(test_bar)

        # --- Audio control bar ---
        audio_bar = QWidget()
        audio_bar.setStyleSheet("background-color: #e0e0e0; border-bottom: 1px solid #c0c0c0;")
        audio_bar.setFixedHeight(60)
        audio_layout = QHBoxLayout(audio_bar)
        
        # Audio controls
        self.play_button = QPushButton("Play")
        self.play_button.setIcon(self.style().standardIcon(self.style().SP_MediaPlay))
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setEnabled(False)  # Disabled until test starts
        
        # Progress bar for audio
        self.audio_progress = QProgressBar()
        self.audio_progress.setTextVisible(True)
        self.audio_progress.setFormat("%v:%s / %m:%s")
        
        # Time display
        self.audio_time_label = QLabel("00:00 / 00:00")
        
        # Section info
        self.section_info_label = QLabel("Section 1: Everyday social contexts")
        self.section_info_label.setStyleSheet("font-weight: bold;")
        
        audio_layout.addWidget(self.section_info_label)
        audio_layout.addStretch()
        audio_layout.addWidget(self.play_button)
        audio_layout.addWidget(self.audio_progress)
        audio_layout.addWidget(self.audio_time_label)
        
        main_layout.addWidget(audio_bar)

        # --- Main Content Area ---
        self.sections_stack = QStackedWidget()
        main_layout.addWidget(self.sections_stack, 1)  # Give this widget more space

        # --- Create Section Widgets ---
        for section_idx in range(4):
            section_widget = QWidget()
            section_layout = QVBoxLayout(section_widget)
            section_layout.setContentsMargins(10, 10, 10, 10)
            
            # Section instructions
            instruction_text = ""
            if section_idx == 0:
                instruction_text = "Section 1: Everyday social contexts (e.g., accommodation, transport)"
            elif section_idx == 1:
                instruction_text = "Section 2: Everyday situations (e.g., shopping, local facilities)"
            elif section_idx == 2:
                instruction_text = "Section 3: Educational or training contexts (e.g., course discussion)"
            else:
                instruction_text = "Section 4: Academic subject lecture (e.g., university lecture)"
            
            instruction_label = QLabel(instruction_text)
            instruction_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
            
            section_layout.addWidget(instruction_label)
            
            # Create scrollable area for questions
            questions_area = QScrollArea()
            questions_area.setWidgetResizable(True)
            questions_area.setStyleSheet("background-color: white;")
            
            questions_content = QWidget()
            questions_layout = QVBoxLayout(questions_content)
            
            # Add placeholder questions for this section
            questions_container = QWidget()
            questions_container_layout = QVBoxLayout(questions_container)
            questions_container_layout.setContentsMargins(0, 0, 0, 0)
            questions_container_layout.setSpacing(15)
            
            # Each section has 10 questions
            for q_idx in range(10):
                q_number = q_idx + 1 + (section_idx * 10)
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
                setattr(self, f"q_text_{section_idx}_{q_idx}", q_text)
                setattr(self, f"q_input_{section_idx}_{q_idx}", q_input)
                
                questions_container_layout.addWidget(q_container)
            
            questions_layout.addWidget(questions_container)
            questions_layout.addStretch()
            
            questions_area.setWidget(questions_content)
            section_layout.addWidget(questions_area)
            
            self.sections_stack.addWidget(section_widget)
        
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
        nav_label = QLabel("Audio will play only once. Make sure your headphones are working properly.")
        nav_label.setStyleSheet("font-style: italic; color: #666;")
        nav_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        status_layout.addWidget(self.completion_label)
        status_layout.addStretch()
        status_layout.addWidget(nav_label)
        
        main_layout.addWidget(status_bar)
        
        # Set the main layout
        self.setLayout(main_layout)
        
        # Initialize with sample content
        self.update_test_options()
        
        # Show first section initially
        self.switch_section(0)

    def switch_section(self, index):
        """Switch between listening sections"""
        self.sections_stack.setCurrentIndex(index)
        self.current_section = index
        
        # Update tab states
        for idx, tab in enumerate(self.section_tabs):
            tab.setChecked(idx == index)
            
        # Update section info label
        section_info = ["Everyday social contexts", 
                        "Everyday situations", 
                        "Educational or training contexts", 
                        "Academic subject lecture"]
        self.section_info_label.setText(f"Section {index + 1}: {section_info[index]}")
        
        # Update completion count
        self.update_completion_count()

    def update_completion_count(self):
        """Update the completion count based on filled answers"""
        filled_count = 0
        total_count = 40  # IELTS listening test has 40 questions
        
        # Iterate through all question inputs
        for section_idx in range(4):
            for q_idx in range(10):
                q_input = getattr(self, f"q_input_{section_idx}_{q_idx}", None)
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
                QMessageBox.warning(self, "Time Alert", "10 minutes remaining for the Listening test.")
            elif self.time_remaining == 300:  # 5 minutes left
                QMessageBox.warning(self, "Time Alert", "5 minutes remaining for the Listening test.")
        else:
            self.timer.stop()
            self.timer_label.setText("00:00")
            self.timer_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
            
            # Stop audio if playing
            if self.is_playing:
                self.media_player.stop()
                self.is_playing = False
                self.play_button.setText("Play")
                self.play_button.setIcon(self.style().standardIcon(self.style().SP_MediaPlay))
                
            # Disable editing when time is up
            for section_idx in range(4):
                for q_idx in range(10):
                    q_input = getattr(self, f"q_input_{section_idx}_{q_idx}", None)
                    if q_input:
                        q_input.setReadOnly(True)
            
            # Alert user
            QMessageBox.critical(self, "Time's Up", "Your Listening test time has ended. Your responses have been saved.")
            
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

    def update_test_options(self):
        """Update listening test options"""
        self.test_combo.clear()
        listening_subjects = self.subjects.get("listening_subjects", [])
        
        # Add placeholder if no subjects available
        if not listening_subjects:
            placeholder_subjects = [
                "City Accommodation Tour",
                "Community Center Programs",
                "University Orientation Meeting",
                "Lecture on Environmental Science"
            ]
            self.test_combo.addItems(placeholder_subjects)
        else:
            self.test_combo.addItems(listening_subjects)
        
        # Load the first subject
        if self.test_combo.count() > 0:
            self.load_selected_test()

    def load_selected_test(self):
        """Load the selected listening test"""
        current_test = self.test_combo.currentText()
        if not current_test:
            return
            
        # For now we'll generate placeholder content
        # In a real app, you would load the actual content from a database or file
        
        # Update all sections with sample questions
        question_types = [
            "Complete the note. Write ONE WORD ONLY:",
            "Choose the correct letter (A, B or C):",
            "Complete the sentence. Write NO MORE THAN TWO WORDS:",
            "Answer the question. Write NO MORE THAN THREE WORDS:",
            "What is the correct answer?"
        ]
        
        for section_idx in range(4):
            for q_idx in range(10):
                q_number = q_idx + 1 + (section_idx * 10)
                q_text = getattr(self, f"q_text_{section_idx}_{q_idx}")
                
                # Generate a sample question
                question_type = question_types[q_idx % len(question_types)]
                
                # Generate context based on section
                contexts = [
                    ["phone call", "rental inquiry", "transportation", "schedule", "directions", 
                     "accommodation", "booking", "registration", "personal details", "contact information"],
                    ["local event", "community service", "public facility", "tourist information",
                     "shopping center", "restaurant", "gym membership", "library service", 
                     "local transportation", "community event"],
                    ["course requirements", "assignment details", "project deadlines", "study resources",
                     "group work", "academic performance", "tutor feedback", "course modules",
                     "research methods", "academic support"],
                    ["scientific research", "historical development", "technological innovation",
                     "economic theory", "psychological concept", "environmental issue",
                     "medical advancement", "social phenomenon", "literary analysis", "mathematical principle"]
                ]
                
                context = contexts[section_idx][q_idx]
                question_content = f"Based on the conversation about {context}, what is the main requirement?"
                
                q_text.setText(f"Question {q_number}: {question_type} {question_content}")

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
            
            # Disable test selection
            self.test_combo.setEnabled(False)
            
            # Enable play button
            self.play_button.setEnabled(True)
            
            # Show confirmation
            QMessageBox.information(self, "Test Started", 
                                   "The IELTS Listening test has started. You will have approximately 30 minutes " +
                                   "to listen to all recordings and 10 minutes to transfer your answers.")
        else:
            # Confirm before stopping
            reply = QMessageBox.question(self, "End Test", 
                                        "Are you sure you want to end the test? This would be equivalent to submitting your answers early.",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Stop the test
                self.test_started = False
                self.timer.stop()
                
                # Stop audio if playing
                if self.is_playing:
                    self.media_player.stop()
                    self.is_playing = False
                    self.play_button.setText("Play")
                    self.play_button.setIcon(self.style().standardIcon(self.style().SP_MediaPlay))
                
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
                
                # Disable play button
                self.play_button.setEnabled(False)
                
                # Re-enable test selection
                self.test_combo.setEnabled(True)
                
                # Show test completion message
                self.show_test_summary()

    def toggle_playback(self):
        """Play or pause the audio"""
        if not self.is_playing:
            # Start playback
            if not self.current_audio_file:
                # If no audio file loaded, create a sample one
                self.load_audio_for_section(self.current_section)
                
            self.media_player.play()
            self.is_playing = True
            self.play_button.setText("Pause")
            self.play_button.setIcon(self.style().standardIcon(self.style().SP_MediaPause))
        else:
            # Pause playback - Note: In a real IELTS test, pausing is not allowed
            self.media_player.pause()
            self.is_playing = False
            self.play_button.setText("Play")
            self.play_button.setIcon(self.style().standardIcon(self.style().SP_MediaPlay))

    def load_audio_for_section(self, section_idx):
        """Load the audio file for the current section"""
        # In a real app, you would load actual audio files
        # For this simulation, we'll just pretend to load audio
        
        # Simulate having audio files
        audio_names = ["conversation", "information_broadcast", "tutorial_discussion", "academic_lecture"]
        
        # Simulate loading file
        self.current_audio_file = f"section_{section_idx+1}_{audio_names[section_idx]}.mp3"
        
        # Since we don't have actual audio files, we'll just set up a simulated duration
        # In a real app, this would come from the audio file metadata
        self.current_audio_duration = 7 * 60 * 1000  # 7 minutes in milliseconds
        
        # Set up the media player with a blank media
        # In a real app, you would use a real audio file URL
        self.media_player.setMedia(QMediaContent())
        
        # For simulation, manually set the progress bar values
        self.audio_progress.setRange(0, self.current_audio_duration)
        self.audio_progress.setValue(0)
        
        # For simulation, update the time label
        minutes = self.current_audio_duration / 60000
        self.audio_time_label.setText(f"00:00 / {int(minutes):02d}:00")

    def handle_media_state_change(self, state):
        """Handle media player state changes"""
        # In a real app, this would update UI based on actual media state
        if state == QMediaPlayer.EndOfMedia:
            # Audio finished playing
            self.is_playing = False
            self.play_button.setText("Play")
            self.play_button.setIcon(self.style().standardIcon(self.style().SP_MediaPlay))
            
            # Reset progress
            self.audio_progress.setValue(0)
            
            # Move to next section if not the last one
            if self.current_section < 3:
                next_section = self.current_section + 1
                # Show a message before moving to next section
                QMessageBox.information(self, "Section Complete", 
                                        f"Section {self.current_section + 1} complete. Moving to Section {next_section + 1}.")
                self.switch_section(next_section)
                # Load audio for next section
                self.load_audio_for_section(next_section)
            else:
                # All sections complete
                QMessageBox.information(self, "Listening Complete", 
                                       "All listening sections complete. You have 10 minutes to check and finalize your answers.")

    def update_position(self, position):
        """Update the audio progress bar position"""
        # In a real app, this would use the actual media position
        self.audio_progress.setValue(position)
        
        # Update time display
        seconds = (position / 1000) % 60
        minutes = (position / 60000)
        time_str = f"{int(minutes):02d}:{int(seconds):02d}"
        
        total_seconds = (self.current_audio_duration / 1000) % 60
        total_minutes = (self.current_audio_duration / 60000)
        total_time_str = f"{int(total_minutes):02d}:{int(total_seconds):02d}"
        
        self.audio_time_label.setText(f"{time_str} / {total_time_str}")

    def update_duration(self, duration):
        """Update when media duration changes"""
        # In a real app, this would update based on the actual media duration
        self.audio_progress.setRange(0, duration)
        
        # Update the max time display
        seconds = (duration / 1000) % 60
        minutes = (duration / 60000)
        time_str = f"{int(minutes):02d}:{int(seconds):02d}"
        
        self.audio_time_label.setText(f"00:00 / {time_str}")
        
        # Store the duration
        self.current_audio_duration = duration

    def show_test_summary(self):
        """Show a summary of the test when completed"""
        completed_count = 0
        total_count = 40
        
        # Count completed questions
        for section_idx in range(4):
            for q_idx in range(10):
                q_input = getattr(self, f"q_input_{section_idx}_{q_idx}", None)
                if q_input and q_input.text().strip():
                    completed_count += 1
        
        # Prepare summary message
        summary = f"Listening Test Completed\n\n"
        summary += f"Questions Answered: {completed_count}/{total_count}\n\n"
        summary += "Your responses have been saved.\n"
        summary += "In the official test, your answers would now be submitted for marking."
        
        QMessageBox.information(self, "Test Summary", summary)

    def show_help(self):
        """Show help information about the test"""
        help_text = """
IELTS Listening Test Help

Test Duration: Approximately 40 minutes
- 30 minutes to listen to the recording and answer questions
- 10 minutes to transfer answers to the answer sheet (not needed in computer-based test)

Test Format:
- 4 sections with 10 questions each (40 questions total)
- Section 1: A conversation between two people in an everyday social context
- Section 2: A monologue in an everyday social context
- Section 3: A conversation between up to four people in an educational context
- Section 4: A monologue on an academic subject

Important Notes:
- Each recording is played ONCE only
- Ensure your headphones are working properly before starting
- Read the questions before the audio starts for each section
- Questions follow the order of the audio
- Pay attention to word limits in your answers (e.g., "ONE WORD ONLY")
- Spelling and grammar count in your answers

Question Types:
- Multiple choice
- Matching
- Plan/map/diagram labeling
- Form/note/table/flow-chart/summary completion
- Sentence completion
- Short-answer questions

Scoring:
- Each correct answer receives 1 mark
- Scores out of 40 are converted to the IELTS 9-band scale
"""
        QMessageBox.information(self, "Help", help_text)

    def export_answers(self):
        """Export answers to a text file"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Listening Test Answers", 
            f"IELTS_Listening_Test_{self.test_id}.txt",
            "Text Files (*.txt)", options=options)
            
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    f.write(f"IELTS LISTENING TEST\n")
                    f.write(f"Test ID: {self.test_id}\n")
                    f.write(f"Test: {self.test_combo.currentText()}\n\n")
                    
                    for section_idx in range(4):
                        section_names = ["Social Context", "Everyday Situation", 
                                        "Educational Context", "Academic Lecture"]
                        
                        f.write(f"SECTION {section_idx + 1}: {section_names[section_idx]}\n\n")
                        
                        for q_idx in range(10):
                            q_number = q_idx + 1 + (section_idx * 10)
                            q_text = getattr(self, f"q_text_{section_idx}_{q_idx}")
                            q_input = getattr(self, f"q_input_{section_idx}_{q_idx}")
                            
                            question = q_text.text().replace("Question ", "", 1)
                            answer = q_input.text()
                            
                            f.write(f"{q_number}. {question}\n")
                            f.write(f"   Answer: {answer}\n\n")
                
                QMessageBox.information(self, "Export Successful", f"Answers saved to {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error saving file: {str(e)}") 