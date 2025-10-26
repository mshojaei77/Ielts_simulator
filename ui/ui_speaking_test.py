import os
import struct
import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import app_logger
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

    def __init__(self):
        super().__init__()
        self.current_part = 0  # 0=Part1, 1=Part2, 2=Part3
        self.current_test = 1  # Default to Test 1
        self.total_parts = 3
        self.audio_supported = QAudioInput is not None and QAudioFormat is not None

        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.speaking_dir = os.path.join(self.base_dir, 'resources', 'Cambridge20', 'speaking')
        self.recordings_dir = os.path.join(self.base_dir, 'recordings', 'speaking')
        os.makedirs(self.recordings_dir, exist_ok=True)

        # Recording state
        self.audio_input = None
        self.wave_writer = None
        self.record_timer = QTimer(self)
        self.record_timer.setInterval(1000)
        self.record_timer.timeout.connect(self.update_recording_timer)
        self.record_seconds = 0
        self.dot_visible = False  # blinking indicator

        # Load available tests
        self.available_tests = self.load_available_tests()
        
        self.apply_style()
        self.init_ui()
        self.load_current_content()
        self.update_navigation_buttons()
        self.update_recording_ui_state()

    def load_available_tests(self):
        """Load available speaking tests from the directory"""
        tests = []
        try:
            if os.path.exists(self.speaking_dir):
                files = os.listdir(self.speaking_dir)
                test_numbers = set()
                for filename in files:
                    if filename.startswith('Test-') and filename.endswith('.html'):
                        parts = filename.split('-')
                        if len(parts) >= 2:
                            try:
                                test_num = int(parts[1])
                                test_numbers.add(test_num)
                            except ValueError:
                                continue
                tests = sorted(list(test_numbers))
        except Exception as e:
            app_logger.debug(f"Error loading available tests: {e}")
        
        # If no tests found, default to Test 1
        return tests if tests else [1]

    def get_part_file_path(self, test_num, part_num):
        """Get the file path for a specific test and part"""
        filename = f"Test-{test_num}-Part-{part_num + 1}.html"
        return os.path.join(self.speaking_dir, filename)

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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar with test selection and part navigation
        self.create_top_bar()
        main_layout.addWidget(self.top_bar)

        # Content area
        self.create_content_area()
        main_layout.addWidget(self.content_frame, 1)

        # Navigation area
        self.create_navigation_area()
        main_layout.addWidget(self.nav_area)

        self.setLayout(main_layout)

    def create_top_bar(self):
        """Create enhanced top bar with test selection and part buttons"""
        self.top_bar = QWidget()
        self.top_bar.setObjectName('top_bar')
        self.top_bar.setFixedHeight(50)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(15, 5, 15, 5)
        top_layout.setSpacing(15)

        # Left section: Test selection
        left_section = QWidget()
        left_layout = QHBoxLayout(left_section)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        test_label = QLabel("Cambridge IELTS Speaking Test")
        test_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        self.test_combo = QComboBox()
        for test_num in self.available_tests:
            self.test_combo.addItem(f"Test {test_num}")
        self.test_combo.setCurrentText(f"Test {self.current_test}")
        self.test_combo.currentTextChanged.connect(self.on_test_changed)

        left_layout.addWidget(test_label)
        left_layout.addWidget(self.test_combo)

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

        # Left side: Status info
        self.status_label = QLabel("Ready to record. Use Start and Stop to capture your answers.")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        
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
        
        nav_buttons_layout.addWidget(self.back_button)
        nav_buttons_layout.addWidget(self.next_button)
        
        nav_layout.addWidget(self.status_label)
        nav_layout.addStretch()
        nav_layout.addWidget(record_panel)
        nav_layout.addStretch()
        nav_layout.addWidget(nav_buttons)

    def on_test_changed(self, test_text):
        """Handle test selection change"""
        try:
            # Extract test number from text like "Test 1"
            self.current_test = int(test_text.split()[-1])
            self.load_current_content()
        except (ValueError, IndexError):
            app_logger.debug(f"Error parsing test number from: {test_text}")

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
        if not self.audio_supported:
            QMessageBox.warning(self, "Recording Unavailable", "QtMultimedia is not available. Please install PyQt5 with QtMultimedia support.")
            return
        if self.audio_input is not None:
            return  # already recording

        fmt = self.get_default_audio_format()
        if fmt is None:
            QMessageBox.warning(self, "No Input Device", "No audio input device found.")
            return

        path = self.generate_recording_path()
        self.wave_writer = WavFileWriter(path, fmt.sampleRate(), fmt.channelCount(), fmt.sampleSize())
        if not self.wave_writer.open():
            QMessageBox.critical(self, "File Error", f"Cannot open file for writing: {path}")
            self.wave_writer = None
            return

        try:
            # Create audio input and start streaming to QFile within WavFileWriter
            self.audio_input = QAudioInput(fmt, self)
            self.audio_input.start(self.wave_writer.file)
        except Exception as e:
            QMessageBox.critical(self, "Recording Error", f"Failed to start recording: {e}")
            self.wave_writer.file.close()
            self.wave_writer = None
            self.audio_input = None
            return

        self.record_seconds = 0
        self.dot_visible = True
        self.recording_label.setText("<span style='color:#E74C3C'>●</span> 00:00:00")
        self.record_timer.start()
        self.update_recording_ui_state()

    def stop_recording(self):
        if self.audio_input is None:
            return
        try:
            self.audio_input.stop()
        except Exception as e:
            QMessageBox.warning(self, "Stop Error", f"Failed to stop: {e}")
        finally:
            self.record_timer.stop()
            # Finalize WAV header
            try:
                if self.wave_writer is not None:
                    self.wave_writer.finalize()
                    saved_path = self.wave_writer.path
                    self.status_label.setText(f"Saved recording to: {saved_path}")
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Failed to finalize WAV: {e}")
            
            # Cleanup
            self.audio_input = None
            self.wave_writer = None
            self.dot_visible = False
            self.recording_label.setText(f"<span style='color:#95a5a6'>●</span> {self.format_seconds(self.record_seconds)}")
            self.update_recording_ui_state()

    def open_recordings_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.recordings_dir))