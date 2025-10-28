import os
import struct
import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import app_logger
from resource_manager import get_resource_manager
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, 
    QFrame, QComboBox, QSpacerItem, QMessageBox
)
from PyQt5.QtCore import QUrl, Qt, QTimer, QFile
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Try to import QtMultimedia components for recording
try:
    from PyQt5.QtMultimedia import QAudioInput, QAudioFormat, QAudioDeviceInfo
except ImportError:
    QAudioInput = None
    QAudioFormat = None
    QAudioDeviceInfo = None


class WavFileWriter:
    """Simple WAV writer using QFile. Writes a placeholder header and fixes sizes on finalize."""
    def __init__(self, path: str, sample_rate: int, channels: int, sample_size_bits: int):
        self.path = path
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_size_bits = sample_size_bits
        self.byte_rate = sample_rate * channels * (sample_size_bits // 8)
        self.block_align = channels * (sample_size_bits // 8)
        self.file = QFile(path)

    def open(self) -> bool:
        if not self.file.open(QFile.WriteOnly):
            return False
        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36,               # placeholder for chunk size
            b'WAVE',
            b'fmt ',
            16,               # PCM fmt chunk size
            1,                # Audio format (PCM)
            self.channels,
            self.sample_rate,
            self.byte_rate,
            self.block_align,
            self.sample_size_bits,
            b'data',
            0                 # placeholder for data size
        )
        self.file.write(header)
        return True

    def finalize(self):
        try:
            total_size = self.file.size()
            data_size = max(0, total_size - 44)
            # Update RIFF chunk size at offset 4: 36 + data_size
            self.file.seek(4)
            self.file.write(struct.pack('<I', 36 + data_size))
            # Update data chunk size at offset 40: data_size
            self.file.seek(40)
            self.file.write(struct.pack('<I', data_size))
            self.file.flush()
        finally:
            self.file.close()


class SpeakingTestUI(QWidget):
    """
    Enhanced IELTS Speaking Test Interface with navigation and recording
    - Navigation between parts with Previous/Next buttons
    - Test selection dropdown
    - Clean content display
    - Enhanced top bar layout
    - Voice recording (Start/Stop) with improved digital timer
    """

    def __init__(self, selected_book: str = None, selected_test: int = None):
        super().__init__()
        self.current_part = 0  # 0=Part1, 1=Part2, 2=Part3
        self.selected_book = selected_book
        try:
            self.current_test = int(selected_test) if selected_test is not None else 1
        except Exception:
            self.current_test = selected_test if selected_test is not None else 1
        self.total_parts = 3
        self.audio_supported = QAudioInput is not None and QAudioFormat is not None

        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.recordings_dir = os.path.join(self.base_dir, 'results', 'speaking')
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        # Initialize resource manager
        self.resource_manager = get_resource_manager()

        # Recording state
        self.audio_input = None
        self.wave_writer = None
        self.record_timer = QTimer(self)
        self.record_timer.setInterval(1000)
        self.record_timer.timeout.connect(self.update_recording_timer)
        self.record_seconds = 0
        self.dot_visible = False  # blinking indicator

        # Speaking test timer state
        self.speaking_timer = QTimer(self)
        self.speaking_timer.setInterval(1000)
        self.speaking_timer.timeout.connect(self.update_speaking_timer)
        self.speaking_time_remaining = 0
        self.speaking_timer_active = False
        self.current_phase = "ready"  # ready, preparation, speaking, completed
        
        # Part-specific durations (in seconds)
        self.part_durations = {
            0: 300,  # Part 1: 5 minutes
            1: 180,  # Part 2: 3 minutes total (1 min prep + 2 min speaking)
            2: 300   # Part 3: 5 minutes
        }
        
        # Part 2 specific timing
        self.part2_prep_time = 60    # 1 minute preparation
        self.part2_speaking_time = 120  # 2 minutes speaking

        # Track recordings for each part
        self.part_recordings = {}  # {part_number: [list_of_recording_paths]}

        # Load available tests
        self.available_tests = self.load_available_tests()
        
        self.apply_style()
        self.init_ui()
        self.load_current_content()
        self.update_navigation_buttons()
        self.update_recording_ui_state()
        
        # Initialize timer display
        self.update_timer_display()
        self.update_timer_controls()

    def load_available_tests(self):
        """Load available speaking tests using the resource manager (fixed selection)"""
        try:
            current_book = getattr(self, 'selected_book', None)
            if current_book:
                tests = self.resource_manager.get_available_tests(current_book, 'speaking')
                return tests if tests else [1]
        except Exception as e:
            app_logger.error("Error loading available tests", exc_info=True)
        return [1]

    def get_part_file_path(self, test_num, part_num):
        """Get the file path for a specific test and part using resource manager"""
        try:
            current_book = self.selected_book
            part_or_task = f"Part-{part_num + 1}"
            
            # Use resource manager to get the correct file path
            book = self.resource_manager.get_book_by_display_name(current_book)
            if book:
                resource_path = self.resource_manager.get_resource_path(book.display_name, 'speaking', int(test_num), part_or_task)
                if resource_path:
                    full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), resource_path)
                    if os.path.exists(full_path):
                        app_logger.info(f"Loaded speaking content: {full_path}")
                        return full_path
                    else:
                        app_logger.warning(f"Speaking file not found: {full_path}")
                else:
                    app_logger.warning(f"Speaking resource not found: Test {test_num} Part {part_num + 1} for book {book.display_name}")
            else:
                app_logger.warning(f"Book not found: {current_book}")
                
        except Exception as e:
            app_logger.error("Error getting part file path", exc_info=True)
        
        # Fallback to default path structure
        fallback_path = os.path.join("resources", "Cambridge20", "speaking", f"Test-{test_num}-Part-{part_num + 1}.html")
        app_logger.warning(f"Using fallback path: {fallback_path}")
        return fallback_path

    def apply_style(self):
        """Apply clean, minimalist styling similar to writing test"""
        self.setStyleSheet("""
            QWidget { 
                background-color: #f8f8f8; 
                font-family: Arial, sans-serif; 
                font-size: 12px; 
                color: #333; 
            }
            
            /* Top bar styling */
            #top_bar { 
                background-color: #f0f0f0; 
                border-bottom: 1px solid #d0d0d0; 
                padding: 5px 15px; 
            }

            /* Button styling */
            QPushButton { 
                background-color: #e6e6e6; 
                border: 1px solid #c8c8c8; 
                border-radius: 3px; 
                padding: 6px 12px; 
                font-size: 12px; 
                min-height: 24px;
                margin: 2px;
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
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border: 1px solid #cccccc;
            }

            /* ComboBox styling */
            QComboBox {
                background-color: white;
                border: 1px solid #c8c8c8;
                padding: 4px 8px;
                border-radius: 3px;
                min-height: 20px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #a0a0a0;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }

            /* Label styling */
            QLabel {
                color: #333333;
                background-color: transparent;
            }

            /* Navigation area styling */
            #nav_area {
                background-color: #f8f8f8;
                border-top: 1px solid #d0d0d0;
                padding: 10px 15px;
            }

            /* Navigation buttons */
            QPushButton#nav_button {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton#nav_button:hover {
                background-color: #1976D2;
            }
            QPushButton#nav_button:disabled {
                background-color: #cccccc;
                color: #666666;
            }

            /* Recording controls */
            QPushButton#record_start {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton#record_start:hover {
                background-color: #45a049;
            }
            QPushButton#record_stop {
                background-color: #E74C3C;
                color: white;
                font-weight: bold;
            }
            QPushButton#record_stop:hover {
                background-color: #C0392B;
            }
            QPushButton#secondary_button {
                background-color: #e6e6e6;
                color: #333;
                font-weight: bold;
            }
            QPushButton#secondary_button:hover {
                background-color: #d8d8d8;
            }

            #recording_label {
                color: #2c3e50;
                font-weight: bold;
                font-size: 14px;
                font-family: Consolas, monospace;
                letter-spacing: 1px;
            }
        """)

    def init_ui(self):
        """Initialize the enhanced user interface"""
        try:
            app_logger.info("Initializing speaking test UI")
            
            # Create main layout with error handling
            try:
                main_layout = QVBoxLayout(self)
                main_layout.setContentsMargins(0, 0, 0, 0)
                main_layout.setSpacing(0)
                app_logger.debug("Main layout created successfully")
            except Exception as layout_error:
                app_logger.error(f"Failed to create main layout: {layout_error}", exc_info=True)
                raise RuntimeError(f"UI initialization failed: {layout_error}")

            # Top bar with test selection and part navigation
            try:
                self.create_top_bar()
                if hasattr(self, 'top_bar') and self.top_bar is not None:
                    main_layout.addWidget(self.top_bar)
                    app_logger.debug("Top bar created and added successfully")
                else:
                    app_logger.error("Top bar creation failed - top_bar attribute not set")
                    raise RuntimeError("Top bar creation failed")
            except Exception as top_bar_error:
                app_logger.error(f"Failed to create top bar: {top_bar_error}", exc_info=True)
                # Try to create a minimal top bar as fallback
                try:
                    fallback_top_bar = QWidget()
                    fallback_top_bar.setFixedHeight(50)
                    fallback_layout = QHBoxLayout(fallback_top_bar)
                    fallback_label = QLabel(f"Speaking Test - {self.selected_book or 'Unknown'} - Test {self.current_test}")
                    fallback_layout.addWidget(fallback_label)
                    main_layout.addWidget(fallback_top_bar)
                    app_logger.warning("Using fallback top bar due to creation error")
                except Exception as fallback_error:
                    app_logger.error(f"Fallback top bar creation also failed: {fallback_error}", exc_info=True)
                    # Continue without top bar

            # Content area
            try:
                self.create_content_area()
                if hasattr(self, 'content_frame') and self.content_frame is not None:
                    main_layout.addWidget(self.content_frame, 1)
                    app_logger.debug("Content area created and added successfully")
                else:
                    app_logger.error("Content area creation failed - content_frame attribute not set")
                    raise RuntimeError("Content area creation failed")
            except Exception as content_error:
                app_logger.error(f"Failed to create content area: {content_error}", exc_info=True)
                # Try to create a minimal content area as fallback
                try:
                    fallback_content = QWidget()
                    fallback_content.setStyleSheet("background-color: #ffffff;")
                    fallback_layout = QVBoxLayout(fallback_content)
                    fallback_label = QLabel("Content area failed to load. Please restart the application.")
                    fallback_label.setAlignment(Qt.AlignCenter)
                    fallback_layout.addWidget(fallback_label)
                    main_layout.addWidget(fallback_content, 1)
                    app_logger.warning("Using fallback content area due to creation error")
                except Exception as fallback_error:
                    app_logger.error(f"Fallback content area creation also failed: {fallback_error}", exc_info=True)
                    raise RuntimeError(f"Critical UI component creation failed: {content_error}")

            # Navigation area
            try:
                self.create_navigation_area()
                if hasattr(self, 'nav_area') and self.nav_area is not None:
                    main_layout.addWidget(self.nav_area)
                    app_logger.debug("Navigation area created and added successfully")
                else:
                    app_logger.error("Navigation area creation failed - nav_area attribute not set")
                    raise RuntimeError("Navigation area creation failed")
            except Exception as nav_error:
                app_logger.error(f"Failed to create navigation area: {nav_error}", exc_info=True)
                # Try to create a minimal navigation area as fallback
                try:
                    fallback_nav = QWidget()
                    fallback_nav.setFixedHeight(80)
                    fallback_layout = QHBoxLayout(fallback_nav)
                    fallback_label = QLabel("Navigation controls failed to load")
                    fallback_layout.addWidget(fallback_label)
                    main_layout.addWidget(fallback_nav)
                    app_logger.warning("Using fallback navigation area due to creation error")
                except Exception as fallback_error:
                    app_logger.error(f"Fallback navigation area creation also failed: {fallback_error}", exc_info=True)
                    # Continue without navigation area

            # Set layout with error handling
            try:
                self.setLayout(main_layout)
                app_logger.info("Speaking test UI initialized successfully")
            except Exception as set_layout_error:
                app_logger.error(f"Failed to set main layout: {set_layout_error}", exc_info=True)
                raise RuntimeError(f"Failed to finalize UI layout: {set_layout_error}")
                
        except RuntimeError as e:
            app_logger.error(f"Critical error in UI initialization: {e}", exc_info=True)
            QMessageBox.critical(self, "UI Initialization Error", 
                               f"Failed to initialize speaking test interface:\n{e}")
            raise
        except Exception as e:
            app_logger.error(f"Unexpected error in UI initialization: {e}", exc_info=True)
            QMessageBox.warning(self, "UI Warning", 
                              f"Speaking test interface loaded with issues:\n{e}\n\nSome features may not work properly.")
            # Try to set a minimal layout if none was set
            try:
                if self.layout() is None:
                    minimal_layout = QVBoxLayout(self)
                    minimal_label = QLabel("Speaking Test - Minimal Mode")
                    minimal_label.setAlignment(Qt.AlignCenter)
                    minimal_layout.addWidget(minimal_label)
                    self.setLayout(minimal_layout)
                    app_logger.warning("Set minimal layout as emergency fallback")
            except Exception as minimal_error:
                app_logger.error(f"Even minimal layout failed: {minimal_error}", exc_info=True)

    def create_top_bar(self):
        """Create enhanced top bar with fixed book/test and part buttons"""
        self.top_bar = QWidget()
        self.top_bar.setObjectName('top_bar')
        self.top_bar.setFixedHeight(50)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(15, 5, 15, 5)
        top_layout.setSpacing(15)

        # Left section: Fixed Book and Test display
        left_section = QWidget()
        left_layout = QHBoxLayout(left_section)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        book_label = QLabel("Book:")
        book_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        book_value_label = QLabel(self.selected_book if self.selected_book else "Unknown")
        book_value_label.setStyleSheet("font-size: 12px;")
        test_value_label = QLabel(f"Test: {self.current_test}")
        test_value_label.setStyleSheet("font-weight: bold; font-size: 13px;")

        left_layout.addWidget(book_label)
        left_layout.addWidget(book_value_label)
        left_layout.addWidget(test_value_label)

        # Center section: Part navigation buttons
        center_section = QWidget()
        center_layout = QHBoxLayout(center_section)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(2)
        
        self.part_buttons = []
        for i in range(3):
            btn = QPushButton(f"Part {i+1}")
            btn.setCheckable(True)
            btn.setMinimumWidth(80)
            btn.clicked.connect(lambda checked, part=i: self.switch_to_part(part))
            self.part_buttons.append(btn)
            center_layout.addWidget(btn)
        
        # Set initial active part
        self.part_buttons[0].setChecked(True)

        # Right section: Progress indicator
        right_section = QWidget()
        right_layout = QHBoxLayout(right_section)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_label = QLabel(f"Part {self.current_part + 1} of {self.total_parts}")
        self.progress_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        right_layout.addWidget(self.progress_label)

        # Add sections to top bar
        top_layout.addWidget(left_section)
        top_layout.addStretch()
        top_layout.addWidget(center_section)
        top_layout.addStretch()
        top_layout.addWidget(right_section)

    def create_content_area(self):
        """Create clean content display area"""
        self.content_frame = QFrame()
        self.content_frame.setFrameStyle(QFrame.NoFrame)
        self.content_frame.setStyleSheet("background-color: #ffffff;")
        
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Web view for HTML content
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.web_view.setStyleSheet("border: none; background-color: #ffffff;")
        self.web_view.loadFinished.connect(self.on_load_finished)
        
        content_layout.addWidget(self.web_view)

    def create_navigation_area(self):
        """Create navigation area with Previous/Next and Recording controls"""
        self.nav_area = QWidget()
        self.nav_area.setObjectName('nav_area')
        self.nav_area.setFixedHeight(80)
        nav_layout = QHBoxLayout(self.nav_area)
        nav_layout.setContentsMargins(15, 10, 15, 10)
        nav_layout.setSpacing(15)

        # Left side: Status info and timer
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        
        self.status_label = QLabel("Ready to record. Use Start and Stop to capture your answers.")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        
        # Speaking timer display
        timer_container = QWidget()
        timer_layout = QHBoxLayout(timer_container)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_layout.setSpacing(10)
        
        self.timer_label = QLabel("Timer:")
        self.timer_label.setStyleSheet("color: #333; font-weight: bold;")
        
        self.countdown_display = QLabel("05:00")
        self.countdown_display.setStyleSheet("""
            color: #2c3e50;
            font-size: 18px;
            font-weight: bold;
            font-family: Consolas, monospace;
            background-color: #ecf0f1;
            padding: 5px 10px;
            border-radius: 5px;
            border: 2px solid #bdc3c7;
        """)
        
        self.phase_label = QLabel("Ready to start")
        self.phase_label.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 11px;")
        
        # Timer controls
        self.start_timer_btn = QPushButton("Start Timer")
        self.start_timer_btn.setObjectName('record_start')
        self.start_timer_btn.setToolTip("Start the speaking test timer")
        self.start_timer_btn.clicked.connect(self.start_speaking_timer)
        
        self.pause_timer_btn = QPushButton("Pause")
        self.pause_timer_btn.setObjectName('secondary_button')
        self.pause_timer_btn.setToolTip("Pause the speaking test timer")
        self.pause_timer_btn.clicked.connect(self.pause_speaking_timer)
        self.pause_timer_btn.setEnabled(False)
        
        self.reset_timer_btn = QPushButton("Reset")
        self.reset_timer_btn.setObjectName('secondary_button')
        self.reset_timer_btn.setToolTip("Reset the speaking test timer")
        self.reset_timer_btn.clicked.connect(self.reset_speaking_timer)
        
        timer_layout.addWidget(self.timer_label)
        timer_layout.addWidget(self.countdown_display)
        timer_layout.addWidget(self.phase_label)
        timer_layout.addWidget(self.start_timer_btn)
        timer_layout.addWidget(self.pause_timer_btn)
        timer_layout.addWidget(self.reset_timer_btn)
        timer_layout.addStretch()
        
        left_layout.addWidget(self.status_label)
        left_layout.addWidget(timer_container)
        
        # Middle: Recording controls
        record_panel = QWidget()
        record_layout = QHBoxLayout(record_panel)
        record_layout.setContentsMargins(0, 0, 0, 0)
        record_layout.setSpacing(10)

        self.recording_label = QLabel("<span style='color:#E74C3C'>●</span> 00:00:00")
        self.recording_label.setObjectName('recording_label')
        self.recording_label.setTextFormat(Qt.RichText)
        
        self.record_start_btn = QPushButton("Start Recording")
        self.record_start_btn.setObjectName('record_start')
        self.record_start_btn.setToolTip("Start recording your answer using the microphone")
        self.record_start_btn.clicked.connect(self.start_recording)

        self.record_stop_btn = QPushButton("Stop")
        self.record_stop_btn.setObjectName('record_stop')
        self.record_stop_btn.setToolTip("Stop recording and save to file")
        self.record_stop_btn.clicked.connect(self.stop_recording)

        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.setObjectName('secondary_button')
        self.open_folder_btn.setToolTip("Open the recordings folder")
        self.open_folder_btn.clicked.connect(self.open_recordings_folder)

        record_layout.addWidget(self.recording_label)
        record_layout.addWidget(self.record_start_btn)
        record_layout.addWidget(self.record_stop_btn)
        record_layout.addWidget(self.open_folder_btn)

        # Right side: Navigation buttons
        nav_buttons = QWidget()
        nav_buttons_layout = QHBoxLayout(nav_buttons)
        nav_buttons_layout.setContentsMargins(0, 0, 0, 0)
        nav_buttons_layout.setSpacing(10)
        
        self.back_button = QPushButton("← Previous")
        self.back_button.setObjectName('nav_button')
        self.back_button.clicked.connect(self.go_previous)
        
        self.next_button = QPushButton("Next →")
        self.next_button.setObjectName('nav_button')
        self.next_button.clicked.connect(self.go_next)
        
        # Add Finish Test button
        self.finish_button = QPushButton("Finish Test")
        self.finish_button.setObjectName('nav_button')
        self.finish_button.clicked.connect(self.finish_test)
        self.finish_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: 1px solid #c0392b;
                padding: 8px 16px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        nav_buttons_layout.addWidget(self.back_button)
        nav_buttons_layout.addWidget(self.next_button)
        nav_buttons_layout.addWidget(self.finish_button)

        nav_layout.addWidget(left_panel)
        nav_layout.addStretch()
        nav_layout.addWidget(record_panel)
        nav_layout.addStretch()
        nav_layout.addWidget(nav_buttons)

    def on_book_changed(self, book_text):
        """Deprecated in fixed selection mode: no in-app book switching"""
        return

    def on_test_changed(self, test_text):
        """Deprecated in fixed selection mode: no in-app test switching"""
        return

    def switch_to_part(self, part_index: int):
        """Switch to specified part"""
        if 0 <= part_index < self.total_parts:
            # Update button states
            for i, btn in enumerate(self.part_buttons):
                btn.setChecked(i == part_index)
            
            self.current_part = part_index
            self.load_current_content()
            self.update_navigation_buttons()
            self.update_progress_label()
            
            # Reset timer for new part
            self.reset_speaking_timer()

    def go_previous(self):
        """Navigate to previous part"""
        if self.current_part > 0:
            self.switch_to_part(self.current_part - 1)

    def go_next(self):
        """Navigate to next part"""
        if self.current_part < self.total_parts - 1:
            self.switch_to_part(self.current_part + 1)

    def update_navigation_buttons(self):
        """Update navigation button states"""
        self.back_button.setEnabled(self.current_part > 0)
        self.next_button.setEnabled(self.current_part < self.total_parts - 1)

    def update_progress_label(self):
        """Update progress indicator"""
        self.progress_label.setText(f"Part {self.current_part + 1} of {self.total_parts}")

    def load_current_content(self):
        """Load the HTML file for the current test and part"""
        file_path = self.get_part_file_path(self.current_test, self.current_part)
        
        if os.path.exists(file_path):
            url = QUrl.fromLocalFile(os.path.abspath(file_path))
            self.web_view.load(url)
        else:
            self.show_error_message(
                f"Part {self.current_part + 1} not found", 
                f"Test {self.current_test}, Part {self.current_part + 1} file not found: {file_path}"
            )

    def show_error_message(self, title: str, message: str):
        """Display error message in web view"""
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 40px;
                    text-align: center;
                    background-color: #f8f9fa;
                }}
                .error-container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    max-width: 600px;
                    margin: 0 auto;
                }}
                h1 {{
                    color: #dc3545;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #6c757d;
                    font-size: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>{title}</h1>
                <p>{message}</p>
            </div>
        </body>
        </html>
        """
        self.web_view.setHtml(html)

    def on_load_finished(self, ok: bool):
        """Apply styling improvements when content loads"""
        if ok:
            # Inject CSS for better readability
            css_injection = """
            var style = document.createElement('style');
            style.textContent = `
                body {
                    font-family: Arial, sans-serif !important;
                    line-height: 1.6 !important;
                    padding: 20px !important;
                    max-width: none !important;
                    margin: 0 !important;
                }
                
                h1, h2, h3, h4, h5, h6 {
                    color: #2c3e50 !important;
                    margin-bottom: 15px !important;
                }
                
                p, div, span, li {
                    font-size: 16px !important;
                    color: #34495e !important;
                }
                
                .question, .instruction {
                    font-size: 18px !important;
                    font-weight: 500 !important;
                    margin-bottom: 15px !important;
                }
                
                button {
                    font-size: 14px !important;
                    padding: 8px 16px !important;
                    margin: 5px !important;
                    border-radius: 4px !important;
                }
                
                ul, ol {
                    padding-left: 25px !important;
                }
                
                li {
                    margin-bottom: 8px !important;
                }
            `;
            document.head.appendChild(style);
            """
            self.web_view.page().runJavaScript(css_injection)

    # ===== Recording Logic =====
    def update_recording_ui_state(self):
        """Enable/disable recording controls based on state and support."""
        supported = self.audio_supported
        recording = self.audio_input is not None

        self.record_start_btn.setEnabled(supported and not recording)
        self.record_stop_btn.setEnabled(supported and recording)
        self.open_folder_btn.setEnabled(True)

        if not supported:
            self.status_label.setText("Recording is not available: QtMultimedia module not found.")
        elif recording:
            self.status_label.setText("Recording in progress...")
        else:
            self.status_label.setText("Ready to record. Use Start and Stop to capture your answers.")

    def format_seconds(self, secs: int) -> str:
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def update_recording_timer(self):
        if self.audio_input is not None:
            self.record_seconds += 1
            self.dot_visible = not self.dot_visible
            dot_html = "<span style='color:#E74C3C'>●</span>" if self.dot_visible else "<span style='color:#E74C3C; opacity:0'>●</span>"
            self.recording_label.setText(f"{dot_html} {self.format_seconds(self.record_seconds)}")

    def get_default_audio_format(self):
        if not self.audio_supported:
            return None
        fmt = QAudioFormat()
        fmt.setSampleRate(44100)
        fmt.setChannelCount(1)
        fmt.setSampleSize(16)
        fmt.setCodec("audio/pcm")
        fmt.setByteOrder(QAudioFormat.LittleEndian)
        fmt.setSampleType(QAudioFormat.SignedInt)
        info = QAudioDeviceInfo.defaultInputDevice()
        if info.isNull():
            return None
        if not info.isFormatSupported(fmt):
            fmt = info.preferredFormat()
        return fmt

    def generate_recording_path(self) -> str:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Speaking-Test-{self.current_test}-Part-{self.current_part + 1}-{timestamp}.wav"
        return os.path.join(self.recordings_dir, filename)

    def start_recording(self):
        try:
            app_logger.info("Attempting to start audio recording")
            
            # Check audio support
            if not self.audio_supported:
                app_logger.warning("Audio recording not supported - QtMultimedia unavailable")
                QMessageBox.warning(self, "Recording Unavailable", "QtMultimedia is not available. Please install PyQt5 with QtMultimedia support.")
                return
            
            # Check if already recording
            if self.audio_input is not None:
                app_logger.debug("Recording already in progress, ignoring start request")
                return  # already recording

            # Get audio format with error handling
            try:
                fmt = self.get_default_audio_format()
                if fmt is None:
                    app_logger.error("No audio input device found")
                    QMessageBox.warning(self, "No Input Device", "No audio input device found.")
                    return
                app_logger.debug(f"Audio format obtained: {fmt.sampleRate()}Hz, {fmt.channelCount()} channels")
            except Exception as format_error:
                app_logger.error(f"Failed to get audio format: {format_error}", exc_info=True)
                QMessageBox.critical(self, "Audio Format Error", f"Failed to configure audio format: {format_error}")
                return

            # Generate recording path with error handling
            try:
                path = self.generate_recording_path()
                if not path:
                    raise ValueError("Generated path is empty")
                app_logger.debug(f"Recording path generated: {path}")
            except Exception as path_error:
                app_logger.error(f"Failed to generate recording path: {path_error}", exc_info=True)
                QMessageBox.critical(self, "Path Error", f"Failed to generate recording path: {path_error}")
                return

            # Initialize wave writer with error handling
            try:
                self.wave_writer = WavFileWriter(path, fmt.sampleRate(), fmt.channelCount(), fmt.sampleSize())
                if not self.wave_writer.open():
                    app_logger.error(f"Failed to open wave file for writing: {path}")
                    QMessageBox.critical(self, "File Error", f"Cannot open file for writing: {path}")
                    self.wave_writer = None
                    return
                app_logger.debug("Wave writer initialized successfully")
            except Exception as writer_error:
                app_logger.error(f"Failed to initialize wave writer: {writer_error}", exc_info=True)
                QMessageBox.critical(self, "Writer Error", f"Failed to initialize audio writer: {writer_error}")
                self.wave_writer = None
                return

            # Start audio input with comprehensive error handling
            try:
                # Create audio input
                try:
                    self.audio_input = QAudioInput(fmt, self)
                    app_logger.debug("Audio input created successfully")
                except Exception as input_create_error:
                    app_logger.error(f"Failed to create audio input: {input_create_error}", exc_info=True)
                    raise RuntimeError(f"Audio input creation failed: {input_create_error}")
                
                # Start streaming
                try:
                    self.audio_input.start(self.wave_writer.file)
                    app_logger.debug("Audio streaming started successfully")
                except Exception as stream_error:
                    app_logger.error(f"Failed to start audio streaming: {stream_error}", exc_info=True)
                    raise RuntimeError(f"Audio streaming failed: {stream_error}")
                    
            except Exception as audio_error:
                app_logger.error(f"Failed to start audio recording: {audio_error}", exc_info=True)
                QMessageBox.critical(self, "Recording Error", f"Failed to start recording: {audio_error}")
                
                # Cleanup on failure
                try:
                    if hasattr(self, 'wave_writer') and self.wave_writer is not None:
                        if hasattr(self.wave_writer, 'file') and self.wave_writer.file is not None:
                            self.wave_writer.file.close()
                        self.wave_writer = None
                    if hasattr(self, 'audio_input') and self.audio_input is not None:
                        self.audio_input = None
                    app_logger.debug("Cleanup completed after recording start failure")
                except Exception as cleanup_error:
                    app_logger.error(f"Failed to cleanup after recording error: {cleanup_error}", exc_info=True)
                return

            # Initialize recording state with error handling
            try:
                self.record_seconds = 0
                self.dot_visible = True
                
                # Update recording label
                try:
                    if hasattr(self, 'recording_label') and self.recording_label is not None:
                        self.recording_label.setText("<span style='color:#E74C3C'>●</span> 00:00:00")
                        app_logger.debug("Recording label updated")
                    else:
                        app_logger.warning("Recording label not available")
                except Exception as label_error:
                    app_logger.warning(f"Failed to update recording label: {label_error}")
                
                # Start recording timer
                try:
                    if hasattr(self, 'record_timer') and self.record_timer is not None:
                        self.record_timer.start()
                        app_logger.debug("Recording timer started")
                    else:
                        app_logger.warning("Recording timer not available")
                except Exception as timer_error:
                    app_logger.warning(f"Failed to start recording timer: {timer_error}")
                
                # Update UI state
                try:
                    self.update_recording_ui_state()
                    app_logger.debug("Recording UI state updated")
                except Exception as ui_error:
                    app_logger.warning(f"Failed to update recording UI state: {ui_error}")
                
                app_logger.info("Audio recording started successfully")
                
            except Exception as state_error:
                app_logger.error(f"Failed to initialize recording state: {state_error}", exc_info=True)
                # Try to stop the recording that was started
                try:
                    if self.audio_input is not None:
                        self.audio_input.stop()
                        self.audio_input = None
                    if self.wave_writer is not None:
                        if hasattr(self.wave_writer, 'file') and self.wave_writer.file is not None:
                            self.wave_writer.file.close()
                        self.wave_writer = None
                except Exception as stop_error:
                    app_logger.error(f"Failed to stop recording after state error: {stop_error}", exc_info=True)
                
                QMessageBox.warning(self, "Recording State Error", 
                                  f"Recording started but state initialization failed: {state_error}")
                
        except Exception as e:
            app_logger.error(f"Critical error in start_recording: {e}", exc_info=True)
            QMessageBox.critical(self, "Critical Recording Error", 
                               f"Unexpected error starting recording: {e}")
            # Ensure cleanup
            try:
                self.audio_input = None
                self.wave_writer = None
            except:
                pass

    def stop_recording(self):
        try:
            app_logger.info("Attempting to stop audio recording")
            
            # Check if recording is active
            if self.audio_input is None:
                app_logger.debug("No active recording to stop")
                return
            
            # Stop audio input with error handling
            try:
                self.audio_input.stop()
                app_logger.debug("Audio input stopped successfully")
            except Exception as stop_error:
                app_logger.error(f"Failed to stop audio input: {stop_error}", exc_info=True)
                QMessageBox.warning(self, "Stop Error", f"Failed to stop audio input: {stop_error}")
                # Continue with cleanup even if stop failed
            
            # Stop recording timer with error handling
            try:
                if hasattr(self, 'record_timer') and self.record_timer is not None:
                    self.record_timer.stop()
                    app_logger.debug("Recording timer stopped")
                else:
                    app_logger.warning("Recording timer not available for stopping")
            except Exception as timer_error:
                app_logger.warning(f"Failed to stop recording timer: {timer_error}")
            
            # Finalize WAV file with comprehensive error handling
            saved_path = None
            try:
                if self.wave_writer is not None:
                    try:
                        self.wave_writer.finalize()
                        saved_path = self.wave_writer.path
                        app_logger.info(f"Recording finalized successfully: {saved_path}")
                        
                        # Update status label
                        try:
                            if hasattr(self, 'status_label') and self.status_label is not None:
                                self.status_label.setText(f"Saved recording to: {saved_path}")
                                app_logger.debug("Status label updated with save path")
                            else:
                                app_logger.warning("Status label not available for update")
                        except Exception as status_error:
                            app_logger.warning(f"Failed to update status label: {status_error}")
                        
                        # Track recording for current part
                        try:
                            if not hasattr(self, 'part_recordings'):
                                self.part_recordings = {}
                                app_logger.debug("Initialized part_recordings dictionary")
                            
                            if not isinstance(self.part_recordings, dict):
                                app_logger.warning("part_recordings is not a dict, reinitializing")
                                self.part_recordings = {}
                            
                            current_part = getattr(self, 'current_part', 0)
                            if current_part not in self.part_recordings:
                                self.part_recordings[current_part] = []
                            
                            self.part_recordings[current_part].append(saved_path)
                            app_logger.info(f"Recording tracked for part {current_part + 1}: {saved_path}")
                            
                        except Exception as tracking_error:
                            app_logger.error(f"Failed to track recording: {tracking_error}", exc_info=True)
                            # Non-critical, continue
                        
                    except Exception as finalize_error:
                        app_logger.error(f"Failed to finalize WAV file: {finalize_error}", exc_info=True)
                        QMessageBox.warning(self, "Save Error", f"Failed to finalize recording: {finalize_error}")
                        # Continue with cleanup
                else:
                    app_logger.warning("Wave writer not available for finalization")
                    
            except Exception as wav_error:
                app_logger.error(f"Critical error in WAV finalization: {wav_error}", exc_info=True)
                QMessageBox.warning(self, "Save Error", f"Critical error saving recording: {wav_error}")
            
            # Cleanup resources with error handling
            try:
                self.audio_input = None
                self.wave_writer = None
                self.dot_visible = False
                app_logger.debug("Audio resources cleaned up")
            except Exception as cleanup_error:
                app_logger.error(f"Failed to cleanup audio resources: {cleanup_error}", exc_info=True)
            
            # Update recording label with error handling
            try:
                if hasattr(self, 'recording_label') and self.recording_label is not None:
                    try:
                        if hasattr(self, 'record_seconds'):
                            formatted_time = self.format_seconds(self.record_seconds)
                        else:
                            formatted_time = "00:00:00"
                        
                        self.recording_label.setText(f"<span style='color:#95a5a6'>●</span> {formatted_time}")
                        app_logger.debug("Recording label updated after stop")
                    except Exception as format_error:
                        app_logger.warning(f"Failed to format recording time: {format_error}")
                        self.recording_label.setText("<span style='color:#95a5a6'>●</span> Stopped")
                else:
                    app_logger.warning("Recording label not available for update")
            except Exception as label_error:
                app_logger.warning(f"Failed to update recording label: {label_error}")
            
            # Update UI state with error handling
            try:
                self.update_recording_ui_state()
                app_logger.debug("Recording UI state updated after stop")
            except Exception as ui_error:
                app_logger.warning(f"Failed to update recording UI state: {ui_error}")
            
            if saved_path:
                app_logger.info(f"Audio recording stopped and saved successfully: {saved_path}")
            else:
                app_logger.warning("Audio recording stopped but save status unknown")
                
        except Exception as e:
            app_logger.error(f"Critical error in stop_recording: {e}", exc_info=True)
            QMessageBox.critical(self, "Critical Stop Error", 
                               f"Unexpected error stopping recording: {e}")
            
            # Emergency cleanup
            try:
                self.audio_input = None
                self.wave_writer = None
                if hasattr(self, 'record_timer') and self.record_timer is not None:
                    self.record_timer.stop()
                app_logger.debug("Emergency cleanup completed")
            except Exception as emergency_error:
                app_logger.error(f"Emergency cleanup failed: {emergency_error}", exc_info=True)

    def open_recordings_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.recordings_dir))

    # Speaking Timer Methods
    def start_speaking_timer(self):
        """Start the speaking test timer for the current part"""
        try:
            app_logger.info(f"Starting speaking timer for part {getattr(self, 'current_part', 'unknown')}")
            
            # Validate current state
            try:
                if not hasattr(self, 'current_part') or self.current_part is None:
                    self.current_part = 0
                    app_logger.warning("current_part not set, defaulting to 0")
                
                # Validate current_part range
                if not isinstance(self.current_part, int) or self.current_part < 0 or self.current_part > 2:
                    app_logger.warning(f"Invalid current_part: {self.current_part}, defaulting to 0")
                    self.current_part = 0
                
                # Validate required attributes
                if not hasattr(self, 'part2_prep_time'):
                    self.part2_prep_time = 60  # Default 1 minute
                    app_logger.warning("part2_prep_time not set, defaulting to 60 seconds")
                
                if not hasattr(self, 'part_durations') or not isinstance(self.part_durations, (list, tuple)):
                    self.part_durations = [180, 120, 300]  # Default durations
                    app_logger.warning("part_durations not set, using default values")
                    
            except Exception as validation_error:
                app_logger.error(f"Error validating timer state: {validation_error}", exc_info=True)
                # Set safe defaults
                self.current_part = 0
                self.part2_prep_time = 60
                self.part_durations = [180, 120, 300]
            
            # Set phase and time based on current part
            try:
                if self.current_part == 1:  # Part 2 has preparation phase
                    self.current_phase = "preparation"
                    self.speaking_time_remaining = self.part2_prep_time
                    phase_text = "Preparation Phase - Take notes"
                else:
                    self.current_phase = "speaking"
                    # Ensure part_durations has enough elements
                    if len(self.part_durations) > self.current_part:
                        self.speaking_time_remaining = self.part_durations[self.current_part]
                    else:
                        self.speaking_time_remaining = 180  # Default 3 minutes
                        app_logger.warning(f"part_durations missing index {self.current_part}, using default 180 seconds")
                    phase_text = f"Part {self.current_part + 1} - Speaking"
                
                app_logger.debug(f"Timer phase set to '{self.current_phase}' with {self.speaking_time_remaining} seconds")
                
            except Exception as phase_error:
                app_logger.error(f"Error setting timer phase: {phase_error}", exc_info=True)
                # Fallback settings
                self.current_phase = "speaking"
                self.speaking_time_remaining = 180
                phase_text = "Speaking"
            
            # Update phase label with error handling
            try:
                if hasattr(self, 'phase_label') and self.phase_label is not None:
                    self.phase_label.setText(phase_text)
                    app_logger.debug("Phase label updated")
                else:
                    app_logger.warning("Phase label not available for update")
            except Exception as label_error:
                app_logger.warning(f"Failed to update phase label: {label_error}")
            
            # Set timer as active
            try:
                self.speaking_timer_active = True
                app_logger.debug("Speaking timer marked as active")
            except Exception as active_error:
                app_logger.warning(f"Failed to set timer active state: {active_error}")
            
            # Start the timer with error handling
            try:
                if not hasattr(self, 'speaking_timer') or self.speaking_timer is None:
                    app_logger.error("Speaking timer not initialized")
                    QMessageBox.warning(self, "Timer Error", "Speaking timer is not available")
                    return
                
                self.speaking_timer.start()
                app_logger.debug("Speaking timer started")
                
            except Exception as timer_error:
                app_logger.error(f"Failed to start speaking timer: {timer_error}", exc_info=True)
                QMessageBox.warning(self, "Timer Error", f"Failed to start timer: {timer_error}")
                return
            
            # Update display and controls
            try:
                self.update_timer_display()
                app_logger.debug("Timer display updated")
            except Exception as display_error:
                app_logger.warning(f"Failed to update timer display: {display_error}")
            
            try:
                self.update_timer_controls()
                app_logger.debug("Timer controls updated")
            except Exception as controls_error:
                app_logger.warning(f"Failed to update timer controls: {controls_error}")
            
            # Update status label with error handling
            try:
                if hasattr(self, 'status_label') and self.status_label is not None:
                    if self.current_part == 1 and self.current_phase == "preparation":
                        status_text = "Preparation time started. Take notes for your 2-minute talk."
                    else:
                        status_text = f"Part {self.current_part + 1} timer started. Begin speaking."
                    
                    self.status_label.setText(status_text)
                    app_logger.debug("Status label updated")
                else:
                    app_logger.warning("Status label not available for update")
            except Exception as status_error:
                app_logger.warning(f"Failed to update status label: {status_error}")
            
            app_logger.info(f"Speaking timer started successfully for part {self.current_part + 1}, phase: {self.current_phase}")
            
        except Exception as e:
            app_logger.error(f"Critical error in start_speaking_timer: {e}", exc_info=True)
            QMessageBox.critical(self, "Critical Timer Error", 
                               f"Unexpected error starting timer: {e}")
            
            # Emergency fallback
            try:
                self.speaking_timer_active = False
                if hasattr(self, 'speaking_timer') and self.speaking_timer is not None:
                    self.speaking_timer.stop()
                app_logger.debug("Emergency timer cleanup completed")
            except Exception as emergency_error:
                app_logger.error(f"Emergency timer cleanup failed: {emergency_error}", exc_info=True)

    def pause_speaking_timer(self):
        """Pause the speaking test timer"""
        if self.speaking_timer_active:
            self.speaking_timer.stop()
            self.speaking_timer_active = False
            self.phase_label.setText(f"{self.phase_label.text()} - PAUSED")
            self.status_label.setText("Timer paused.")
        else:
            self.speaking_timer.start()
            self.speaking_timer_active = True
            phase_text = self.phase_label.text().replace(" - PAUSED", "")
            self.phase_label.setText(phase_text)
            self.status_label.setText("Timer resumed.")
        
        self.update_timer_controls()

    def reset_speaking_timer(self):
        """Reset the speaking test timer"""
        self.speaking_timer.stop()
        self.speaking_timer_active = False
        self.current_phase = "ready"
        
        # Reset to initial time for current part
        if self.current_part == 1:
            self.speaking_time_remaining = self.part2_prep_time
        else:
            self.speaking_time_remaining = self.part_durations[self.current_part]
        
        self.update_timer_display()
        self.update_timer_controls()
        self.phase_label.setText("Ready to start")
        self.status_label.setText("Timer reset. Ready to start.")

    def update_speaking_timer(self):
        """Update the speaking timer countdown"""
        try:
            # Validate timer state
            try:
                if not hasattr(self, 'speaking_time_remaining'):
                    app_logger.warning("speaking_time_remaining not set, initializing to 0")
                    self.speaking_time_remaining = 0
                
                if not isinstance(self.speaking_time_remaining, (int, float)):
                    app_logger.warning(f"Invalid speaking_time_remaining type: {type(self.speaking_time_remaining)}, converting to int")
                    try:
                        self.speaking_time_remaining = int(self.speaking_time_remaining)
                    except (ValueError, TypeError):
                        self.speaking_time_remaining = 0
                        
            except Exception as validation_error:
                app_logger.error(f"Error validating timer state: {validation_error}", exc_info=True)
                self.speaking_time_remaining = 0
            
            # Update timer countdown
            if self.speaking_time_remaining > 0:
                try:
                    self.speaking_time_remaining -= 1
                    app_logger.debug(f"Timer updated: {self.speaking_time_remaining} seconds remaining")
                except Exception as countdown_error:
                    app_logger.error(f"Error updating countdown: {countdown_error}", exc_info=True)
                    self.speaking_time_remaining = 0
                
                # Update display
                try:
                    self.update_timer_display()
                except Exception as display_error:
                    app_logger.warning(f"Failed to update timer display: {display_error}")
            else:
                # Time's up for current phase
                try:
                    app_logger.info("Timer completed, handling completion")
                    self.handle_timer_completion()
                except Exception as completion_error:
                    app_logger.error(f"Error handling timer completion: {completion_error}", exc_info=True)
                    # Emergency stop timer
                    try:
                        if hasattr(self, 'speaking_timer') and self.speaking_timer is not None:
                            self.speaking_timer.stop()
                        self.speaking_timer_active = False
                        app_logger.debug("Emergency timer stop completed")
                    except Exception as emergency_error:
                        app_logger.error(f"Emergency timer stop failed: {emergency_error}", exc_info=True)
                        
        except Exception as e:
            app_logger.error(f"Critical error in update_speaking_timer: {e}", exc_info=True)
            # Emergency cleanup
            try:
                if hasattr(self, 'speaking_timer') and self.speaking_timer is not None:
                    self.speaking_timer.stop()
                self.speaking_timer_active = False
                app_logger.debug("Critical error cleanup completed")
            except Exception as cleanup_error:
                app_logger.error(f"Critical error cleanup failed: {cleanup_error}", exc_info=True)

    def handle_timer_completion(self):
        """Handle timer completion for different phases"""
        try:
            app_logger.info(f"Handling timer completion for part {getattr(self, 'current_part', 'unknown')}, phase: {getattr(self, 'current_phase', 'unknown')}")
            
            # Validate current state
            try:
                if not hasattr(self, 'current_part') or self.current_part is None:
                    self.current_part = 0
                    app_logger.warning("current_part not set during completion, defaulting to 0")
                
                if not hasattr(self, 'current_phase') or not self.current_phase:
                    self.current_phase = "speaking"
                    app_logger.warning("current_phase not set during completion, defaulting to speaking")
                    
            except Exception as validation_error:
                app_logger.error(f"Error validating completion state: {validation_error}", exc_info=True)
                self.current_part = 0
                self.current_phase = "speaking"
            
            # Handle phase transitions
            if self.current_part == 1 and self.current_phase == "preparation":
                try:
                    app_logger.info("Transitioning from preparation to speaking phase for Part 2")
                    
                    # Transition from preparation to speaking phase
                    self.current_phase = "speaking"
                    
                    # Set speaking time with validation
                    try:
                        if hasattr(self, 'part2_speaking_time') and isinstance(self.part2_speaking_time, (int, float)):
                            self.speaking_time_remaining = self.part2_speaking_time
                        else:
                            self.speaking_time_remaining = 120  # Default 2 minutes
                            app_logger.warning("part2_speaking_time not available, using default 120 seconds")
                    except Exception as time_error:
                        app_logger.warning(f"Error setting speaking time: {time_error}")
                        self.speaking_time_remaining = 120
                    
                    # Update phase label
                    try:
                        if hasattr(self, 'phase_label') and self.phase_label is not None:
                            self.phase_label.setText("Part 2 - Speaking (2 minutes)")
                            app_logger.debug("Phase label updated for speaking phase")
                        else:
                            app_logger.warning("Phase label not available for update")
                    except Exception as label_error:
                        app_logger.warning(f"Failed to update phase label: {label_error}")
                    
                    # Update status label
                    try:
                        if hasattr(self, 'status_label') and self.status_label is not None:
                            self.status_label.setText("Preparation time finished. Begin your 2-minute talk now.")
                            app_logger.debug("Status label updated for speaking phase")
                        else:
                            app_logger.warning("Status label not available for update")
                    except Exception as status_error:
                        app_logger.warning(f"Failed to update status label: {status_error}")
                    
                    # Update timer display
                    try:
                        self.update_timer_display()
                        app_logger.debug("Timer display updated for speaking phase")
                    except Exception as display_error:
                        app_logger.warning(f"Failed to update timer display: {display_error}")
                        
                except Exception as transition_error:
                    app_logger.error(f"Error during phase transition: {transition_error}", exc_info=True)
                    # Fallback: stop timer
                    try:
                        if hasattr(self, 'speaking_timer') and self.speaking_timer is not None:
                            self.speaking_timer.stop()
                        self.speaking_timer_active = False
                    except Exception as fallback_error:
                        app_logger.error(f"Fallback timer stop failed: {fallback_error}", exc_info=True)
            else:
                try:
                    app_logger.info(f"Completing speaking phase for part {self.current_part + 1}")
                    
                    # Speaking phase completed - stop timer
                    try:
                        if hasattr(self, 'speaking_timer') and self.speaking_timer is not None:
                            self.speaking_timer.stop()
                            app_logger.debug("Speaking timer stopped")
                        else:
                            app_logger.warning("Speaking timer not available for stopping")
                    except Exception as stop_error:
                        app_logger.error(f"Failed to stop speaking timer: {stop_error}", exc_info=True)
                    
                    # Set timer as inactive
                    try:
                        self.speaking_timer_active = False
                        app_logger.debug("Speaking timer marked as inactive")
                    except Exception as active_error:
                        app_logger.warning(f"Failed to set timer inactive: {active_error}")
                    
                    # Set phase as completed
                    try:
                        self.current_phase = "completed"
                        app_logger.debug("Phase marked as completed")
                    except Exception as phase_error:
                        app_logger.warning(f"Failed to set phase as completed: {phase_error}")
                    
                    # Update phase label
                    try:
                        if hasattr(self, 'phase_label') and self.phase_label is not None:
                            self.phase_label.setText("Time's Up!")
                            app_logger.debug("Phase label updated to 'Time's Up!'")
                        else:
                            app_logger.warning("Phase label not available for completion update")
                    except Exception as label_error:
                        app_logger.warning(f"Failed to update phase label for completion: {label_error}")
                    
                    # Update status label
                    try:
                        if hasattr(self, 'status_label') and self.status_label is not None:
                            self.status_label.setText(f"Part {self.current_part + 1} completed. Time's up!")
                            app_logger.debug("Status label updated for completion")
                        else:
                            app_logger.warning("Status label not available for completion update")
                    except Exception as status_error:
                        app_logger.warning(f"Failed to update status label for completion: {status_error}")
                    
                    # Update timer controls
                    try:
                        self.update_timer_controls()
                        app_logger.debug("Timer controls updated for completion")
                    except Exception as controls_error:
                        app_logger.warning(f"Failed to update timer controls: {controls_error}")
                    
                    # Flash the timer display with error handling
                    try:
                        if hasattr(self, 'countdown_display') and self.countdown_display is not None:
                            self.countdown_display.setStyleSheet("""
                                color: white;
                                font-size: 18px;
                                font-weight: bold;
                                font-family: Consolas, monospace;
                                background-color: #e74c3c;
                                padding: 5px 10px;
                                border-radius: 5px;
                                border: 2px solid #c0392b;
                            """)
                            app_logger.debug("Timer display styled for completion")
                        else:
                            app_logger.warning("Countdown display not available for styling")
                    except Exception as style_error:
                        app_logger.warning(f"Failed to style countdown display: {style_error}")
                        
                except Exception as completion_error:
                    app_logger.error(f"Error during speaking completion: {completion_error}", exc_info=True)
                    # Emergency cleanup
                    try:
                        if hasattr(self, 'speaking_timer') and self.speaking_timer is not None:
                            self.speaking_timer.stop()
                        self.speaking_timer_active = False
                        app_logger.debug("Emergency completion cleanup done")
                    except Exception as emergency_error:
                        app_logger.error(f"Emergency completion cleanup failed: {emergency_error}", exc_info=True)
            
            app_logger.info("Timer completion handled successfully")
            
        except Exception as e:
            app_logger.error(f"Critical error in handle_timer_completion: {e}", exc_info=True)
            QMessageBox.critical(self, "Critical Timer Error", 
                               f"Unexpected error handling timer completion: {e}")
            
            # Emergency cleanup
            try:
                if hasattr(self, 'speaking_timer') and self.speaking_timer is not None:
                    self.speaking_timer.stop()
                self.speaking_timer_active = False
                self.current_phase = "completed"
                app_logger.debug("Critical error cleanup completed")
            except Exception as cleanup_error:
                app_logger.error(f"Critical error cleanup failed: {cleanup_error}", exc_info=True)

    def update_timer_display(self):
        """Update the visual countdown display"""
        minutes = self.speaking_time_remaining // 60
        seconds = self.speaking_time_remaining % 60
        time_text = f"{minutes:02d}:{seconds:02d}"
        
        self.countdown_display.setText(time_text)
        
        # Color coding based on time remaining
        if self.speaking_time_remaining <= 30:  # Last 30 seconds
            color = "#e74c3c"  # Red
            bg_color = "#fadbd8"
            border_color = "#e74c3c"
        elif self.speaking_time_remaining <= 60:  # Last minute
            color = "#f39c12"  # Orange
            bg_color = "#fef5e7"
            border_color = "#f39c12"
        else:
            color = "#2c3e50"  # Normal
            bg_color = "#ecf0f1"
            border_color = "#bdc3c7"
        
        self.countdown_display.setStyleSheet(f"""
            color: {color};
            font-size: 18px;
            font-weight: bold;
            font-family: Consolas, monospace;
            background-color: {bg_color};
            padding: 5px 10px;
            border-radius: 5px;
            border: 2px solid {border_color};
        """)

    def update_timer_controls(self):
        """Update timer control button states"""
        if self.current_phase == "ready":
            self.start_timer_btn.setText("Start Timer")
            self.start_timer_btn.setEnabled(True)
            self.pause_timer_btn.setEnabled(False)
            self.reset_timer_btn.setEnabled(True)
        elif self.current_phase in ["preparation", "speaking"]:
            if self.speaking_timer_active:
                self.start_timer_btn.setEnabled(False)
                self.pause_timer_btn.setText("Pause")
                self.pause_timer_btn.setEnabled(True)
            else:
                self.start_timer_btn.setEnabled(False)
                self.pause_timer_btn.setText("Resume")
                self.pause_timer_btn.setEnabled(True)
            self.reset_timer_btn.setEnabled(True)
        elif self.current_phase == "completed":
            self.start_timer_btn.setEnabled(False)
            self.pause_timer_btn.setEnabled(False)
            self.reset_timer_btn.setEnabled(True)
    
    def refresh_resources(self):
        """Refresh the UI when resources change."""
        try:
            # Reload available tests
            self.load_available_tests()
            
            # Refresh current content if a test is loaded
            if hasattr(self, 'current_test') and self.current_test:
                self.load_current_content()
                
        except Exception as e:
            from logger import app_logger
            app_logger.error("Error refreshing speaking test resources", exc_info=True)

    def finish_test(self):
        """Finish the speaking test and save results to JSON"""
        try:
            reply = QMessageBox.question(self, "Finish Test",
                                       "Are you sure you want to finish the Speaking test?\n\n"
                                       "This will save your recordings and end the test.",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Stop any ongoing recording
                if self.audio_input is not None:
                    self.stop_recording()
                
                # Save answers to JSON
                self.save_answers_to_json()
                
                # Show completion message
                QMessageBox.information(self, 'Test Completed', 
                                      'Your Speaking test has been completed and saved!')
                
        except Exception as e:
            app_logger.error(f"Error finishing speaking test: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to finish test: {e}")

    def save_answers_to_json(self):
        """Save speaking test results including recording paths to JSON file"""
        try:
            # Create results directory
            results_dir = os.path.join(self.base_dir, 'results', 'speaking')
            os.makedirs(results_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"speaking_test_{self.selected_book}_{self.current_test}_{timestamp}.json"
            filepath = os.path.join(results_dir, filename)
            
            # Prepare test data
            test_data = {
                "test_type": "speaking",
                "book": self.selected_book,
                "test_number": self.current_test,
                "timestamp": datetime.datetime.now().isoformat(),
                "recordings": {},
                "metadata": {
                    "total_parts": self.total_parts,
                    "audio_supported": self.audio_supported,
                    "recordings_directory": self.recordings_dir
                }
            }
            
            # Add recordings for each part
            for part_num in range(self.total_parts):
                part_key = f"part_{part_num + 1}"
                if part_num in self.part_recordings:
                    # Convert absolute paths to relative paths for portability
                    relative_paths = []
                    for recording_path in self.part_recordings[part_num]:
                        try:
                            # Get relative path from base directory
                            rel_path = os.path.relpath(recording_path, self.base_dir)
                            relative_paths.append(rel_path)
                        except ValueError:
                            # If relative path fails, use absolute path
                            relative_paths.append(recording_path)
                    
                    test_data["recordings"][part_key] = {
                        "recording_paths": relative_paths,
                        "recording_count": len(relative_paths)
                    }
                else:
                    test_data["recordings"][part_key] = {
                        "recording_paths": [],
                        "recording_count": 0
                    }
            
            # Save to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2, ensure_ascii=False)
            
            app_logger.info(f"Speaking test results saved to: {filepath}")
            
        except Exception as e:
            app_logger.error(f"Error saving speaking test results: {e}", exc_info=True)
            raise