import sys
from logger import app_logger
from resource_manager import get_resource_manager
try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel, QMessageBox
    from PyQt5.QtCore import Qt
    from ui.ui_writing_test import WritingTestUI
    try:
        from ui.ui_reading_test import ReadingTestUI
    except ImportError as e:
        app_logger.debug(f"Error importing ReadingTestUI: {e}")
    try:
        from ui.ui_listening_test import ListeningTestUI
    except ImportError as e:
        app_logger.debug(f"Error importing ListeningTestUI: {e}")
    try:
        from ui.ui_speaking_test import SpeakingTestUI
    except ImportError as e:
        app_logger.debug(f"Error importing SpeakingTestUI: {e}")
    from ui.selection_dialog import BookTestSelectionDialog
    try:
        from ui.ui_admin_panel import AdminPanelUI
    except ImportError as e:
        app_logger.debug(f"Error importing AdminPanelUI: {e}")
except ImportError as e:
    app_logger.debug(f"Error importing PyQt5 modules: {e}")
    sys.exit(1)

class IELTSTestSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IELTS Test Simulator")
        self.setMinimumSize(1024, 768)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header with test section tabs
        header = QWidget()
        header.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #d0d0d0;")
        header.setFixedHeight(50)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        # Title label
        title_label = QLabel("IELTS Academic Test Simulator")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # Subtitle label
        subtitle_label = QLabel("Based on Academic IELTS Books")
        subtitle_label.setStyleSheet("font-size: 12px; color: #666; font-style: italic;")
        
        # Navigation buttons
        self.listening_btn = QPushButton("Listening")
        self.reading_btn = QPushButton("Reading")
        self.writing_btn = QPushButton("Writing")
        self.speaking_btn = QPushButton("Speaking")
        
        # Style and configure the buttons
        for btn in [self.listening_btn, self.reading_btn, self.writing_btn, self.speaking_btn]:
            btn.setCheckable(True)
            btn.setMinimumWidth(120)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #c0c0c0;
                    border-radius: 2px;
                    padding: 8px 16px;
                    font-size: 14px;
                }
                QPushButton:checked {
                    background-color: #4CAF50;
                    color: white;
                    border: 1px solid #388E3C;
                }
                QPushButton:hover {
                    background-color: #d8d8d8;
                }
            """)
        
        self.listening_btn.clicked.connect(lambda: self.switch_section(0))
        self.reading_btn.clicked.connect(lambda: self.switch_section(1))
        self.writing_btn.clicked.connect(lambda: self.switch_section(2))
        self.speaking_btn.clicked.connect(lambda: self.switch_section(3))
        
        # Help button
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.show_help)
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #e6e6e6;
                border: 1px solid #c8c8c8;
                padding: 6px 12px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #d8d8d8;
            }
        """)
        
        # Admin panel button
        admin_btn = QPushButton("Admin")
        admin_btn.clicked.connect(self.open_admin_panel)
        admin_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 4px 8px;
                border-radius: 2px;
                font-size: 11px;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        
        # Add widgets to header layout
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.listening_btn)
        header_layout.addWidget(self.reading_btn)
        header_layout.addWidget(self.writing_btn)
        header_layout.addWidget(self.speaking_btn)
        header_layout.addStretch()
        header_layout.addWidget(admin_btn)
        header_layout.addWidget(help_btn)
        
        # Add header to main layout
        main_layout.addWidget(header)
        
        # Initialize resource manager and ask user for book/test once at startup
        self.resource_manager = get_resource_manager()
        selection_dialog = BookTestSelectionDialog(self.resource_manager, self)
        result = selection_dialog.exec_()
        if result != selection_dialog.Accepted or selection_dialog.selected_book is None or selection_dialog.selected_test is None:
            QMessageBox.warning(self, "Selection Required", "Please select a book and test to start the simulator.")
            self.close()
            return
        self.selected_book = selection_dialog.selected_book
        self.selected_test = selection_dialog.selected_test
        app_logger.info(f"Starting app with book='{self.selected_book}', test={self.selected_test}")
        
        # Create stacked widget for different test sections
        self.test_stack = QTabWidget()
        self.test_stack.tabBar().setVisible(False)  # Hide tab bar as we're using our own buttons
        
        # Create test section UIs with fixed book/test context
        try:
            self.listening_ui = ListeningTestUI(self.selected_book, self.selected_test)
            app_logger.debug("Successfully created ListeningTestUI")
        except Exception as e:
            app_logger.debug(f"Error creating ListeningTestUI: {e}")
            self.listening_ui = QWidget()
            
        try:
            self.reading_ui = ReadingTestUI(self.selected_book, self.selected_test)
            app_logger.debug("Successfully created ReadingTestUI")
        except Exception as e:
            app_logger.debug(f"Error creating ReadingTestUI: {e}")
            self.reading_ui = QWidget()
            
        try:
            self.writing_ui = WritingTestUI(self.selected_book, self.selected_test)
            app_logger.debug("Successfully created WritingTestUI")
        except Exception as e:
            app_logger.debug(f"Error creating WritingTestUI: {e}")
            self.writing_ui = QWidget()
            
        try:
            self.speaking_ui = SpeakingTestUI(self.selected_book, self.selected_test)
            app_logger.debug("Successfully created SpeakingTestUI")
        except Exception as e:
            app_logger.debug(f"Error creating SpeakingTestUI: {e}")
            self.speaking_ui = QWidget()
        
        # Add test sections to stacked widget
        self.test_stack.addTab(self.listening_ui, "Listening")
        self.test_stack.addTab(self.reading_ui, "Reading")
        self.test_stack.addTab(self.writing_ui, "Writing")
        self.test_stack.addTab(self.speaking_ui, "Speaking")
        
        # Register for resource change notifications
        self.resource_manager.add_change_callback(self.on_resources_changed)
        
        # Initialize admin panel reference
        self.admin_panel = None
        
        # Add stacked widget to main layout
        main_layout.addWidget(self.test_stack)
        
        # Set initial section
        self.switch_section(0)
        
    def switch_section(self, index):
        """Switch between test sections"""
        # Get current section before switching
        current_index = self.test_stack.currentIndex()
        
        # If leaving listening section (index 0), stop audio
        if current_index == 0 and index != 0:
            try:
                if hasattr(self, 'listening_ui') and hasattr(self.listening_ui, 'stop_audio'):
                    self.listening_ui.stop_audio()
            except Exception as e:
                app_logger.debug(f"Error stopping audio when leaving listening section: {e}")
        
        self.test_stack.setCurrentIndex(index)
        
        # Update button states
        self.listening_btn.setChecked(index == 0)
        self.reading_btn.setChecked(index == 1)
        self.writing_btn.setChecked(index == 2)
        self.speaking_btn.setChecked(index == 3)
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
IELTS Test Simulator Help

This simulator includes all four IELTS test sections:

1. Listening Test (30 minutes + 10 minutes transfer time)
   - 4 sections with increasing difficulty
   - 40 questions total

2. Reading Test (60 minutes)
   - 3 sections with 13-14 questions each
   - 40 questions total
   - Academic content

3. Writing Test (60 minutes)
   - Task 1: 20 minutes (150 words minimum)
   - Task 2: 40 minutes (250 words minimum)
   - Academic content

4. Speaking Test (11-14 minutes)
   - Part 1: Introduction and interview (4-5 minutes)
   - Part 2: Long turn (3-4 minutes)
   - Part 3: Discussion (4-5 minutes)

Use the buttons at the top to switch between test sections.
Each section has its own timer and instructions.

Note: This simulator aims to replicate the experience of the
official IELTS test as closely as possible.
"""
        QMessageBox.information(self, "Help", help_text)
    
    def open_admin_panel(self):
        """Open the admin panel in a new window"""
        try:
            if not hasattr(self, 'admin_panel') or self.admin_panel is None:
                self.admin_panel = AdminPanelUI()
            self.admin_panel.show()
            self.admin_panel.raise_()
            self.admin_panel.activateWindow()
        except Exception as e:
            app_logger.error(f"Error opening admin panel: {e}")
            QMessageBox.warning(self, "Error", f"Could not open admin panel: {str(e)}")
    
    def on_resources_changed(self):
        """Handle resource changes by refreshing UI components."""
        try:
            app_logger.info("Resources changed, refreshing UI components...")
            
            # Refresh each UI component if it has a refresh method
            if hasattr(self.listening_ui, 'refresh_resources'):
                self.listening_ui.refresh_resources()
            
            if hasattr(self.reading_ui, 'refresh_resources'):
                self.reading_ui.refresh_resources()
            
            if hasattr(self.writing_ui, 'refresh_resources'):
                self.writing_ui.refresh_resources()
            
            if hasattr(self.speaking_ui, 'refresh_resources'):
                self.speaking_ui.refresh_resources()
                
            app_logger.info("UI components refreshed successfully")
            
        except Exception as e:
            app_logger.error(f"Error refreshing UI components: {e}")

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Clean, consistent style across platforms
        window = IELTSTestSimulator()
        window.showMaximized()  # Start maximized like test centers
        sys.exit(app.exec_())
    except Exception as e:
        app_logger.debug(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)