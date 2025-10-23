import json
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QSplitter, QComboBox, QPushButton, QStackedWidget, 
                             QMessageBox, QFrame, QSizePolicy, QFileDialog,
                             QCheckBox, QRadioButton, QButtonGroup, QScrollArea,
                             QGroupBox, QLineEdit, QSlider, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QTime, QUrl, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCursor, QPalette, QTextFormat, QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWebEngineWidgets import QWebEngineView

class ListeningTestUI(QWidget):
    def __init__(self):
        super().__init__()
        self.subjects = self.load_subjects()
        self.total_time = 35 * 60  # 35 minutes in seconds
        self.time_remaining = self.total_time
        self.current_section = 0  # 0, 1, 2, or 3 for the four sections
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_display)
        self.test_started = False
        
        # Completion counter timer for real-time updates
        self.completion_timer = QTimer(self)
        self.completion_timer.timeout.connect(self.update_completion_count)
        self.completion_timer.start(1000)  # Update every second
        
        # Preview timer for sections
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.update_preview_timer)
        self.preview_time = 0
        self.in_preview_mode = False
        
        # Review period timer
        self.review_timer = QTimer(self)
        self.review_timer.timeout.connect(self.update_review_timer)
        self.review_time = 120
        self.in_review_mode = False
        
        # Media player for audio playback
        self.media_player = QMediaPlayer()
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        
        # Current audio state
        self.current_audio_file = ""
        self.current_audio_duration = 0
        self.is_playing = False
        
        # Apply authentic IELTS CBT style
        self.apply_ielts_cbt_style()
        self.initUI()

    def apply_ielts_cbt_style(self):
        """Apply authentic IELTS CBT styling to match the official interface"""
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                font-family: Arial, sans-serif;
                font-size: 12px;
                color: #333333;
            }
            
            /* Merged top bar styling */
            #merged_top_bar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 8px 15px;
            }
            
            /* Section tabs at bottom */
            #section_tabs {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                padding: 5px 15px;
            }
            
            /* Navigation area */
            #navigation_area {
                background-color: #ffffff;
                padding: 10px 15px;
                border-top: 1px solid #dee2e6;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 12px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
            
            /* Navigation buttons */
            QPushButton#nav_button {
                background-color: #007bff;
                color: white;
                border-color: #007bff;
                font-weight: bold;
                min-width: 80px;
                padding: 8px 16px;
            }
            QPushButton#nav_button:hover {
                background-color: #0056b3;
                border-color: #004085;
            }
            QPushButton#nav_button:disabled {
                background-color: #6c757d;
                border-color: #6c757d;
                color: #ffffff;
            }
            
            /* Section tab buttons */
            QPushButton.section_tab {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 3px 3px 0 0;
            }
            QPushButton.section_tab:checked {
                background-color: #007bff;
                color: white;
                border-color: #007bff;
            }
            QPushButton.section_tab:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
                border-color: #dee2e6;
            }
            
            /* Start test button */
            QPushButton#start_test_button {
                background-color: #007bff;
                color: white;
                border-color: #007bff;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton#start_test_button:hover {
                background-color: #0056b3;
                border-color: #004085;
            }
            
            /* Timer label */
            QLabel#timer_label {
                font-size: 14px;
                font-weight: bold;
                color: #dc3545;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 4px 8px;
                border-radius: 3px;
            }
            
            /* Top bar labels with gray background */
            QLabel#top_bar_label {
                font-size: 13px;
                color: #333333;
                background-color: #f8f9fa;
                font-weight: bold;
            }
            
            /* Completion counter */
            QLabel#completion_label {
                font-size: 11px;
                color: #6c757d;
                font-style: italic;
                background-color: #f8f9fa;
            }
            
            /* Combo boxes */
            QComboBox {
                background-color: white;
                border: 1px solid #ced4da;
                padding: 4px 8px;
                border-radius: 3px;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #007bff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #6c757d;
                margin-right: 5px;
            }
            
            /* Web view - full width */
            QWebEngineView {
                border: none;
                background-color: white;
            }
        """)

    def initUI(self):
        """Initialize the authentic IELTS CBT user interface"""
        # Main layout - vertical stack
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === MERGED TOP BAR ===
        merged_top_bar = QWidget()
        merged_top_bar.setObjectName("merged_top_bar")
        merged_top_bar.setFixedHeight(50)
        top_bar_layout = QHBoxLayout(merged_top_bar)
        top_bar_layout.setContentsMargins(15, 8, 15, 8)
        
        # Title
        title_label = QLabel("Cambridge IELTS Academic Listening Test")
        title_label.setObjectName("top_bar_label")
        
        # Cambridge book selection
        book_label = QLabel("Book:")
        book_label.setObjectName("top_bar_label")
        self.book_combo = QComboBox()
        self.book_combo.addItems(["Cambridge 20", "Cambridge 19"])
        self.book_combo.setMinimumWidth(120)
        self.book_combo.currentTextChanged.connect(self.update_test_options)
        
        # Test selection
        test_label = QLabel("Test:")
        test_label.setObjectName("top_bar_label")
        self.test_combo = QComboBox()
        self.test_combo.setMinimumWidth(150)
        self.test_combo.currentIndexChanged.connect(self.load_selected_test)
        
        # Timer (center-right)
        self.timer_label = QLabel("35:00")
        self.timer_label.setObjectName("timer_label")
        
        # Start test button
        self.start_test_button = QPushButton("Start Test")
        self.start_test_button.setObjectName("start_test_button")
        self.start_test_button.clicked.connect(self.toggle_test)
        
        # Layout merged top bar
        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(book_label)
        top_bar_layout.addWidget(self.book_combo)
        top_bar_layout.addWidget(test_label)
        top_bar_layout.addWidget(self.test_combo)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.timer_label)
        top_bar_layout.addWidget(self.start_test_button)
        
        main_layout.addWidget(merged_top_bar)

        # === MAIN CONTENT AREA (100% width for HTML) ===
        # Create a stacked widget to hold both the protection overlay and web view
        self.content_stack = QStackedWidget()
        
        # Create web view for displaying HTML content - takes all available space, edge-to-edge
        self.web_view = QWebEngineView()
        
        # Create protection overlay with guidance card
        self.protection_overlay = self.create_protection_overlay()
        
        # Add both to the stack (overlay first, so it shows by default)
        self.content_stack.addWidget(self.protection_overlay)
        self.content_stack.addWidget(self.web_view)
        
        # Show protection overlay by default
        self.content_stack.setCurrentWidget(self.protection_overlay)
        
        main_layout.addWidget(self.content_stack, 1)  # Stretch factor 1 = takes all remaining space

        # === BOTTOM SECTION TABS ===
        section_tabs_widget = QWidget()
        section_tabs_widget.setObjectName("section_tabs")
        section_tabs_widget.setFixedHeight(40)
        section_tabs_layout = QHBoxLayout(section_tabs_widget)
        section_tabs_layout.setContentsMargins(15, 5, 15, 5)
        
        # Section navigation tabs
        self.section_tabs = []
        for i in range(4):
            tab = QPushButton(f"Section {i+1}")
            tab.setObjectName("section_tab")
            tab.setProperty("class", "section_tab")
            tab.setCheckable(True)
            tab.setEnabled(False)  # Initially disabled
            tab.clicked.connect(lambda checked, idx=i: self.switch_section(idx))
            self.section_tabs.append(tab)
            section_tabs_layout.addWidget(tab)
        
        # Enable first section
        self.section_tabs[0].setChecked(True)
        self.section_tabs[0].setEnabled(True)
        
        section_tabs_layout.addStretch()
        
        # Completion counter
        self.completion_label = QLabel("Completed: 0/40 questions")
        self.completion_label.setObjectName("completion_label")
        section_tabs_layout.addWidget(self.completion_label)
        
        main_layout.addWidget(section_tabs_widget)

        # === NAVIGATION AREA ===
        navigation_widget = QWidget()
        navigation_widget.setObjectName("navigation_area")
        navigation_widget.setFixedHeight(50)
        nav_layout = QHBoxLayout(navigation_widget)
        nav_layout.setContentsMargins(15, 10, 15, 10)
        
        # Add stretch to push buttons to the right
        nav_layout.addStretch()
        
        # Back button
        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("nav_button")
        self.back_button.clicked.connect(self.go_to_previous_section)
        self.back_button.setEnabled(False)  # Initially disabled
        nav_layout.addWidget(self.back_button)
        
        # Next button
        self.next_button = QPushButton("Next →")
        self.next_button.setObjectName("nav_button")
        self.next_button.clicked.connect(self.go_to_next_section)
        nav_layout.addWidget(self.next_button)
        
        main_layout.addWidget(navigation_widget)

        # Initialize test options
        self.update_test_options()

    def create_protection_overlay(self):
        """Create the protection overlay with IELTS guidance card and audio test"""
        overlay = QWidget()
        overlay.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout(overlay)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)
        
        # Add vertical stretch to center content
        layout.addStretch()
        
        # Main guidance card
        guidance_card = QFrame()
        guidance_card.setFrameStyle(QFrame.Box)
        guidance_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #007bff;
                border-radius: 10px;
                padding: 30px;
            }
        """)
        guidance_card.setMaximumWidth(800)
        guidance_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        card_layout = QVBoxLayout(guidance_card)
        card_layout.setSpacing(20)
        
        # Title
        title = QLabel("IELTS Listening Test Instructions")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
                text-align: center;
                margin-bottom: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("""
<div style="font-size: 14px; line-height: 1.6; color: #333;">
<p><strong>Before you begin:</strong></p>
<ul style="margin-left: 20px;">
<li>You will hear each recording <strong>ONLY ONCE</strong></li>
<li>The test has <strong>4 sections</strong> with a total of <strong>40 questions</strong></li>
<li>You have <strong>35 minutes</strong> to complete the test</li>
<li>Write your answers directly in the answer boxes</li>
<li>At the end, you will have time to transfer your answers</li>
</ul>

<p><strong>Audio Test:</strong></p>
<p>Before starting, please test your headphones using the audio test below to ensure you can hear clearly.</p>

<p><strong>When you are ready to begin, click "Start Test" to proceed.</strong></p>
</div>
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                border: 1px solid #dee2e6;
            }
        """)
        card_layout.addWidget(instructions)
        
        # Audio test section
        audio_test_frame = QFrame()
        audio_test_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        audio_layout = QHBoxLayout(audio_test_frame)
        
        audio_label = QLabel("Audio Test:")
        audio_label.setStyleSheet("font-weight: bold; color: #1976d2;")
        
        self.audio_test_button = QPushButton("🔊 Test Audio")
        self.audio_test_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.audio_test_button.clicked.connect(self.play_audio_test)
        
        self.audio_status_label = QLabel("Click to test your audio")
        self.audio_status_label.setStyleSheet("color: #666; font-style: italic;")
        
        audio_layout.addWidget(audio_label)
        audio_layout.addWidget(self.audio_test_button)
        audio_layout.addWidget(self.audio_status_label)
        audio_layout.addStretch()
        
        card_layout.addWidget(audio_test_frame)
        
        # Start test button (large and prominent)
        self.start_actual_test_button = QPushButton("Start Test")
        self.start_actual_test_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 15px 40px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.start_actual_test_button.clicked.connect(self.start_actual_test)
        card_layout.addWidget(self.start_actual_test_button, 0, Qt.AlignCenter)
        
        # Center the guidance card
        card_container = QHBoxLayout()
        card_container.addStretch()
        card_container.addWidget(guidance_card)
        card_container.addStretch()
        
        layout.addLayout(card_container)
        layout.addStretch()
        
        return overlay

    def load_subjects(self):
        """Load test subjects from JSON file"""
        try:
            subjects_file = os.path.join(os.path.dirname(__file__), '..', 'resources', 'subjects.json')
            if os.path.exists(subjects_file):
                with open(subjects_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading subjects: {e}")
        
        # Return default structure if file doesn't exist
        return {
            "listening": {
                "Cambridge 20": {
                    "Test 1": {"sections": 4, "questions": 40},
                    "Test 2": {"sections": 4, "questions": 40},
                    "Test 3": {"sections": 4, "questions": 40},
                    "Test 4": {"sections": 4, "questions": 40}
                },
                "Cambridge 19": {
                    "Test 1": {"sections": 4, "questions": 40},
                    "Test 2": {"sections": 4, "questions": 40},
                    "Test 3": {"sections": 4, "questions": 40},
                    "Test 4": {"sections": 4, "questions": 40}
                }
            }
        }

    def update_test_options(self):
        """Update test options based on selected Cambridge book"""
        selected_book = self.book_combo.currentText()
        self.test_combo.clear()
        
        if selected_book in self.subjects.get("listening", {}):
            tests = list(self.subjects["listening"][selected_book].keys())
            self.test_combo.addItems(tests)

    def load_selected_test(self):
        """Load the selected test and display first section"""
        if self.test_combo.currentText():
            # Load HTML for first section
            self.load_html_for_section(0)
            # Load audio for first section
            self.load_audio_for_section(0)
            # Reset section tabs
            for i, tab in enumerate(self.section_tabs):
                tab.setEnabled(i == 0)  # Only enable first section initially
                tab.setChecked(i == 0)
            self.current_section = 0

    def load_html_for_section(self, section_index):
        """Load HTML file for specific section"""
        try:
            # Get current test selection
            current_test = self.test_combo.currentText()
            if not current_test:
                return
            
            # Extract test number (e.g., "Test 1" -> "1")
            test_number = current_test.split()[-1]
            
            # Construct HTML file path
            html_file = f"Test-{test_number}-Part-{section_index + 1}.html"
            html_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'resources', 
                'Cambridge20', 
                'listening', 
                html_file
            )
            
            if os.path.exists(html_path):
                # Load HTML file into web view
                file_url = QUrl.fromLocalFile(os.path.abspath(html_path))
                self.web_view.load(file_url)
                print(f"Loaded HTML: {html_path}")
            else:
                print(f"HTML file not found: {html_path}")
                # Load default content
                self.web_view.setHtml(f"""
                <html>
                <head>
                    <title>IELTS Listening Test</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 20px; }}
                        .header {{ background: #4285F4; color: white; padding: 15px; margin-bottom: 20px; }}
                        .section {{ margin-bottom: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>IELTS Listening</h2>
                        <p>{current_test} - Section {section_index + 1} Questions {section_index * 10 + 1}-{(section_index + 1) * 10}</p>
                    </div>
                    <div class="section">
                        <h3>Section {section_index + 1}</h3>
                        <p>Questions {section_index * 10 + 1}-{(section_index + 1) * 10}</p>
                        <p>HTML content for this section will be loaded here.</p>
                    </div>
                </body>
                </html>
                """)
        except Exception as e:
            print(f"Error loading HTML for section {section_index}: {e}")

    def load_audio_for_section(self, section_index):
        """Load audio file for specific section"""
        try:
            # Get current test selection
            current_test = self.test_combo.currentText()
            if not current_test:
                return
            
            # Extract test number (e.g., "Test 1" -> "1")
            test_number = current_test.split()[-1]
            
            # Construct audio file path based on actual file structure
            audio_file = f"Test-{test_number}-Part-{section_index + 1}.mp3"
            audio_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'resources', 
                'Cambridge20', 
                'listening', 
                audio_file
            )
            
            if os.path.exists(audio_path):
                # Set up media player
                media_content = QMediaContent(QUrl.fromLocalFile(os.path.abspath(audio_path)))
                self.media_player.setMedia(media_content)
                self.current_audio_file = audio_path
                print(f"Loaded audio: {audio_path}")
            else:
                print(f"Audio file not found: {audio_path}")
                
        except Exception as e:
            print(f"Error loading audio for section {section_index}: {e}")

    def switch_section(self, index):
        """Switch to a different section"""
        if index < 0 or index >= 4:
            return
        
        # Update current section
        self.current_section = index
        
        # Update section tab states
        for i, tab in enumerate(self.section_tabs):
            tab.setChecked(i == index)
        
        # Load HTML and audio for the section
        self.load_html_for_section(index)
        self.load_audio_for_section(index)
        
        # Auto-play audio if test is started (simulate real IELTS exam)
        if self.test_started and self.media_player.state() != QMediaPlayer.PlayingState:
            self.media_player.play()
        
        # Update completion count and navigation buttons
        self.update_completion_count()
        self.update_navigation_buttons()

    def go_to_previous_section(self):
        """Navigate to the previous section"""
        if self.current_section > 0:
            self.switch_section(self.current_section - 1)

    def go_to_next_section(self):
        """Navigate to the next section"""
        if self.current_section < 3:
            self.switch_section(self.current_section + 1)

    def update_navigation_buttons(self):
        """Update the state of navigation buttons"""
        self.back_button.setEnabled(self.current_section > 0)
        self.next_button.setEnabled(self.current_section < 3)



    def update_position(self, position):
        """Update audio position (for future progress tracking)"""
        pass

    def update_duration(self, duration):
        """Update audio duration"""
        self.current_audio_duration = duration

    def play_audio_test(self):
        """Play a simple audio test for headphone checking"""
        try:
            # Create a simple test audio file path (we'll use a system sound or create a simple tone)
            # For now, let's create a simple beep sound programmatically
            import tempfile
            import wave
            import math
            import struct
            
            # Create a simple 1-second beep at 440Hz (A note)
            sample_rate = 44100
            duration = 1.0
            frequency = 440.0
            
            # Generate sine wave
            frames = int(duration * sample_rate)
            audio_data = []
            for i in range(frames):
                value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                audio_data.append(struct.pack('<h', value))
            
            # Create temporary WAV file
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes per sample
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(b''.join(audio_data))
            
            # Play the test audio
            test_url = QUrl.fromLocalFile(temp_file.name)
            self.media_player.setMedia(QMediaContent(test_url))
            self.media_player.play()
            
            # Update status
            self.audio_status_label.setText("🔊 Playing test audio...")
            self.audio_test_button.setText("Playing...")
            self.audio_test_button.setEnabled(False)
            
            # Re-enable button after 2 seconds
            QTimer.singleShot(2000, self.reset_audio_test_button)
            
        except Exception as e:
            print(f"Error playing audio test: {e}")
            self.audio_status_label.setText("❌ Audio test failed")
    
    def reset_audio_test_button(self):
        """Reset the audio test button after playing"""
        self.audio_test_button.setText("🔊 Test Audio")
        self.audio_test_button.setEnabled(True)
        self.audio_status_label.setText("✅ Audio test completed")
    
    def start_actual_test(self):
        """Start the actual test by hiding overlay and showing web view"""
        # Switch to web view
        self.content_stack.setCurrentWidget(self.web_view)
        
        # Start the timer
        if not self.test_started:
            self.test_started = True
            self.timer.start(1000)  # Update every second
            self.start_test_button.setText("End Test")
            self.start_test_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border-color: #dc3545;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                    border-color: #bd2130;
                }
            """)
            
            # Enable section tabs
            for tab in self.section_tabs:
                tab.setEnabled(True)
            
            # Load the first test
            self.load_selected_test()
            
            # Load audio for first section
            self.load_audio_for_section(0)
            
            # Auto-play audio (simulate real IELTS exam)
            if self.media_player.state() != QMediaPlayer.PlayingState:
                self.media_player.play()

    def toggle_test(self):
        """End the test (start is now handled by protection overlay)"""
        if self.test_started:
            # Stop test
            reply = QMessageBox.question(self, 'End Test', 
                                       'Are you sure you want to end the test?\n\n'
                                       'Your progress will be saved and you can review your answers.',
                                       QMessageBox.Yes | QMessageBox.No, 
                                       QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.timer.stop()
                self.media_player.stop()
                self.test_started = False
                self.start_test_button.setText("Start Test")
                self.start_test_button.setStyleSheet("")  # Reset to default style
                
                # Show protection overlay again
                self.content_stack.setCurrentWidget(self.protection_overlay)
                
                # Reset section tabs
                for i, tab in enumerate(self.section_tabs):
                    if i == 0:
                        tab.setEnabled(True)
                        tab.setChecked(True)
                    else:
                        tab.setEnabled(False)
                        tab.setChecked(False)
                
                self.show_test_summary()
        else:
            # If test hasn't started, this shouldn't happen with the new system
            # But just in case, show a message
            QMessageBox.information(self, "Test Not Started", 
                                  "Please use the 'Start Test' button in the instructions to begin the test.")

    def update_timer_display(self):
        """Update the timer display"""
        if self.time_remaining > 0:
            self.time_remaining -= 1
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
        else:
            # Time's up
            self.timer.stop()
            self.media_player.stop()
            self.test_started = False
            self.start_test_button.setText("Start Test")
            QMessageBox.information(self, "Time's Up", "The listening test time has ended.")
            self.show_test_summary()

    def update_completion_count(self):
        """Update completion count with real-time JavaScript integration"""
        if hasattr(self, 'web_view') and self.web_view.page():
            # Execute JavaScript to count filled inputs
            js_code = """
            (function() {
                var inputs = document.querySelectorAll('.answer-blank');
                var completed = 0;
                var total = inputs.length;
                
                inputs.forEach(function(input) {
                    if (input.value && input.value.trim() !== '') {
                        completed++;
                    }
                });
                
                return {completed: completed, total: total};
            })();
            """
            
            def handle_result(result):
                if result and isinstance(result, dict):
                    completed = result.get('completed', 0)
                    total = result.get('total', 10)  # Default to 10 for each section
                    # Calculate total across all sections (40 questions total)
                    section_completed = completed
                    total_questions = 40
                    self.completion_label.setText(f"Completed: {section_completed}/{total} questions (Section {self.current_section + 1})")
                else:
                    self.completion_label.setText(f"Completed: 0/10 questions (Section {self.current_section + 1})")
            
            try:
                self.web_view.page().runJavaScript(js_code, handle_result)
            except:
                # Fallback if JavaScript execution fails
                self.completion_label.setText(f"Completed: 0/10 questions (Section {self.current_section + 1})")

    def show_test_summary(self):
        """Show test completion summary"""
        QMessageBox.information(self, "Test Complete", 
                              "Your listening test has been completed.\n\n"
                              "Results will be processed and made available shortly.")



    def start_section_preview(self):
        """Start preview period for a section"""
        self.preview_time = 30  # 30 seconds preview
        self.in_preview_mode = True
        self.preview_timer.start(1000)

    def update_preview_timer(self):
        """Update preview timer"""
        if self.preview_time > 0:
            self.preview_time -= 1
        else:
            self.preview_timer.stop()
            self.in_preview_mode = False

    def update_review_timer(self):
        """Update review timer"""
        if self.review_time > 0:
            self.review_time -= 1
        else:
            self.review_timer.stop()
            self.in_review_mode = False