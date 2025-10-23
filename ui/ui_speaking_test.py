import os
import wave
import subprocess
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, 
    QFrame, QGroupBox, QTextEdit, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtMultimedia import QAudioInput, QAudioFormat, QAudioDeviceInfo
from PyQt5.QtGui import QFont

class SpeakingTestUI(QWidget):
    """
    Real IELTS Speaking Test Simulator with maximum exam simulation
    - Enforced timing for each part
    - No back/skip/re-record capabilities (real exam conditions)
    - Prominent recording interface with guidance
    - Auto-start/stop timing enforcement
    """

    def __init__(self):
        super().__init__()
        self.current_part = 0  # 0=Part1, 1=Part2, 2=Part3
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.speaking_dir = os.path.join(self.base_dir, 'resources', 'Cambridge20', 'speaking')
        self.part_files = [
            os.path.join(self.speaking_dir, 'Test-1-Part-1.html'),
            os.path.join(self.speaking_dir, 'Test-1-Part-2.html'),
            os.path.join(self.speaking_dir, 'Test-1-Part-3.html'),
        ]
        
        # Real exam timing (in seconds)
        self.part_durations = [300, 240, 300]  # Part 1: 5min, Part 2: 4min, Part 3: 5min
        self.current_time_left = 0
        self.part_started = [False, False, False]  # Track which parts have been started
        self.part_skipped = [False, False, False]  # Track which parts have been skipped
        self.exam_timer = QTimer(self)
        self.exam_timer.timeout.connect(self.update_countdown)
        
        # Recording state
        self.is_recording = False
        self.audio_input = None
        self.audio_io = None
        self.wave_fp = None
        self.audio_timer = None
        self.temp_wav_path = None
        self.final_mp3_path = None
        
        self.storage_dir = self.get_storage_dir()

        self.apply_style()
        self.init_ui()
        self.load_part(self.current_part)

    def apply_style(self):
        self.setStyleSheet("""
            QWidget { 
                background-color: #ffffff; 
                font-family: Arial, sans-serif; 
                font-size: 12px; 
                color: #333; 
            }
            #top_bar { 
                background-color: #f8f9fa; 
                border-bottom: 1px solid #dee2e6; 
                padding: 6px 12px; 
            }
            #recording_section { 
                background-color: #f0f8ff; 
                border: 2px solid #0066cc; 
                border-radius: 8px; 
                padding: 15px; 
                margin: 8px; 
            }
            #countdown_display {
                background-color: #ff4444;
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 8px 12px;
                border-radius: 5px;
                text-align: center;
                min-width: 80px;
            }
            QPushButton { 
                background-color: #e0e0e0; 
                border: 1px solid #c0c0c0; 
                border-radius: 3px; 
                padding: 6px 12px; 
                font-size: 12px; 
                margin: 2px;
            }
            QPushButton:hover { background-color: #d8d8d8; }
            QPushButton:disabled { color: #999; background-color: #f5f5f5; }
            QPushButton.primary { 
                background-color: #0066cc; 
                color: #fff; 
                border: 1px solid #0052a3; 
                font-weight: bold; 
            }
            QPushButton.primary:hover { background-color: #0052a3; }
            QPushButton.record { 
                background-color: #dc3545; 
                color: white; 
                font-size: 14px; 
                font-weight: bold; 
                padding: 10px 20px; 
                border-radius: 6px; 
                margin: 4px;
            }
            QPushButton.record:hover { background-color: #c82333; }
            QPushButton.stop { 
                background-color: #6c757d; 
                color: white; 
                font-size: 14px; 
                font-weight: bold; 
                padding: 10px 20px; 
                border-radius: 6px; 
                margin: 4px;
            }
            QPushButton.skip { 
                background-color: #ffc107; 
                color: #212529; 
                font-size: 12px; 
                font-weight: bold; 
                padding: 8px 16px; 
                border-radius: 4px; 
                margin: 4px;
            }
            QPushButton.skip:hover { background-color: #e0a800; }
            QPushButton.tab { 
                background-color: #e9ecef; 
                border: 1px solid #ced4da; 
                padding: 6px 12px; 
                margin-right: 4px; 
                border-radius: 3px; 
            }
            QPushButton.tab:checked { 
                background-color: #0066cc; 
                color: #fff; 
                border-color: #0066cc; 
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #0066cc;
                border: 2px solid #0066cc;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                background-color: #f8f9fa;
            }
        """)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Top bar: Part tabs + countdown timer + skip button
        top_bar = QWidget()
        top_bar.setObjectName('top_bar')
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 4, 10, 4)
        top_layout.setSpacing(8)

        self.part_tabs = []
        for i in range(3):
            tab = QPushButton(f"Part {i+1}")
            tab.setCheckable(True)
            tab.setProperty('class', 'tab')
            tab.setObjectName('tab')
            # Disable part switching in real exam mode
            tab.setEnabled(False)
            self.part_tabs.append(tab)
            top_layout.addWidget(tab)
        self.part_tabs[0].setChecked(True)

        # Skip part button
        self.skip_part_btn = QPushButton("⏭️ Skip Part (Score Penalty)")
        self.skip_part_btn.setProperty('class', 'skip')
        self.skip_part_btn.clicked.connect(self.skip_current_part)
        top_layout.addWidget(self.skip_part_btn)

        top_layout.addStretch()
        
        # Always visible countdown timer
        self.countdown_label = QLabel("05:00")
        self.countdown_label.setObjectName('countdown_display')
        top_layout.addWidget(self.countdown_label)

        main_layout.addWidget(top_bar)

        # Content: WebEngineView for HTML slides with better space utilization
        content_frame = QFrame()
        content_frame.setFrameStyle(QFrame.StyledPanel)
        content_frame.setStyleSheet("border: 1px solid #dee2e6; border-radius: 4px; background-color: #ffffff;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.web_view.setMinimumHeight(400)  # Ensure minimum height to fill space
        self.web_view.setStyleSheet("border: none; background-color: #ffffff;")
        self.web_view.loadFinished.connect(self.on_load_finished)
        
        content_layout.addWidget(self.web_view)
        main_layout.addWidget(content_frame, 1)

        # Recording Section (Compact and below content)
        self.create_recording_section()
        main_layout.addWidget(self.recording_section)

        self.setLayout(main_layout)

    def create_recording_section(self):
        self.recording_section = QGroupBox("🎤 IELTS Speaking Test Recording")
        self.recording_section.setObjectName('recording_section')
        recording_layout = QVBoxLayout(self.recording_section)
        recording_layout.setSpacing(8)
        recording_layout.setContentsMargins(12, 15, 12, 12)

        # Recording guidance (compact one-page card without scrolling)
        guidance_frame = QFrame()
        guidance_frame.setFrameStyle(QFrame.Box)
        guidance_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        guidance_layout = QVBoxLayout(guidance_frame)
        guidance_layout.setContentsMargins(8, 8, 8, 8)
        guidance_layout.setSpacing(4)
        
        # Title
        title_label = QLabel("📋 Real Exam Instructions:")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #2c3e50; margin-bottom: 4px;")
        guidance_layout.addWidget(title_label)
        
        # Instructions in a compact format
        instructions = [
            "• Click \"Start Recording\" to begin speaking • Speak clearly for the full duration",
            "• No pausing or re-recording - just like the real exam • Skip parts with score penalty if needed", 
            "• Recording auto-stops when time expires • Responses saved to Desktop/IELTS_Practice as MP3"
        ]
        
        for instruction in instructions:
            inst_label = QLabel(instruction)
            inst_label.setStyleSheet("font-size: 11px; line-height: 1.2; color: #495057; margin: 1px 0;")
            inst_label.setWordWrap(True)
            guidance_layout.addWidget(inst_label)
        
        recording_layout.addWidget(guidance_frame)

        # Recording controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.rec_status = QLabel("🔴 Status: Ready to Record")
        self.rec_status.setStyleSheet("font-size: 13px; font-weight: bold; color: #dc3545;")
        controls_layout.addWidget(self.rec_status)
        
        controls_layout.addStretch()
        
        self.start_rec_btn = QPushButton("🎤 Start Recording")
        self.start_rec_btn.setProperty('class', 'record')
        self.start_rec_btn.clicked.connect(self.start_recording_and_timer)
        controls_layout.addWidget(self.start_rec_btn)
        
        recording_layout.addLayout(controls_layout)

        # Progress bar for visual feedback
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(8)
        recording_layout.addWidget(self.progress_bar)

    def skip_current_part(self):
        """Skip current part with score penalty warning"""
        if self.current_part >= 2:  # Already on last part
            return
            
        reply = QMessageBox.question(
            self, 
            'Skip Part Warning', 
            f'Are you sure you want to skip Part {self.current_part + 1}?\n\n'
            f'⚠️ WARNING: Skipping will result in a significant score penalty!\n'
            f'• You will receive 0 points for this part\n'
            f'• This will negatively impact your overall speaking score\n'
            f'• Consider attempting the questions even if difficult\n\n'
            f'Skip anyway?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Mark part as skipped
            self.part_skipped[self.current_part] = True
            
            # Stop current recording if active
            if self.is_recording:
                self.stop_recording()
            
            # Stop timer
            if self.exam_timer.isActive():
                self.exam_timer.stop()
            
            # Move to next part
            if self.current_part < 2:
                self.current_part += 1
                self.part_tabs[self.current_part].setChecked(True)
                self.part_tabs[self.current_part - 1].setChecked(False)
                self.load_part(self.current_part)
                self.progress_bar.setVisible(False)
                
                # Reset for next part
                self.rec_status.setText(f"⚠️ Part {self.current_part} Skipped - Ready for Part {self.current_part + 1}")
                self.start_rec_btn.setEnabled(True)
                
                # Update skip button
                if self.current_part >= 2:
                    self.skip_part_btn.setEnabled(False)
                    self.skip_part_btn.setText("⏭️ Last Part")
                
                # Disable navigation for the new part until recording starts
                self.disable_navigation_until_recording()
            else:
                self.finish_exam()

    def start_recording_and_timer(self):
        """Start both recording and exam timer for real exam simulation"""
        # Preflight checks: ensure ffmpeg is available and disk space is sufficient
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            self.rec_status.setText("❌ ffmpeg not found. Please install ffmpeg to save MP3 recordings.")
            return
        if not self.check_disk_space():
            self.rec_status.setText("❌ Insufficient disk space in IELTS_Practice folder.")
            return

        if not self.part_started[self.current_part]:
            self.part_started[self.current_part] = True
            self.current_time_left = self.part_durations[self.current_part]
            self.progress_bar.setMaximum(self.part_durations[self.current_part])
            self.progress_bar.setVisible(True)
            self.exam_timer.start(1000)  # Update every second
            
        self.start_recording()
        
        # Enable navigation when recording starts (but remove Previous button)
        self.enable_navigation_after_recording_start()

    def enable_navigation_after_recording_start(self):
        """Enable Next button and remove Previous button when recording starts"""
        js_code = """
        // Set the global flag to indicate recording has started
        window.recordingStarted = true;
        
        // Enable Next buttons and completely remove Previous buttons
        function enableNavigationAfterRecording() {
            const allButtons = document.querySelectorAll('button');
            allButtons.forEach(btn => {
                // Check for Next buttons by onclick content or data attributes
                if (btn.onclick && (
                    btn.onclick.toString().includes('nextSection') ||
                    btn.onclick.toString().includes('nextSlide') ||
                    btn.onclick.toString().includes('preventDefault')
                )) {
                    // Check if this is a disabled Next button
                    if (btn.onclick.toString().includes('preventDefault') && 
                        btn.onclick.toString().includes('start recording first')) {
                        
                        // Enable Next buttons and restore original functionality
                        btn.disabled = false;
                        btn.style.opacity = '1';
                        btn.style.cursor = 'pointer';
                        
                        // Restore original onclick if it was stored
                        if (btn.originalOnclick) {
                            btn.onclick = btn.originalOnclick;
                        } else {
                            // Fallback: try to restore from global functions
                            const originalNextSection = window.originalNextSection || window.nextSection;
                            const originalNextSlide = window.originalNextSlide || window.nextSlide;
                            
                            if (originalNextSection) {
                                btn.onclick = function() { originalNextSection(); };
                            } else if (originalNextSlide) {
                                btn.onclick = function() { originalNextSlide(); };
                            }
                        }
                    }
                } else if (btn.onclick && (
                    btn.onclick.toString().includes('previousSection') ||
                    btn.onclick.toString().includes('prevSlide')
                )) {
                    // Completely remove Previous buttons
                    btn.style.display = 'none';
                    btn.remove();
                }
            });
            
            // Also check for buttons with specific classes or text
            const navButtons = document.querySelectorAll('.btn-secondary, .btn-primary, button[class*="nav"], button[class*="back"], button[class*="next"]');
            navButtons.forEach(btn => {
                if (btn.textContent.toLowerCase().includes('next')) {
                    // Check if this is a disabled Next button
                    if (btn.onclick && btn.onclick.toString().includes('preventDefault') && 
                        btn.onclick.toString().includes('start recording first')) {
                        
                        // Enable Next buttons
                        btn.disabled = false;
                        btn.style.opacity = '1';
                        btn.style.cursor = 'pointer';
                        
                        // Restore original onclick if it was stored
                        if (btn.originalOnclick) {
                            btn.onclick = btn.originalOnclick;
                        } else {
                            // Fallback: try to restore from global functions
                            const originalNextSection = window.originalNextSection || window.nextSection;
                            const originalNextSlide = window.originalNextSlide || window.nextSlide;
                            
                            if (originalNextSection) {
                                btn.onclick = function() { originalNextSection(); };
                            } else if (originalNextSlide) {
                                btn.onclick = function() { originalNextSlide(); };
                            }
                        }
                    }
                } else if (btn.textContent.toLowerCase().includes('previous') ||
                           btn.textContent.toLowerCase().includes('back')) {
                    // Completely remove Previous buttons
                    btn.style.display = 'none';
                    btn.remove();
                }
            });
            
            console.log('Navigation enabled: Next buttons unlocked, Previous buttons removed');
        }
        
        enableNavigationAfterRecording();
        """
        
        self.web_view.page().runJavaScript(js_code)

    def disable_navigation_until_recording(self):
        """Disable Next buttons until recording starts (for new parts)"""
        js_code = """
        // Disable Next buttons until recording starts
        function disableNavigationUntilRecording() {
            const nextButtons = document.querySelectorAll('button[onclick*="nextSection"], button[onclick*="nextSlide"]');
            nextButtons.forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.3';
                btn.style.cursor = 'not-allowed';
                btn.onclick = function(e) { 
                    e.preventDefault(); 
                    e.stopPropagation(); 
                    alert('Please start recording first to unlock navigation.');
                    return false; 
                };
            });
            
            // Also check for buttons with specific classes or text
            const allNavButtons = document.querySelectorAll('.btn-secondary, .btn-primary, button[class*="nav"], button[class*="next"]');
            allNavButtons.forEach(btn => {
                if (btn.textContent.toLowerCase().includes('next')) {
                    btn.disabled = true;
                    btn.style.opacity = '0.3';
                    btn.style.cursor = 'not-allowed';
                    btn.onclick = function(e) { 
                        e.preventDefault(); 
                        e.stopPropagation(); 
                        alert('Please start recording first to unlock navigation.');
                        return false; 
                    };
                }
            });
        }
        
        disableNavigationUntilRecording();
        """
        
        self.web_view.page().runJavaScript(js_code)

    def disable_all_navigation(self):
        """Disable all navigation when exam is complete"""
        js_code = """
        // Disable all navigation buttons
        function disableAllNavigation() {
            const allButtons = document.querySelectorAll('button');
            allButtons.forEach(btn => {
                if (btn.onclick && (
                    btn.onclick.toString().includes('nextSection') ||
                    btn.onclick.toString().includes('nextSlide') ||
                    btn.onclick.toString().includes('previousSection') ||
                    btn.onclick.toString().includes('prevSlide')
                )) {
                    btn.disabled = true;
                    btn.style.opacity = '0.3';
                    btn.style.cursor = 'not-allowed';
                    btn.onclick = function(e) { 
                        e.preventDefault(); 
                        e.stopPropagation(); 
                        alert('Exam is complete. Navigation is disabled.');
                        return false; 
                    };
                }
            });
            
            // Also check for buttons with specific classes or text
            const navButtons = document.querySelectorAll('.btn-secondary, .btn-primary, button[class*="nav"], button[class*="back"], button[class*="next"]');
            navButtons.forEach(btn => {
                if (btn.textContent.toLowerCase().includes('next') || 
                    btn.textContent.toLowerCase().includes('previous') ||
                    btn.textContent.toLowerCase().includes('back')) {
                    btn.disabled = true;
                    btn.style.opacity = '0.3';
                    btn.style.cursor = 'not-allowed';
                    btn.onclick = function(e) { 
                        e.preventDefault(); 
                        e.stopPropagation(); 
                        alert('Exam is complete. Navigation is disabled.');
                        return false; 
                    };
                }
            });
        }
        
        disableAllNavigation();
        """
        
        self.web_view.page().runJavaScript(js_code)

    def auto_advance_part(self):
        """Automatically advance to next part (real exam behavior)"""
        self.current_part += 1
        self.part_tabs[self.current_part].setChecked(True)
        self.part_tabs[self.current_part - 1].setChecked(False)
        self.load_part(self.current_part)
        self.progress_bar.setVisible(False)
        
        # Reset for next part
        self.rec_status.setText("🔴 Status: Ready to Record Next Part")
        self.start_rec_btn.setEnabled(True)
        
        # Disable navigation for the new part until recording starts
        self.disable_navigation_until_recording()

    def finish_exam(self):
        """Handle exam completion"""
        skipped_parts = [i+1 for i, skipped in enumerate(self.part_skipped) if skipped]
        if skipped_parts:
            self.rec_status.setText(f"✅ Exam Complete! Parts {', '.join(map(str, skipped_parts))} were skipped (score penalty applied).")
        else:
            self.rec_status.setText("✅ Exam Complete! All recordings saved.")
            
        self.start_rec_btn.setEnabled(False)
        self.skip_part_btn.setEnabled(False)
        self.countdown_label.setText("DONE")
        self.countdown_label.setStyleSheet("background-color: #28a745; color: white; font-size: 20px; font-weight: bold; padding: 8px 12px; border-radius: 5px;")
        
        # Disable all navigation after exam completion
        self.disable_all_navigation()

    def update_countdown(self):
        """Update countdown timer and auto-advance parts"""
        if self.current_time_left > 0:
            self.current_time_left -= 1
            minutes = self.current_time_left // 60
            seconds = self.current_time_left % 60
            self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
            
            # Update progress bar
            elapsed = self.part_durations[self.current_part] - self.current_time_left
            self.progress_bar.setValue(elapsed)
            
            # Warning colors
            if self.current_time_left <= 30:
                self.countdown_label.setStyleSheet("background-color: #ff0000; color: white; font-size: 24px; font-weight: bold; padding: 10px; border-radius: 5px;")
            elif self.current_time_left <= 60:
                self.countdown_label.setStyleSheet("background-color: #ff8800; color: white; font-size: 24px; font-weight: bold; padding: 10px; border-radius: 5px;")
        else:
            # Time's up - auto advance to next part
            self.exam_timer.stop()
            if self.is_recording:
                self.stop_recording()
            
            if self.current_part < 2:
                self.auto_advance_part()
            else:
                self.finish_exam()

    def load_part(self, part_index: int):
        file_path = self.part_files[part_index]
        if not os.path.exists(file_path):
            html = f"""
                <html><body style='font-family: Arial; padding:20px;'>
                    <h2>Missing content</h2>
                    <p>Could not find: {file_path}</p>
                </body></html>
            """
            self.web_view.setHtml(html)
            return
        url = QUrl.fromLocalFile(os.path.abspath(file_path))
        self.web_view.load(url)

    def on_load_finished(self, ok: bool):
        """Inject CSS to make question fonts bigger and improve readability"""
        if ok:
            css_injection = """
            // Inject CSS to make questions more readable
            var style = document.createElement('style');
            style.textContent = `
                /* Make question text larger and more readable */
                .question, .question-text, h1, h2, h3, h4, h5, h6 {
                    font-size: 18px !important;
                    line-height: 1.4 !important;
                    font-weight: 600 !important;
                    color: #2c3e50 !important;
                    margin-bottom: 12px !important;
                }
                
                /* Make all paragraph text larger */
                p, div, span, li {
                    font-size: 16px !important;
                    line-height: 1.5 !important;
                    color: #34495e !important;
                }
                
                /* Make instruction text stand out */
                .instruction, .instructions, .note {
                    font-size: 17px !important;
                    font-weight: 500 !important;
                    background-color: #f8f9fa !important;
                    padding: 10px !important;
                    border-left: 4px solid #0066cc !important;
                    margin: 10px 0 !important;
                }
                
                /* Improve button visibility */
                button {
                    font-size: 14px !important;
                    padding: 8px 16px !important;
                    margin: 4px !important;
                }
                
                /* Better spacing for content and fill available space */
                body {
                    padding: 15px !important;
                    max-width: none !important;
                    min-height: 100vh !important;
                    margin: 0 !important;
                }
                
                /* Ensure content fills available space */
                html, body {
                    height: 100% !important;
                    overflow-y: auto !important;
                }
                
                /* Reduce excessive margins and padding */
                * {
                    margin-top: 0 !important;
                }
                
                /* Better content distribution */
                .content, .main-content, .question-content {
                    min-height: 300px !important;
                    display: block !important;
                }
                
                /* Make lists more readable */
                ul, ol {
                    padding-left: 25px !important;
                }
                
                li {
                    margin-bottom: 8px !important;
                }
                
                /* Improve table readability if present */
                table {
                    font-size: 15px !important;
                }
                
                th, td {
                    padding: 8px 12px !important;
                }
            `;
            document.head.appendChild(style);
            """
            
            self.web_view.page().runJavaScript(css_injection)
            
            # Disable navigation until recording starts (for new parts)
            if not self.part_started[self.current_part]:
                self.disable_navigation_until_recording()

    def cleanup_recording_resources(self):
        """Stop timers/devices and release resources."""
        try:
            if self.audio_timer:
                self.audio_timer.stop()
                self.audio_timer.deleteLater()
                self.audio_timer = None
        except Exception:
            pass
        try:
            if self.audio_input:
                self.audio_input.stop()
                self.audio_input.deleteLater()
                self.audio_input = None
        except Exception:
            pass
        try:
            if self.wave_fp:
                self.wave_fp.close()
                self.wave_fp = None
        except Exception:
            pass

    def convert_to_mp3(self) -> bool:
        """Convert the temporary WAV file to MP3 using ffmpeg."""
        try:
            ffmpeg_path = shutil.which('ffmpeg')
            if not ffmpeg_path or not os.path.exists(self.temp_wav_path):
                return False
            result = subprocess.run([
                ffmpeg_path, '-y', '-i', os.path.abspath(self.temp_wav_path), os.path.abspath(self.final_mp3_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            return result.returncode == 0 and os.path.exists(self.final_mp3_path)
        except Exception:
            return False

    def start_recording(self):
        if self.is_recording:
            return
        # Setup audio format safely
        try:
            fmt = self.get_valid_audio_format()
            info = QAudioDeviceInfo.defaultInputDevice()
        except Exception as e:
            self.rec_status.setText(f"❌ Audio device/format error: {e}")
            return
        
        # Prepare file paths
        self.temp_wav_path, self.final_mp3_path = self.build_output_paths()
        
        # Ensure no stray timers from prior sessions
        if self.audio_timer:
            try:
                self.audio_timer.stop()
                self.audio_timer.deleteLater()
            except Exception:
                pass
            self.audio_timer = None
        
        # Start audio input (pull mode)
        try:
            self.audio_input = QAudioInput(info, fmt, self)
            self.audio_io = self.audio_input.start()
        except Exception as e:
            self.rec_status.setText(f"❌ Failed to start audio input: {e}")
            return
        
        # Open WAV writer
        try:
            self.wave_fp = wave.open(self.temp_wav_path, 'wb')
            self.wave_fp.setnchannels(fmt.channelCount())
            self.wave_fp.setsampwidth(int(fmt.sampleSize() / 8))
            self.wave_fp.setframerate(fmt.sampleRate())
        except Exception as e:
            self.rec_status.setText(f"❌ Failed to open WAV file: {e}")
            try:
                self.audio_input.stop()
            except Exception:
                pass
            return
        
        # Poll recorded data into WAV
        self.audio_timer = QTimer(self)
        self.audio_timer.timeout.connect(self._poll_audio_data)
        self.audio_timer.start(50)
        self.is_recording = True
        self.rec_status.setText(f"🔴 Recording Part {self.current_part + 1}... (saving to {os.path.basename(self.final_mp3_path)})")
        self.start_rec_btn.setEnabled(False)

    def _poll_audio_data(self):
        if not self.is_recording:
            return
        if not self.audio_io or not self.wave_fp:
            return
        try:
            data = self.audio_io.readAll()
            if data and len(data) > 0:
                self.wave_fp.writeframes(bytes(data))
        except Exception as e:
            # Gracefully stop on polling error
            self.rec_status.setText(f"❌ Recording error: {e}")
            self.stop_recording()

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.cleanup_recording_resources()
        
        # Convert to MP3
        if self.convert_to_mp3():
            self.rec_status.setText(f"✅ Part {self.current_part + 1} recorded and saved as MP3!")
            # Clean up temporary WAV file
            try:
                if os.path.exists(self.temp_wav_path):
                    os.remove(self.temp_wav_path)
            except Exception:
                pass
        else:
            self.rec_status.setText("❌ Failed to convert to MP3. Please ensure ffmpeg is installed.")

    # === Recording Helpers ===
    def get_storage_dir(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        target = os.path.join(desktop, "IELTS_Practice")
        os.makedirs(target, exist_ok=True)
        return target

    def check_disk_space(self, min_free_mb: int = 20) -> bool:
        """Ensure sufficient free space in the storage directory."""
        try:
            total, used, free = shutil.disk_usage(self.storage_dir)
            return (free // (1024 * 1024)) >= min_free_mb
        except Exception:
            return True  # Be permissive if we cannot determine

    def build_output_paths(self):
        ts = datetime.now().strftime('%Y%m%d_%H%M')
        part = self.current_part + 1
        wav = os.path.join(self.storage_dir, f"{ts}_Part{part}.wav")
        mp3 = os.path.join(self.storage_dir, f"{ts}_Part{part}.mp3")
        return wav, mp3

    def get_valid_audio_format(self) -> QAudioFormat:
        fmt = QAudioFormat()
        fmt.setSampleRate(16000)
        fmt.setChannelCount(1)
        fmt.setSampleSize(16)
        fmt.setCodec("audio/pcm")
        fmt.setByteOrder(QAudioFormat.LittleEndian)
        fmt.setSampleType(QAudioFormat.SignedInt)
        info = QAudioDeviceInfo.defaultInputDevice()
        if not info.isFormatSupported(fmt):
            nearest = info.nearestFormat(fmt)
            # Basic validation of nearest format
            if nearest.sampleRate() < 8000 or nearest.sampleSize() < 16:
                raise RuntimeError("Unsupported audio format from default input device.")
            return nearest
        return fmt

    def load_part(self, part_index: int):
        """Load the HTML file for the specified part"""
        if 0 <= part_index < len(self.part_files):
            file_path = self.part_files[part_index]
            if os.path.exists(file_path):
                url = QUrl.fromLocalFile(file_path)
                self.web_view.load(url)
            else:
                self.web_view.setHtml(f"<h1>Part {part_index + 1} file not found</h1><p>Expected: {file_path}</p>")
        else:
            self.web_view.setHtml("<h1>Invalid part</h1>")