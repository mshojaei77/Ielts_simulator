import json
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import app_logger
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


        
        # === QUESTION TRACKER (All 40) ===
        self.build_question_tracker(main_layout)

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
                background-color: #fafafa;
            }
        """)
        
        layout = QVBoxLayout(overlay)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # Add vertical stretch to center content
        layout.addStretch()
        
        # Main guidance card
        guidance_card = QFrame()
        guidance_card.setFrameStyle(QFrame.NoFrame)
        guidance_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 24px;
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
                font-size: 20px;
                font-weight: 600;
                color: #111827;
                text-align: center;
                margin-bottom: 6px;
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
                background-color: transparent;
                padding: 4px 0;
                border-radius: 0;
                border: none;
                color: #4b5563;
            }
        """)
        card_layout.addWidget(instructions)
        
        # Audio test section
        audio_test_frame = QFrame()
        audio_test_frame.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        audio_layout = QHBoxLayout(audio_test_frame)
        
        audio_label = QLabel("Audio Test:")
        audio_label.setStyleSheet("font-weight: bold; color: #374151;")
        
        self.audio_test_button = QPushButton("🔊 Test Audio")
        self.audio_test_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #ced4da;
                padding: 8px 14px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
        """)
        self.audio_test_button.clicked.connect(self.play_audio_test)
        
        self.audio_status_label = QLabel("Click to test your audio")
        self.audio_status_label.setStyleSheet("color: #6b7280; font-style: italic;")
        
        audio_layout.addWidget(audio_label)
        audio_layout.addWidget(self.audio_test_button)
        audio_layout.addWidget(self.audio_status_label)
        audio_layout.addStretch()
        
        card_layout.addWidget(audio_test_frame)
        
        # Start test button (large and prominent)
        self.start_actual_test_button = QPushButton("Start Test")
        self.start_actual_test_button.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                border: none;
                padding: 12px 28px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                min-height: 44px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
            QPushButton:pressed {
                background-color: #15803d;
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
                with open(subjects_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            app_logger.debug(f"Error loading subjects: {e}")
        
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

            self.current_section = 0

    def load_html_for_section(self, section_index):
        """Load HTML file for specific section"""
        try:
            # Validate section index
            if not (0 <= section_index <= 3):
                raise ValueError(f"Invalid section index: {section_index}. Must be 0-3.")
            
            # Get current test selection
            current_test = self.test_combo.currentText()
            current_book = self.book_combo.currentText()
            if not current_test or not current_book:
                raise ValueError("No test or book selected")
            
            # Extract test number (e.g., "Test 1" -> "1")
            test_number = current_test.split()[-1]
            
            # Convert book name to folder name (e.g., "Cambridge 20" -> "Cambridge20")
            book_folder = current_book.replace(" ", "")
            
            # Construct HTML file path
            html_file = f"Test-{test_number}-Part-{section_index + 1}.html"
            html_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'resources', 
                book_folder, 
                'listening', 
                html_file
            )
            
            # Validate file exists and is readable
            if not os.path.exists(html_path):
                raise FileNotFoundError(f"HTML file not found: {html_path}")
            
            if not os.path.isfile(html_path):
                raise ValueError(f"Path is not a file: {html_path}")
            
            # Check file size (prevent loading extremely large files)
            file_size = os.path.getsize(html_path)
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError(f"HTML file too large: {file_size} bytes")
            
            # Load HTML file into web view
            file_url = QUrl.fromLocalFile(os.path.abspath(html_path))
            self.web_view.load(file_url)
            app_logger.debug(f"Loaded HTML: {html_path}")
            
        except (FileNotFoundError, ValueError, OSError) as e:
            app_logger.debug(f"Error loading HTML for section {section_index + 1}: {e}")
            # Show user-friendly error in web view
            fallback_html = f"""
            <html>
            <head>
                <title>IELTS Listening Test - Section {section_index + 1}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5; }}
                    .header {{ background: #4285F4; color: white; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                    .error {{ color: #d32f2f; background-color: #ffebee; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .section {{ margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>IELTS Listening</h2>
                    <p>Section {section_index + 1} - Questions {section_index * 10 + 1}-{(section_index + 1) * 10}</p>
                </div>
                <div class="error">
                    <strong>Content not available</strong><br>
                    The content for this section could not be loaded. Please check that the test files are properly installed.
                </div>
                <div class="section">
                    <h3>Section {section_index + 1}</h3>
                    <p>Questions {section_index * 10 + 1}-{(section_index + 1) * 10}</p>
                    <p>Please ensure the HTML files are available in the resources directory.</p>
                </div>
            </body>
            </html>
            """
            self.web_view.setHtml(fallback_html)
        except Exception as e:
            app_logger.debug(f"Unexpected error loading HTML for section {section_index + 1}: {e}")
            # Show generic error in web view
            error_html = f"""
            <html>
            <head>
                <title>Error - Section {section_index + 1}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    .error {{ color: red; background-color: #ffe6e6; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h2>Error Loading Section {section_index + 1}</h2>
                <div class="error">An unexpected error occurred while loading the section content.</div>
            </body>
            </html>
            """
            self.web_view.setHtml(error_html)

    def load_audio_for_section(self, section_index):
        """Load audio file for specific section"""
        try:
            # Validate section index
            if not (0 <= section_index <= 3):
                raise ValueError(f"Invalid section index: {section_index}. Must be 0-3.")
            
            # Get current test selection
            current_test = self.test_combo.currentText()
            current_book = self.book_combo.currentText()
            if not current_test or not current_book:
                raise ValueError("No test or book selected")
            
            # Extract test number (e.g., "Test 1" -> "1")
            test_number = current_test.split()[-1]
            
            # Convert book name to folder name (e.g., "Cambridge 20" -> "Cambridge20")
            book_folder = current_book.replace(" ", "")
            
            # Construct audio file path based on actual file structure
            audio_file = f"Test-{test_number}-Part-{section_index + 1}.mp3"
            audio_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'resources', 
                book_folder, 
                'listening', 
                audio_file
            )
            
            # Validate file exists and is readable
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            if not os.path.isfile(audio_path):
                raise ValueError(f"Path is not a file: {audio_path}")
            
            # Check file size (prevent loading extremely large files)
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                raise ValueError(f"Audio file is empty: {audio_path}")
            
            if file_size > 100 * 1024 * 1024:  # 100MB limit for audio
                raise ValueError(f"Audio file too large: {file_size} bytes")
            
            # Validate file extension
            if not audio_path.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg')):
                raise ValueError(f"Unsupported audio format: {audio_path}")
            
            # Set up media player
            media_content = QMediaContent(QUrl.fromLocalFile(os.path.abspath(audio_path)))
            self.media_player.setMedia(media_content)
            self.current_audio_file = audio_path
            app_logger.debug(f"Loaded audio: {audio_path}")
                
        except (FileNotFoundError, ValueError, OSError) as e:
            app_logger.debug(f"Error loading audio for section {section_index + 1}: {e}")
            # Clear any existing media to prevent playing wrong audio
            self.media_player.setMedia(QMediaContent())
            
        except Exception as e:
            app_logger.debug(f"Unexpected error loading audio for section {section_index + 1}: {e}")
            # Clear any existing media to prevent playing wrong audio
            self.media_player.setMedia(QMediaContent())

    def switch_section(self, index):
        """Switch to a different section"""
        if index < 0 or index >= 4:
            return
        
        # Update current section
        self.current_section = index
        

        
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
        try:
            # Validate current_section exists and is valid
            if not hasattr(self, 'current_section'):
                self.current_section = 0
            
            # Ensure current_section is within valid range
            if not (0 <= self.current_section <= 3):
                app_logger.debug(f"Warning: Invalid current_section value: {self.current_section}. Resetting to 0.")
                self.current_section = 0
            
            # Check if buttons exist before updating them
            if hasattr(self, 'back_button') and self.back_button is not None:
                # Enable back button only if not on first section
                self.back_button.setEnabled(self.current_section > 0)
                
                # Update button text to be more descriptive
                if self.current_section > 0:
                    self.back_button.setToolTip(f"Go to Section {self.current_section}")
                else:
                    self.back_button.setToolTip("No previous section")
            else:
                app_logger.debug("Warning: back_button not found or is None")
            
            if hasattr(self, 'next_button') and self.next_button is not None:
                # Enable next button only if not on last section
                self.next_button.setEnabled(self.current_section < 3)
                
                # Update button text to be more descriptive
                if self.current_section < 3:
                    self.next_button.setToolTip(f"Go to Section {self.current_section + 2}")
                else:
                    self.next_button.setToolTip("No next section")
            else:
                app_logger.debug("Warning: next_button not found or is None")
                
            # Update section indicator if it exists
            if hasattr(self, 'section_label') and self.section_label is not None:
                self.section_label.setText(f"Section {self.current_section + 1} of 4")
                
        except Exception as e:
            app_logger.debug(f"Error updating navigation buttons: {e}")
            # Fallback: disable both buttons to prevent crashes
            if hasattr(self, 'back_button') and self.back_button is not None:
                self.back_button.setEnabled(False)
            if hasattr(self, 'next_button') and self.next_button is not None:
                self.next_button.setEnabled(False)



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
            temp_file_path = temp_file.name
            temp_file.close()  # Close file handle before writing with wave
            
            with wave.open(temp_file_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes per sample
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(b''.join(audio_data))
            
            # Play the test audio
            test_url = QUrl.fromLocalFile(temp_file_path)
            self.media_player.setMedia(QMediaContent(test_url))
            self.media_player.play()
            
            # Store temp file path for cleanup
            self.temp_audio_file = temp_file_path
            
            # Update status
            self.audio_status_label.setText("🔊 Playing test audio...")
            self.audio_test_button.setText("Playing...")
            self.audio_test_button.setEnabled(False)
            
            # Re-enable button and cleanup after 3 seconds
            QTimer.singleShot(3000, self.reset_audio_test_button)
            
        except Exception as e:
            app_logger.debug(f"Error playing audio test: {e}")
            self.audio_status_label.setText("❌ Audio test failed")
    
    def reset_audio_test_button(self):
        """Reset the audio test button after playing"""
        self.audio_test_button.setText("🔊 Test Audio")
        self.audio_test_button.setEnabled(True)
        self.audio_status_label.setText("✅ Audio test completed")
        
        # Clean up temporary audio file
        if hasattr(self, 'temp_audio_file'):
            try:
                import os
                if os.path.exists(self.temp_audio_file):
                    os.unlink(self.temp_audio_file)
                delattr(self, 'temp_audio_file')
            except Exception as e:
                app_logger.debug(f"Error cleaning up temp audio file: {e}")
    
    def start_actual_test(self):
        """Start the actual test by hiding overlay and showing web view"""
        # Switch to web view
        self.content_stack.setCurrentWidget(self.web_view)
        
        # Start the timer
        if not self.test_started:
            # Reset timer to full duration
            self.time_remaining = self.total_time
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
        """Update completion count and question tracker for current section"""
        if hasattr(self, 'web_view') and self.web_view.page():
            # Execute JavaScript to count filled inputs and collect answered indices
            js_code = """
            (function() {
                try {
                    var inputs = document.querySelectorAll('.answer-blank');
                    var completed = 0;
                    var total = inputs.length;
                    var answered_indices = [];
                    
                    inputs.forEach(function(input, idx) {
                        if (input.value && input.value.trim() !== '') {
                            completed++;
                            answered_indices.push(idx);
                        }
                    });
                    
                    return {completed: completed, total: total, answered_indices: answered_indices, success: true};
                } catch (error) {
                    return {completed: 0, total: 10, answered_indices: [], success: false, error: error.message};
                }
            })();
            """
            
            def handle_result(result):
                try:
                    if result and isinstance(result, dict) and result.get('success', False):
                        answered = result.get('answered_indices', [])
                        self.refresh_question_tracker(answered)
                    else:
                        error_msg = result.get('error', 'Unknown error') if result else 'No result'
                        app_logger.debug(f"JavaScript execution error: {error_msg}")
                        self.refresh_question_tracker([])
                except Exception as e:
                    app_logger.debug(f"Error handling JavaScript result: {e}")
                    self.refresh_question_tracker([])
            
            try:
                self.web_view.page().runJavaScript(js_code, handle_result)
            except Exception as e:
                # Fallback if JavaScript execution fails
                app_logger.debug(f"Failed to execute JavaScript: {e}")
                self.refresh_question_tracker([])
    
    def build_question_tracker(self, main_layout):
        """Create the bottom question tracker UI with 40 buttons grouped by part."""
        self.question_buttons = {}
        tracker = QWidget()
        tracker.setObjectName("question_tracker")
        layout = QHBoxLayout(tracker)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(12)
        
        for part in range(4):
            part_widget = QWidget()
            part_layout = QHBoxLayout(part_widget)
            part_layout.setContentsMargins(0, 0, 0, 0)
            part_layout.setSpacing(6)
            
            part_label = QLabel(f"Part {part + 1}")
            part_label.setObjectName("part_label")
            part_layout.addWidget(part_label)
            
            numbers_container = QWidget()
            nums_layout = QHBoxLayout(numbers_container)
            nums_layout.setContentsMargins(6, 0, 0, 0)
            nums_layout.setSpacing(4)
            
            start = part * 10 + 1
            for q in range(start, start + 10):
                btn = QPushButton(f"{q:02d}")
                btn.setObjectName("question_cell")
                btn.setFixedSize(32, 24)
                btn.clicked.connect(lambda checked, num=q: self.on_question_cell_clicked(num))
                self.question_buttons[q] = btn
                nums_layout.addWidget(btn)
            
            part_layout.addWidget(numbers_container)
            layout.addWidget(part_widget)
        
        # Style just the tracker area
        tracker.setStyleSheet("""
            QWidget#question_tracker { background-color: #ffffff; border-top: 1px solid #dee2e6; }
            QLabel#part_label { color: #6c757d; font-size: 11px; font-style: italic; min-width: 50px; }
            QPushButton#question_cell { background-color: #000000; color: #ffffff; border: 1px solid #333333; padding: 2px; border-radius: 2px; min-width: 28px; min-height: 20px; }
            QPushButton#question_cell[answered="true"] { background-color: #007bff; border-color: #0056b3; }
            QPushButton#question_cell:disabled { background-color: #222222; color: #777777; border-color: #444444; }
        """)
        
        # Add to layout and initialize state
        main_layout.addWidget(tracker)
        self.refresh_question_tracker([])
    
    def refresh_question_tracker(self, answered_indices):
        """Refresh the question tracker button states using answered indices for the current section."""
        if not hasattr(self, 'question_buttons') or not self.question_buttons:
            return
        
        start = self.current_section * 10 + 1
        end = start + 9
        
        for q in range(1, 41):
            btn = self.question_buttons.get(q)
            if not btn:
                continue
            in_current = start <= q <= end
            
            if in_current:
                idx_in_section = q - start
                is_answered = idx_in_section in (answered_indices or [])
            else:
                # Preserve previously detected answered state for other sections
                is_answered = bool(btn.property('answered'))
            btn.setProperty('answered', is_answered)
            
            # Re-apply stylesheet to reflect property changes
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()
    
    def on_question_cell_clicked(self, qnum: int):
        """Navigate to a question number; switch section if needed and scroll to input."""
        target_section = (qnum - 1) // 10
        if target_section != self.current_section:
            self.switch_section(target_section)
            QTimer.singleShot(600, lambda: self.scroll_to_question(qnum))
        else:
            self.scroll_to_question(qnum)
    
    def scroll_to_question(self, qnum: int):
        """Scroll to the question input within the current section."""
        try:
            idx = (qnum - 1) % 10
            js_code = f"""
            (function() {{
                try {{
                    var inputs = document.querySelectorAll('.answer-blank');
                    var idx = {idx};
                    if (inputs && inputs.length > idx) {{
                        var el = inputs[idx];
                        el.scrollIntoView({{behavior:'smooth', block:'center'}});
                        if (el.focus) el.focus();
                        el.style.outline = '2px solid #007bff';
                        setTimeout(function() {{ el.style.outline = ''; }}, 1500);
                        return true;
                    }}
                    var el2 = document.querySelector('.answer-blank[data-question="{qnum}"]');
                    if (el2) {{
                        el2.scrollIntoView({{behavior:'smooth', block:'center'}});
                        if (el2.focus) el2.focus();
                        el2.style.outline = '2px solid #007bff';
                        setTimeout(function() {{ el2.style.outline = ''; }}, 1500);
                        return true;
                    }}
                    return false;
                }} catch (e) {{
                    return false;
                }}
            }})();
            """
            self.web_view.page().runJavaScript(js_code, lambda res: None)
        except Exception as e:
            app_logger.debug(f"Failed to scroll to question {qnum}: {e}")

    def collect_all_answers(self):
        """Collect all answers from all sections using JavaScript"""
        # Initialize collection state
        self.collected_answers = {}
        self.sections_to_collect = list(range(4))
        self.current_collection_index = 0
        
        # Start collecting from first section
        self.collect_next_section()
    
    def collect_next_section(self):
        """Collect answers from the next section in sequence"""
        if self.current_collection_index >= len(self.sections_to_collect):
            # All sections collected, save answers
            self.save_answers_to_file()
            return
        
        section_index = self.sections_to_collect[self.current_collection_index]
        
        # JavaScript code to collect all answers from the current page
        js_code = """
        (function() {
            try {
                var inputs = document.querySelectorAll('.answer-blank');
                var answers = {};
                
                inputs.forEach(function(input, index) {
                    var questionNumber = input.getAttribute('data-question') || (index + 1);
                    var value = input.value ? input.value.trim() : '';
                    answers[questionNumber] = value;
                });
                
                return {answers: answers, success: true};
            } catch (error) {
                return {answers: {}, success: false, error: error.message};
            }
        })();
        """
        
        # Switch to the section
        self.switch_section(section_index)
        
        # Wait for page to load, then collect answers
        QTimer.singleShot(800, lambda: self.execute_collection_js(section_index, js_code))
    
    def execute_collection_js(self, section_index, js_code):
        """Execute JavaScript to collect answers for a section"""
        def handle_collection_result(result):
            try:
                if result and isinstance(result, dict) and result.get('success', False):
                    answers = result.get('answers', {})
                    self.store_section_answers(section_index, answers)
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'No result'
                    app_logger.debug(f"Failed to collect answers for section {section_index + 1}: {error_msg}")
                    self.store_section_answers(section_index, {})
            except Exception as e:
                app_logger.debug(f"Error processing collection result for section {section_index + 1}: {e}")
                self.store_section_answers(section_index, {})
        
        try:
            self.web_view.page().runJavaScript(js_code, handle_collection_result)
        except Exception as e:
            app_logger.debug(f"Failed to execute collection JavaScript for section {section_index + 1}: {e}")
            self.store_section_answers(section_index, {})
    
    def store_section_answers(self, section_index, answers):
        """Store answers for a specific section"""
        self.collected_answers[f"Section {section_index + 1}"] = answers
        
        # Move to next section
        self.current_collection_index += 1
        
        # Continue with next section or finish if all done
        if self.current_collection_index < len(self.sections_to_collect):
            # Collect next section after a short delay
            QTimer.singleShot(200, self.collect_next_section)
        else:
            # All sections collected, save the answers
            self.save_answers_to_file()
    
    def save_answers_to_file(self):
        """Save all collected answers to a text file """
        try:
            ielts_practice_path = os.path.join(os.path.dirname(__file__), '..', 'results', 'listening')
            
            # Create directory if it doesn't exist
            if not os.path.exists(ielts_practice_path):
                os.makedirs(ielts_practice_path)
            
            # Generate filename with timestamp
            current_time = datetime.now()
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            current_test = self.test_combo.currentText() or "Unknown_Test"
            current_book = self.book_combo.currentText() or "Unknown_Book"
            
            filename = f"Listening_Answers_{current_book.replace(' ', '_')}_{current_test.replace(' ', '_')}_{timestamp}.txt"
            file_path = os.path.join(ielts_practice_path, filename)
            
            # Prepare content
            content = []
            content.append("=" * 60)
            content.append("IELTS LISTENING TEST ANSWERS")
            content.append("=" * 60)
            content.append(f"Test: {current_book} - {current_test}")
            content.append(f"Date: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            content.append(f"Duration: {35 - (self.time_remaining // 60)} minutes")
            content.append("=" * 60)
            content.append("")
            
            # Add answers for each section
            for section_name in ["Section 1", "Section 2", "Section 3", "Section 4"]:
                content.append(f"{section_name}:")
                content.append("-" * 20)
                
                if section_name in getattr(self, 'collected_answers', {}):
                    answers = self.collected_answers[section_name]
                    if answers:
                        for question, answer in answers.items():
                            content.append(f"Question {question}: {answer if answer else '[No Answer]'}")
                    else:
                        content.append("No answers recorded for this section")
                else:
                    content.append("Section not completed")
                
                content.append("")
            
            content.append("=" * 60)
            content.append("End of Answers")
            content.append("=" * 60)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            # Show success message
            QMessageBox.information(self, "Answers Saved", 
                                  f"Your answers have been saved successfully!\n\n"
                                  f"File location: {file_path}")
            
        except Exception as e:
            QMessageBox.warning(self, "Save Error", 
                              f"Failed to save answers: {str(e)}")
    
    def show_test_summary(self):
        """Show test completion summary and save answers"""
        # Collect and save answers
        self.collect_all_answers()
        
        QMessageBox.information(self, "Test Complete", 
                              "Your listening test has been completed.\n\n"
                              "Your answers are being saved to results folder.")



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