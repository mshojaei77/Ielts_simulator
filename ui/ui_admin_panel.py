import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import app_logger

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QTabWidget,
                             QPushButton, QComboBox, QLineEdit, QTextEdit,
                             QSplitter, QGroupBox, QScrollArea, QFrame,
                             QHeaderView, QMessageBox, QFileDialog, QProgressBar,
                             QDateEdit, QCheckBox, QSpinBox, QGridLayout,
                             QApplication, QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, QTimer, QDate, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPixmap


class TestResultsLoader(QThread):
    """Background thread for loading test results from JSON files."""
    
    results_loaded = pyqtSignal(dict)
    progress_updated = pyqtSignal(int, str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, results_dir: str):
        super().__init__()
        self.results_dir = results_dir
        app_logger.info(f"TestResultsLoader initialized with directory: {results_dir}")
        
    def run(self) -> None:
        """Load all JSON test results from the results directory."""
        try:
            app_logger.info("Starting test results loading process")
            
            if not os.path.exists(self.results_dir):
                error_msg = f"Results directory does not exist: {self.results_dir}"
                app_logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return
                
            if not os.path.isdir(self.results_dir):
                error_msg = f"Results path is not a directory: {self.results_dir}"
                app_logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            results = {
                'listening': [],
                'reading': [],
                'writing': [],
                'speaking': []
            }
            
            total_files = 0
            processed_files = 0
            
            # Count total JSON files first
            try:
                for test_type in results.keys():
                    test_dir = os.path.join(self.results_dir, test_type)
                    if os.path.exists(test_dir) and os.path.isdir(test_dir):
                        try:
                            for file in os.listdir(test_dir):
                                if file.endswith('.json'):
                                    total_files += 1
                        except (OSError, PermissionError) as e:
                            app_logger.error(f"Error accessing directory {test_dir}: {e}")
                            continue
                            
                app_logger.info(f"Found {total_files} JSON files to process")
                
            except Exception as e:
                app_logger.error(f"Error counting JSON files: {e}", exc_info=True)
                self.error_occurred.emit(f"Error counting files: {str(e)}")
                return
            
            # Load JSON files
            for test_type in results.keys():
                test_dir = os.path.join(self.results_dir, test_type)
                
                if not os.path.exists(test_dir):
                    app_logger.warning(f"Test directory does not exist: {test_dir}")
                    continue
                    
                if not os.path.isdir(test_dir):
                    app_logger.warning(f"Test path is not a directory: {test_dir}")
                    continue
                
                try:
                    self.progress_updated.emit(
                        int((processed_files / max(total_files, 1)) * 100),
                        f"Loading {test_type} test results..."
                    )
                    
                    files = os.listdir(test_dir)
                    app_logger.debug(f"Processing {len(files)} files in {test_dir}")
                    
                    for file in files:
                        if not file.endswith('.json'):
                            continue
                            
                        file_path = os.path.join(test_dir, file)
                        
                        try:
                            if not os.path.isfile(file_path):
                                app_logger.warning(f"Skipping non-file: {file_path}")
                                continue
                                
                            file_size = os.path.getsize(file_path)
                            if file_size == 0:
                                app_logger.warning(f"Skipping empty file: {file_path}")
                                processed_files += 1
                                continue
                                
                            if file_size > 10 * 1024 * 1024:  # 10MB limit
                                app_logger.warning(f"Skipping large file ({file_size} bytes): {file_path}")
                                processed_files += 1
                                continue
                            
                            with open(file_path, 'r', encoding='utf-8') as f:
                                try:
                                    data = json.load(f)
                                    
                                    if not isinstance(data, dict):
                                        app_logger.warning(f"Invalid JSON structure in {file_path}: expected dict, got {type(data)}")
                                        processed_files += 1
                                        continue
                                    
                                    data['file_path'] = file_path
                                    data['file_name'] = file
                                    results[test_type].append(data)
                                    
                                    app_logger.debug(f"Successfully loaded: {file}")
                                    
                                except json.JSONDecodeError as e:
                                    app_logger.error(f"JSON decode error in {file_path}: {e}")
                                except UnicodeDecodeError as e:
                                    app_logger.error(f"Unicode decode error in {file_path}: {e}")
                                except Exception as e:
                                    app_logger.error(f"Unexpected error reading {file_path}: {e}")
                                    
                            processed_files += 1
                            
                            self.progress_updated.emit(
                                int((processed_files / max(total_files, 1)) * 100),
                                f"Loaded {file}"
                            )
                            
                        except (OSError, PermissionError) as e:
                            app_logger.error(f"File access error for {file_path}: {e}")
                            processed_files += 1
                        except Exception as e:
                            app_logger.error(f"Unexpected error processing {file_path}: {e}", exc_info=True)
                            processed_files += 1
                            
                except (OSError, PermissionError) as e:
                    app_logger.error(f"Directory access error for {test_dir}: {e}")
                    continue
                except Exception as e:
                    app_logger.error(f"Unexpected error processing directory {test_dir}: {e}", exc_info=True)
                    continue
            
            total_loaded = sum(len(results[test_type]) for test_type in results.keys())
            app_logger.info(f"Successfully loaded {total_loaded} test results from {processed_files} files")
            
            self.progress_updated.emit(100, "Loading complete!")
            self.results_loaded.emit(results)
            
        except Exception as e:
            error_msg = f"Critical error in TestResultsLoader: {e}"
            app_logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
            self.results_loaded.emit({})


class StatisticCard(QFrame):
    """Modern card widget for displaying statistics."""
    
    def __init__(self, title: str, value: str = "0", icon: str = "📊"):
        super().__init__()
        
        try:
            app_logger.debug(f"Creating StatisticCard: {title}")
            
            self.setFrameStyle(QFrame.StyledPanel)
            self.setObjectName("stat_card")
            
            layout = QVBoxLayout(self)
            layout.setContentsMargins(20, 15, 20, 15)
            layout.setSpacing(8)
            
            # Icon and title row
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(0, 0, 0, 0)
            
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Segoe UI", 16))
            icon_label.setFixedSize(28, 28)
            
            title_label = QLabel(title)
            title_label.setFont(QFont("Segoe UI", 12, QFont.Medium))
            title_label.setStyleSheet("color: #4a5568; font-weight: 500; letter-spacing: 0.2px;")
            
            header_layout.addWidget(icon_label)
            header_layout.addWidget(title_label)
            header_layout.addStretch()
            
            # Value
            self.value_label = QLabel(value)
            self.value_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
            self.value_label.setStyleSheet("color: #1a202c; font-weight: 700; letter-spacing: -0.5px;")
            self.value_label.setAlignment(Qt.AlignCenter)
            
            layout.addLayout(header_layout)
            layout.addWidget(self.value_label)
            
        except Exception as e:
            app_logger.error(f"Error creating StatisticCard '{title}': {e}", exc_info=True)
            # Create minimal fallback UI
            layout = QVBoxLayout(self)
            self.value_label = QLabel(value)
            layout.addWidget(self.value_label)
        
    def update_value(self, value: str):
        """Update the displayed value."""
        self.value_label.setText(value)


class AdminPanelUI(QWidget):
    """Modern IELTS Test Results Admin Panel with enhanced UI/UX."""
    
    def __init__(self):
        super().__init__()
        self.results_data = {}
        self.filtered_data = {}
        self.results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
        
        self.apply_modern_style()
        self.initUI()
        self.load_test_results()
        
    def initUI(self):
        """Initialize the modern user interface."""
        self.setWindowTitle("IELTS Test Results - Admin Dashboard")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Main layout with improved spacing
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        self.setLayout(main_layout)
        
        # Modern header
        self.create_modern_header(main_layout)
        
        # Content area with splitter
        self.create_content_area(main_layout)
        
        # Modern status bar
        self.create_status_bar(main_layout)
        
    def create_modern_header(self, layout):
        """Create a modern header with consistent styling."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 8, 24, 8)
        header_layout.setSpacing(20)
        
        # Left section - Title and subtitle
        title_section = QVBoxLayout()
        title_section.setContentsMargins(0, 10, 0, 10)
        title_section.setSpacing(4)
        
        title_label = QLabel("📊 IELTS Test Results Dashboard")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setStyleSheet("color: #1a202c; font-weight: 700; letter-spacing: 0.5px;")
        
        subtitle_label = QLabel("Comprehensive test analysis and reporting")
        subtitle_label.setFont(QFont("Segoe UI", 11))
        subtitle_label.setStyleSheet("color: #4a5568; font-weight: 400; letter-spacing: 0.3px;")
        
        title_section.addWidget(title_label)
        title_section.addWidget(subtitle_label)
        
        # Right section - Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setObjectName("action_button")
        self.refresh_btn.clicked.connect(self.load_test_results)
        
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.setObjectName("action_button")
        self.export_btn.clicked.connect(self.export_report)
        
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.setObjectName("action_button")
        self.settings_btn.clicked.connect(self.show_settings)
        
        actions_layout.addWidget(self.refresh_btn)
        actions_layout.addWidget(self.export_btn)
        actions_layout.addWidget(self.settings_btn)
        
        header_layout.addLayout(title_section)
        header_layout.addStretch()
        header_layout.addLayout(actions_layout)
        
        layout.addWidget(header)
        
    def create_content_area(self, layout):
        """Create the main content area with modern layout."""
        try:
            app_logger.debug("Creating content area")
            
            # Main splitter for responsive layout
            main_splitter = QSplitter(Qt.Horizontal)
            main_splitter.setObjectName("main_splitter")
            
            # Left panel - Statistics and filters
            left_panel = self.create_left_panel()
            
            # Right panel - Data tables and details
            right_panel = self.create_right_panel()
            
            main_splitter.addWidget(left_panel)
            main_splitter.addWidget(right_panel)
            main_splitter.setSizes([400, 1200])  # 25% left, 75% right
            
            layout.addWidget(main_splitter)
            
            app_logger.debug("Content area created successfully")
            
        except Exception as e:
            app_logger.error(f"Error creating content area: {e}", exc_info=True)
            raise
        
    def create_left_panel(self) -> QFrame:
        """Create the left panel with statistics and filters."""
        try:
            app_logger.debug("Creating left panel")
            
            panel = QFrame()
            panel.setObjectName("left_panel")
            panel.setMinimumWidth(350)
            panel.setMaximumWidth(450)
            
            layout = QVBoxLayout(panel)
            layout.setContentsMargins(15, 15, 15, 15)
            layout.setSpacing(20)
            
            # Statistics cards
            stats_group = QGroupBox("📈 Test Statistics")
            stats_group.setObjectName("modern_group")
            stats_layout = QGridLayout(stats_group)
            stats_layout.setContentsMargins(15, 20, 15, 15)
            stats_layout.setSpacing(15)
            
            # Create statistic cards
            self.listening_card = StatisticCard("Listening Tests", "0", "🎧")
            self.reading_card = StatisticCard("Reading Tests", "0", "📖")
            self.writing_card = StatisticCard("Writing Tests", "0", "✍️")
            self.speaking_card = StatisticCard("Speaking Tests", "0", "🎤")
            
            stats_layout.addWidget(self.listening_card, 0, 0)
            stats_layout.addWidget(self.reading_card, 0, 1)
            stats_layout.addWidget(self.writing_card, 1, 0)
            stats_layout.addWidget(self.speaking_card, 1, 1)
            
            # Filters section
            filters_group = self.create_filters_section()
            
            layout.addWidget(stats_group)
            layout.addWidget(filters_group)
            layout.addStretch()
            
            app_logger.debug("Left panel created successfully")
            return panel
            
        except Exception as e:
            app_logger.error(f"Error creating left panel: {e}", exc_info=True)
            # Return minimal fallback panel
            fallback_panel = QFrame()
            fallback_layout = QVBoxLayout(fallback_panel)
            fallback_layout.addWidget(QLabel("Error loading panel"))
            return fallback_panel
    
    def create_filters_section(self) -> QGroupBox:
        """Create the filters section."""
        try:
            app_logger.debug("Creating filters section")
            
            filters_group = QGroupBox("🔍 Filters & Search")
            filters_group.setObjectName("modern_group")
            filters_layout = QVBoxLayout(filters_group)
            filters_layout.setContentsMargins(15, 20, 15, 15)
            filters_layout.setSpacing(12)
            
            # Test type filter
            type_layout = QHBoxLayout()
            type_layout.addWidget(QLabel("Test Type:"))
            self.test_type_combo = QComboBox()
            self.test_type_combo.setObjectName("modern_combo")
            self.test_type_combo.addItems(["All Tests", "Listening", "Reading", "Writing", "Speaking"])
            self.test_type_combo.currentTextChanged.connect(self.apply_filters)
            type_layout.addWidget(self.test_type_combo)
            
            # Book filter
            book_layout = QHBoxLayout()
            book_layout.addWidget(QLabel("Book:"))
            self.book_combo = QComboBox()
            self.book_combo.setObjectName("modern_combo")
            self.book_combo.addItem("All Books")
            self.book_combo.currentTextChanged.connect(self.apply_filters)
            book_layout.addWidget(self.book_combo)
            
            # Test number filter
            test_num_layout = QHBoxLayout()
            test_num_layout.addWidget(QLabel("Test #:"))
            self.test_number_spin = QSpinBox()
            self.test_number_spin.setObjectName("modern_spin")
            self.test_number_spin.setMinimum(0)
            self.test_number_spin.setMaximum(50)
            self.test_number_spin.setSpecialValueText("All")
            self.test_number_spin.valueChanged.connect(self.apply_filters)
            test_num_layout.addWidget(self.test_number_spin)
            
            # Search box
            search_layout = QVBoxLayout()
            search_layout.addWidget(QLabel("Search:"))
            self.search_box = QLineEdit()
            self.search_box.setObjectName("modern_search")
            self.search_box.setPlaceholderText("Search in test results...")
            self.search_box.textChanged.connect(self.apply_filters)
            search_layout.addWidget(self.search_box)
            
            # Add all filter controls
            filters_layout.addLayout(type_layout)
            filters_layout.addLayout(book_layout)
            filters_layout.addLayout(test_num_layout)
            filters_layout.addLayout(search_layout)
            
            # Clear filters button
            clear_btn = QPushButton("🗑️ Clear Filters")
            clear_btn.setObjectName("secondary_button")
            clear_btn.clicked.connect(self.clear_filters)
            filters_layout.addWidget(clear_btn)
            
            app_logger.debug("Filters section created successfully")
            return filters_group
            
        except Exception as e:
            app_logger.error(f"Error creating filters section: {e}", exc_info=True)
            # Return minimal fallback
            fallback_group = QGroupBox("Filters (Error)")
            return fallback_group
        
    def create_right_panel(self):
        """Create the right panel with data tables."""
        panel = QFrame()
        panel.setObjectName("right_panel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("modern_progress")
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("modern_tabs")
        
        # Overview tab
        self.create_overview_tab()
        
        # Individual test type tabs
        self.create_test_type_tabs()
        
        layout.addWidget(self.tab_widget)
        
        return panel
        
    def create_overview_tab(self):
        """Create the overview tab with recent tests and summary."""
        overview_widget = QWidget()
        layout = QVBoxLayout(overview_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Recent tests table
        recent_group = QGroupBox("📋 Recent Test Results")
        recent_group.setObjectName("modern_group")
        recent_layout = QVBoxLayout(recent_group)
        recent_layout.setContentsMargins(15, 20, 15, 15)
        
        self.recent_table = QTableWidget()
        self.recent_table.setObjectName("modern_table")
        self.recent_table.setColumnCount(7)
        self.recent_table.setHorizontalHeaderLabels([
            "Type", "Book", "Test #", "Date", "Time", "Grade", "Teacher Comment"
        ])
        
        # Configure table
        header = self.recent_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultSectionSize(100)
        
        # Set specific column widths - optimized for visibility
        self.recent_table.setColumnWidth(0, 150)   # Type
        self.recent_table.setColumnWidth(1, 150)  # Book
        self.recent_table.setColumnWidth(2, 70)   # Test #
        self.recent_table.setColumnWidth(3, 100)  # Date
        self.recent_table.setColumnWidth(4, 80)   # Time
        self.recent_table.setColumnWidth(5, 120)   # Grade
        # Teacher Comment column will stretch to fill remaining space
        
        # Ensure table has minimum width to show all columns
        self.recent_table.setMinimumWidth(750)
        
        # Set row height for better readability
        self.recent_table.verticalHeader().setDefaultSectionSize(35)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_table.setSelectionMode(QTableWidget.SingleSelection)
        self.recent_table.doubleClicked.connect(self.view_test_details)
        
        recent_layout.addWidget(self.recent_table)
        layout.addWidget(recent_group)
        
        self.tab_widget.addTab(overview_widget, "📊 Overview")
        
    def create_test_type_tabs(self):
        """Create tabs for each test type."""
        test_types = [
            ("listening", "🎧 Listening", ["File", "Book", "Test #", "Date", "Sections", "Grade", "Teacher Comment"]),
            ("reading", "📖 Reading", ["File", "Book", "Test #", "Date", "Passages", "Grade", "Teacher Comment"]),
            ("writing", "✍️ Writing", ["File", "Book", "Test #", "Date", "Tasks", "Words", "Grade", "Teacher Comment"]),
            ("speaking", "🎤 Speaking", ["File", "Book", "Test #", "Date", "Parts", "Recordings", "Grade", "Teacher Comment"])
        ]
        
        for test_type, tab_name, columns in test_types:
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(15)
            
            # Test results table
            table_group = QGroupBox(f"{tab_name} Results")
            table_group.setObjectName("modern_group")
            table_layout = QVBoxLayout(table_group)
            table_layout.setContentsMargins(15, 20, 15, 15)
            
            table = QTableWidget()
            table.setObjectName(f"{test_type}_table")
            table.setColumnCount(len(columns))
            table.setHorizontalHeaderLabels(columns)
            
            # Configure table
            header = table.horizontalHeader()
            header.setStretchLastSection(True)
            header.setDefaultSectionSize(100)
            
            # Set optimized column widths based on test type
            if test_type == "listening":
                table.setColumnWidth(0, 110)  # File
                table.setColumnWidth(1, 90)   # Book
                table.setColumnWidth(2, 60)   # Test #
                table.setColumnWidth(3, 90)   # Date
                table.setColumnWidth(4, 70)   # Sections
                table.setColumnWidth(5, 70)   # Grade
                table.setColumnWidth(6, 200)  # Teacher Comment
                table.setMinimumWidth(690)
            elif test_type == "reading":
                table.setColumnWidth(0, 110)  # File
                table.setColumnWidth(1, 90)   # Book
                table.setColumnWidth(2, 60)   # Test #
                table.setColumnWidth(3, 90)   # Date
                table.setColumnWidth(4, 70)   # Passages
                table.setColumnWidth(5, 70)   # Grade
                table.setColumnWidth(6, 200)  # Teacher Comment
                table.setMinimumWidth(690)
            elif test_type == "writing":
                table.setColumnWidth(0, 110)  # File
                table.setColumnWidth(1, 90)   # Book
                table.setColumnWidth(2, 60)   # Test #
                table.setColumnWidth(3, 90)   # Date
                table.setColumnWidth(4, 60)   # Tasks
                table.setColumnWidth(5, 60)   # Words
                table.setColumnWidth(6, 70)   # Grade
                table.setColumnWidth(7, 200)  # Teacher Comment
                table.setMinimumWidth(740)
            elif test_type == "speaking":
                table.setColumnWidth(0, 110)  # File
                table.setColumnWidth(1, 90)   # Book
                table.setColumnWidth(2, 60)   # Test #
                table.setColumnWidth(3, 90)   # Date
                table.setColumnWidth(4, 60)   # Parts
                table.setColumnWidth(5, 70)   # Recordings
                table.setColumnWidth(6, 70)   # Grade
                table.setColumnWidth(7, 200)  # Teacher Comment
                table.setMinimumWidth(750)
            
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setSelectionMode(QTableWidget.SingleSelection)
            table.doubleClicked.connect(lambda: self.view_test_details(test_type))
            
            table_layout.addWidget(table)
            
            # Details section
            details_group = QGroupBox("📄 Test Details")
            details_group.setObjectName("modern_group")
            details_layout = QVBoxLayout(details_group)
            details_layout.setContentsMargins(15, 20, 15, 15)
            
            details_text = QTextEdit()
            details_text.setObjectName(f"{test_type}_details")
            details_text.setMaximumHeight(200)
            details_text.setReadOnly(True)
            details_layout.addWidget(details_text)
            
            layout.addWidget(table_group)
            layout.addWidget(details_group)
            
            self.tab_widget.addTab(widget, tab_name)
            
    def create_status_bar(self, layout):
        """Create a modern status bar."""
        status_bar = QFrame()
        status_bar.setObjectName("status_bar")
        status_bar.setFixedHeight(35)
        
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(20, 0, 20, 0)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        
        # Connection status indicator
        self.connection_status = QLabel("● Connected")
        self.connection_status.setStyleSheet("color: #27ae60; font-size: 11px; font-weight: bold;")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.connection_status)
        
        layout.addWidget(status_bar)
        
    def apply_modern_style(self):
        """Apply modern styling consistent with other UI files."""
        self.setStyleSheet("""
            /* Main widget styling */
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #212529;
                line-height: 1.4;
            }
            
            /* Main window layout */
            QMainWindow {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            
            /* Header styling */
            QFrame#header {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border-bottom: 2px solid #e9ecef;
            }
            
            /* Left panel styling */
            QFrame#left_panel {
                background-color: #f8f9fa;
                border-right: 2px solid #e9ecef;
                border-radius: 0px 8px 8px 0px;
                padding: 10px;
            }
            
            /* Right panel styling */
            QFrame#right_panel {
                background-color: #ffffff;
                border-radius: 8px;
                margin: 5px;
            }
            
            /* Status bar styling */
            QFrame#status_bar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-top: 2px solid #dee2e6;
                color: #495057;
            }
            
            /* Modern group boxes */
            QGroupBox#modern_group {
                font-weight: 600;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 12px;
                background-color: #ffffff;
            }
            
            QGroupBox#modern_group::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #ffffff;
            }
            
            /* Statistic cards */
            QFrame#stat_card {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 8px;
            }
            
            QFrame#stat_card:hover {
                border-color: #3498db;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f8f9fa, stop:1 #e3f2fd);
            }
            
            /* Action buttons */
            QPushButton#action_button {
                background-color: #3498db;
                border: 1px solid #2980b9;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
                color: #ffffff;
                min-height: 24px;
                min-width: 80px;
            }
            
            QPushButton#action_button:hover {
                background-color: #2980b9;
                border-color: #1f5f8b;
            }
            
            QPushButton#action_button:pressed {
                background-color: #1f5f8b;
            }
            
            /* Secondary buttons */
            QPushButton#secondary_button {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
                color: #495057;
                min-height: 24px;
            }
            
            QPushButton#secondary_button:hover {
                background-color: #f8f9fa;
                color: #212529;
                border-color: #adb5bd;
            }
            
            /* Modern combo boxes */
            QComboBox#modern_combo {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 6px 8px;
                min-height: 20px;
                font-size: 12px;
            }
            
            QComboBox#modern_combo:hover {
                border-color: #3498db;
            }
            
            QComboBox#modern_combo:focus {
                border-color: #3498db;
                outline: none;
            }
            
            QComboBox#modern_combo::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox#modern_combo::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #666666;
                margin-right: 5px;
            }
            
            /* Modern spin box */
            QSpinBox#modern_spin {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px 12px;
                min-height: 24px;
                font-size: 13px;
                color: #495057;
            }
            
            QSpinBox#modern_spin:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
            
            QSpinBox#modern_spin:focus {
                border-color: #2980b9;
                outline: none;
            }
            
            /* Modern search box */
            QLineEdit#modern_search {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 12px;
            }
            
            QLineEdit#modern_search:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
            
            QLineEdit#modern_search:focus {
                border-color: #2980b9;
                outline: none;
            }
            
            /* Modern progress bar */
            QProgressBar#modern_progress {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: #f8f9fa;
                text-align: center;
                font-size: 11px;
                height: 20px;
            }
            
            QProgressBar#modern_progress::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
            
            /* Modern tabs */
            QTabWidget#modern_tabs::pane {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: #ffffff;
                margin-top: -1px;
            }
            
            QTabWidget#modern_tabs::tab-bar {
                alignment: left;
            }
            
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 2px solid #dee2e6;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 3px;
                font-size: 13px;
                font-weight: 500;
                color: #495057;
            }
            
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border-bottom: 3px solid #3498db;
                color: #2980b9;
                font-weight: 600;
            }
            
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #e9ecef, stop:1 #dee2e6);
                color: #212529;
                border-color: #adb5bd;
            }
            
            /* Modern tables */
            QTableWidget#modern_table, QTableWidget[objectName$="_table"] {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                gridline-color: #f1f3f4;
                selection-background-color: #3498db;
                selection-color: #ffffff;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
                outline: none;
            }
            
            QTableWidget#modern_table::item, QTableWidget[objectName$="_table"]::item {
                padding: 12px 10px;
                border-bottom: 1px solid #f1f3f4;
                border-right: 1px solid #f8f9fa;
                font-size: 13px;
                color: #2c3e50;
                font-weight: 400;
            }
            
            QTableWidget#modern_table::item:selected, QTableWidget[objectName$="_table"]::item:selected {
                background-color: #3498db;
                color: #ffffff;
                border-color: #2980b9;
                font-weight: 500;
            }
            
            QTableWidget#modern_table::item:alternate, QTableWidget[objectName$="_table"]::item:alternate {
                background-color: #f8f9fa;
            }
            
            QTableWidget#modern_table::item:hover, QTableWidget[objectName$="_table"]::item:hover {
                background-color: #e8f4fd;
                border-color: #bee5eb;
                color: #1a202c;
            }
            
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f1f3f4, stop:1 #e9ecef);
                border: none;
                border-right: 1px solid #dee2e6;
                border-bottom: 2px solid #3498db;
                padding: 14px 10px;
                font-weight: 600;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #343a40;
                text-align: left;
                min-height: 25px;
            }
            
            QHeaderView::section:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e9ecef, stop:1 #dee2e6);
                color: #212529;
            }
            
            QHeaderView::section:first {
                border-left: none;
                border-top-left-radius: 6px;
            }
            
            QHeaderView::section:last {
                border-right: none;
                border-top-right-radius: 6px;
            }
            
            /* Splitter styling */
            QSplitter#main_splitter::handle {
                background-color: #e0e0e0;
                width: 1px;
            }
            
            QSplitter#main_splitter::handle:hover {
                background-color: #3498db;
            }
            
            /* Text edit styling */
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                line-height: 1.4;
            }
            
            QTextEdit:focus {
                border-color: #3498db;
                outline: none;
            }
        """)
        
    def load_test_results(self):
        """Load test results from JSON files."""
        self.progress_bar.setVisible(True)
        self.status_label.setText("Loading test results...")
        self.refresh_btn.setEnabled(False)
        
        # Start background loading
        self.loader_thread = TestResultsLoader(self.results_dir)
        self.loader_thread.results_loaded.connect(self.on_results_loaded)
        self.loader_thread.progress_updated.connect(self.on_progress_updated)
        self.loader_thread.error_occurred.connect(self.on_loading_error)
        self.loader_thread.start()
        
        app_logger.info("Test results loading initiated")
        
    @pyqtSlot(dict)
    def on_results_loaded(self, results):
        """Handle loaded test results."""
        self.results_data = results
        self.filtered_data = results.copy()
        
        # Update UI
        self.update_statistics()
        self.update_filter_options()
        self.populate_tables()
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        
        total_tests = sum(len(tests) for tests in results.values())
        self.status_label.setText(f"Loaded {total_tests} test results successfully")
        
    @pyqtSlot(int, str)
    def on_progress_updated(self, progress, message):
        """Update progress bar and status."""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        
    def update_statistics(self) -> None:
        """Update the statistics cards."""
        try:
            app_logger.debug("Updating statistics cards")
            
            if not hasattr(self, 'results_data') or not self.results_data:
                app_logger.warning("No results data available for statistics update")
                return
            
            listening_count = len(self.results_data.get('listening', []))
            reading_count = len(self.results_data.get('reading', []))
            writing_count = len(self.results_data.get('writing', []))
            speaking_count = len(self.results_data.get('speaking', []))
            
            if hasattr(self, 'listening_card'):
                self.listening_card.update_value(str(listening_count))
            if hasattr(self, 'reading_card'):
                self.reading_card.update_value(str(reading_count))
            if hasattr(self, 'writing_card'):
                self.writing_card.update_value(str(writing_count))
            if hasattr(self, 'speaking_card'):
                self.speaking_card.update_value(str(speaking_count))
            
            app_logger.debug(f"Statistics updated - L:{listening_count}, R:{reading_count}, W:{writing_count}, S:{speaking_count}")
            
        except Exception as e:
            app_logger.error(f"Error updating statistics: {e}", exc_info=True)
            
    def update_filter_options(self) -> None:
        """Update filter combo boxes with available options."""
        try:
            app_logger.debug("Updating filter options")
            
            if not hasattr(self, 'results_data') or not self.results_data:
                app_logger.warning("No results data available for filter options update")
                return
            
            # Update book filter
            books = set()
            for test_type_data in self.results_data.values():
                for test in test_type_data:
                    if 'book' in test and test['book']:
                        books.add(test['book'])
            
            if hasattr(self, 'book_combo'):
                current_book = self.book_combo.currentText()
                self.book_combo.clear()
                self.book_combo.addItem("All Books")
                self.book_combo.addItems(sorted(books))
                
                # Restore selection if still valid
                index = self.book_combo.findText(current_book)
                if index >= 0:
                    self.book_combo.setCurrentIndex(index)
            
            app_logger.debug(f"Filter options updated with {len(books)} unique books")
            
        except Exception as e:
            app_logger.error(f"Error updating filter options: {e}", exc_info=True)
        
    def apply_filters(self) -> None:
        """Apply current filters to the data."""
        try:
            app_logger.debug("Applying filters to data")
            
            if not hasattr(self, 'results_data') or not self.results_data:
                app_logger.warning("No results data available for filtering")
                return
            
            # Get filter values safely
            test_type_filter = self.test_type_combo.currentText().lower() if hasattr(self, 'test_type_combo') else "all tests"
            if test_type_filter == "all tests":
                test_type_filter = "all"
                
            book_filter = self.book_combo.currentText() if hasattr(self, 'book_combo') else "All Books"
            test_number_filter = self.test_number_spin.value() if hasattr(self, 'test_number_spin') else 0
            search_text = self.search_box.text().lower() if hasattr(self, 'search_box') else ""
            
            app_logger.debug(f"Filter criteria - Type: {test_type_filter}, Book: {book_filter}, Test#: {test_number_filter}, Search: '{search_text}'")
            
            self.filtered_data = {}
            
            for test_type, tests in self.results_data.items():
                if test_type_filter != "all" and test_type != test_type_filter:
                    self.filtered_data[test_type] = []
                    continue
                    
                filtered_tests = []
                for test in tests:
                    try:
                        # Apply filters
                        if book_filter != "All Books" and test.get('book', '') != book_filter:
                            continue
                            
                        if test_number_filter > 0 and test.get('test_number', 0) != test_number_filter:
                            continue
                            
                        if search_text:
                            try:
                                test_json = json.dumps(test).lower()
                                if search_text not in test_json:
                                    continue
                            except Exception as json_error:
                                app_logger.warning(f"Error serializing test for search: {json_error}")
                                # Fallback to basic string search
                                searchable_text = ' '.join([
                                    str(test.get('book', '')),
                                    str(test.get('test_number', '')),
                                    str(test.get('grade', '')),
                                    str(test.get('teacher_comment', ''))
                                ]).lower()
                                if search_text not in searchable_text:
                                    continue
                            
                        filtered_tests.append(test)
                        
                    except Exception as test_error:
                        app_logger.warning(f"Error filtering individual test: {test_error}")
                        continue
                    
                self.filtered_data[test_type] = filtered_tests
                
            self.populate_tables()
            
            total_filtered = sum(len(tests) for tests in self.filtered_data.values())
            app_logger.debug(f"Filters applied successfully, {total_filtered} tests match criteria")
            
        except Exception as e:
            app_logger.error(f"Error applying filters: {e}", exc_info=True)
            # Reset to show all data on error
            if hasattr(self, 'results_data'):
                self.filtered_data = self.results_data.copy()
                self.populate_tables()
        
    def clear_filters(self) -> None:
        """Clear all filters and reset to show all data."""
        try:
            app_logger.debug("Clearing all filters")
            
            if hasattr(self, 'test_type_combo'):
                self.test_type_combo.setCurrentText("All Tests")
            if hasattr(self, 'book_combo'):
                self.book_combo.setCurrentText("All Books")
            if hasattr(self, 'test_number_spin'):
                self.test_number_spin.setValue(0)
            if hasattr(self, 'search_box'):
                self.search_box.clear()
            
            # Reset filtered data
            if hasattr(self, 'results_data'):
                self.filtered_data = self.results_data.copy()
                self.populate_tables()
            
            app_logger.debug("All filters cleared successfully")
            
        except Exception as e:
            app_logger.error(f"Error clearing filters: {e}", exc_info=True)
        
    def populate_tables(self) -> None:
        """Populate all tables with filtered data."""
        try:
            app_logger.debug("Populating all tables with filtered data")
            
            self.populate_recent_table()
            
            for test_type in ['listening', 'reading', 'writing', 'speaking']:
                try:
                    self.populate_test_type_table(test_type)
                except Exception as table_error:
                    app_logger.error(f"Error populating {test_type} table: {table_error}", exc_info=True)
            
            app_logger.debug("All tables populated successfully")
            
        except Exception as e:
            app_logger.error(f"Error populating tables: {e}", exc_info=True)
            
    def populate_recent_table(self) -> None:
        """Populate the recent tests table."""
        try:
            app_logger.debug("Populating recent tests table")
            
            if not hasattr(self, 'recent_table'):
                app_logger.warning("Recent table not available")
                return
            
            if not hasattr(self, 'filtered_data') or not self.filtered_data:
                app_logger.debug("No filtered data available for recent table")
                self.recent_table.setRowCount(0)
                return
            
            # Collect all tests and sort by timestamp
            all_tests = []
            for test_type, tests in self.filtered_data.items():
                for test in tests:
                    try:
                        test_copy = test.copy()
                        test_copy['type'] = test_type
                        all_tests.append(test_copy)
                    except Exception as test_error:
                        app_logger.warning(f"Error processing test for recent table: {test_error}")
                        continue
                    
            # Sort by timestamp (newest first)
            try:
                all_tests.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            except Exception as sort_error:
                app_logger.warning(f"Error sorting tests by timestamp: {sort_error}")
            
            # Take only the most recent 50
            recent_tests = all_tests[:50]
            
            self.recent_table.setRowCount(len(recent_tests))
            
            for row, test in enumerate(recent_tests):
                try:
                    # Type
                    type_item = QTableWidgetItem(test.get('type', '').capitalize())
                    type_item.setFont(QFont("Arial", 11, QFont.Bold))
                    self.recent_table.setItem(row, 0, type_item)
                    
                    # Book
                    self.recent_table.setItem(row, 1, QTableWidgetItem(test.get('book', '')))
                    
                    # Test number
                    self.recent_table.setItem(row, 2, QTableWidgetItem(str(test.get('test_number', ''))))
                    
                    # Date (formatted)
                    timestamp = test.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                            date_str = dt.strftime('%Y-%m-%d')
                            time_str = dt.strftime('%H:%M')
                        except Exception as date_error:
                            app_logger.debug(f"Error parsing timestamp {timestamp}: {date_error}")
                            date_str = timestamp[:8] if len(timestamp) >= 8 else timestamp
                            time_str = timestamp[9:] if len(timestamp) > 9 else ''
                    else:
                        date_str = 'N/A'
                        time_str = 'N/A'
                        
                    self.recent_table.setItem(row, 3, QTableWidgetItem(date_str))
                    self.recent_table.setItem(row, 4, QTableWidgetItem(time_str))
                    
                    # Grade
                    grade = test.get('grade', '')
                    if grade:
                        grade_item = QTableWidgetItem(str(grade))
                        grade_item.setForeground(QColor("#2c3e50"))
                    else:
                        grade_item = QTableWidgetItem("Not graded")
                        grade_item.setForeground(QColor("#95a5a6"))
                    self.recent_table.setItem(row, 5, grade_item)
                    
                    # Teacher Comment
                    comment = test.get('teacher_comment', '')
                    if comment:
                        # Truncate long comments for table display
                        display_comment = comment[:50] + "..." if len(comment) > 50 else comment
                        comment_item = QTableWidgetItem(display_comment)
                        comment_item.setForeground(QColor("#2c3e50"))
                        comment_item.setToolTip(comment)  # Full comment on hover
                    else:
                        comment_item = QTableWidgetItem("No comment")
                        comment_item.setForeground(QColor("#95a5a6"))
                    self.recent_table.setItem(row, 6, comment_item)
                    
                except Exception as row_error:
                    app_logger.warning(f"Error populating recent table row {row}: {row_error}")
                    # Fill with error indicators
                    for col in range(7):
                        try:
                            self.recent_table.setItem(row, col, QTableWidgetItem("Error"))
                        except Exception:
                            pass
            
            app_logger.debug(f"Recent table populated with {len(recent_tests)} tests")
            
        except Exception as e:
            app_logger.error(f"Error populating recent table: {e}", exc_info=True)
            
    def populate_test_type_table(self, test_type: str) -> None:
        """Populate a specific test type table."""
        try:
            app_logger.debug(f"Populating {test_type} table")
            
            table = self.findChild(QTableWidget, f"{test_type}_table")
            if not table:
                app_logger.error(f"Table for {test_type} not found")
                return
                
            if not hasattr(self, 'filtered_data') or not self.filtered_data:
                app_logger.debug(f"No filtered data available for {test_type} table")
                table.setRowCount(0)
                return
                
            tests = self.filtered_data.get(test_type, [])
            table.setRowCount(len(tests))
            
            for row, test in enumerate(tests):
                try:
                    col = 0
                    
                    # File name
                    table.setItem(row, col, QTableWidgetItem(test.get('file_name', '')))
                    col += 1
                    
                    # Book
                    table.setItem(row, col, QTableWidgetItem(test.get('book', '')))
                    col += 1
                    
                    # Test number
                    table.setItem(row, col, QTableWidgetItem(str(test.get('test_number', ''))))
                    col += 1
                    
                    # Date (formatted)
                    timestamp = test.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                            date_str = dt.strftime('%Y-%m-%d %H:%M')
                        except Exception as date_error:
                            app_logger.debug(f"Error parsing timestamp {timestamp}: {date_error}")
                            date_str = timestamp
                    else:
                        date_str = 'N/A'
                    table.setItem(row, col, QTableWidgetItem(date_str))
                    col += 1
                
                    # Test-specific columns
                    try:
                        if test_type == "listening":
                            # Sections
                            sections = len(test.get('answers', {}))
                            table.setItem(row, col, QTableWidgetItem(str(sections)))
                            col += 1
                            
                        elif test_type == "reading":
                            # Passages
                            passages = len(test.get('answers', {}))
                            table.setItem(row, col, QTableWidgetItem(str(passages)))
                            col += 1
                            
                        elif test_type == "writing":
                            # Tasks
                            tasks = len(test.get('answers', {}))
                            table.setItem(row, col, QTableWidgetItem(str(tasks)))
                            col += 1
                            
                            # Word count
                            total_words = 0
                            for task_data in test.get('answers', {}).values():
                                if isinstance(task_data, dict):
                                    total_words += task_data.get('word_count', 0)
                            table.setItem(row, col, QTableWidgetItem(str(total_words)))
                            col += 1
                            
                        else:  # speaking
                            # Parts
                            parts = len(test.get('answers', {}))
                            table.setItem(row, col, QTableWidgetItem(str(parts)))
                            col += 1
                            
                            # Recordings
                            recordings = len(test.get('recordings', {}))
                            table.setItem(row, col, QTableWidgetItem(str(recordings)))
                            col += 1
                    except Exception as specific_error:
                        app_logger.warning(f"Error processing {test_type}-specific data for row {row}: {specific_error}")
                        # Fill remaining columns with error indicators
                        remaining_cols = 2 if test_type == "writing" else 1
                        for _ in range(remaining_cols):
                            table.setItem(row, col, QTableWidgetItem("Error"))
                            col += 1
                    
                    # Grade
                    grade = test.get('grade', '')
                    if grade:
                        grade_item = QTableWidgetItem(str(grade))
                        grade_item.setForeground(QColor("#2c3e50"))
                    else:
                        grade_item = QTableWidgetItem("Not graded")
                        grade_item.setForeground(QColor("#95a5a6"))
                    table.setItem(row, col, grade_item)
                    col += 1
                    
                    # Teacher Comment
                    comment = test.get('teacher_comment', '')
                    if comment:
                        # Truncate long comments for table display
                        display_comment = comment[:50] + "..." if len(comment) > 50 else comment
                        comment_item = QTableWidgetItem(display_comment)
                        comment_item.setForeground(QColor("#2c3e50"))
                        comment_item.setToolTip(comment)  # Full comment on hover
                    else:
                        comment_item = QTableWidgetItem("No comment")
                        comment_item.setForeground(QColor("#95a5a6"))
                    table.setItem(row, col, comment_item)
                    
                except Exception as row_error:
                    app_logger.warning(f"Error populating {test_type} table row {row}: {row_error}")
                    # Fill with error indicators
                    for col_idx in range(table.columnCount()):
                        try:
                            table.setItem(row, col_idx, QTableWidgetItem("Error"))
                        except Exception:
                            pass
        
            app_logger.debug(f"{test_type.capitalize()} table populated with {len(tests)} tests")
            
        except Exception as e:
            app_logger.error(f"Error populating {test_type} table: {e}", exc_info=True)
            
    def view_test_details(self, test_type=None) -> None:
        """View detailed information about a selected test."""
        try:
            app_logger.debug("Viewing test details")
            
            if test_type is None:
                # Called from overview table
                try:
                    current_row = self.recent_table.currentRow()
                    if current_row < 0:
                        app_logger.debug("No row selected in recent table")
                        return
                        
                    type_item = self.recent_table.item(current_row, 0)
                    if not type_item:
                        app_logger.warning("Could not get test type from recent table")
                        return
                        
                    test_type = type_item.text().lower()
                except Exception as recent_error:
                    app_logger.error(f"Error getting test type from recent table: {recent_error}")
                    return
                
            # Find the corresponding table
            try:
                table = self.findChild(QTableWidget, f"{test_type}_table")
                details_text = self.findChild(QTextEdit, f"{test_type}_details")
                
                if not table or not details_text:
                    app_logger.warning(f"Table or details widget not found for {test_type}")
                    return
            except Exception as widget_error:
                app_logger.error(f"Error finding widgets for {test_type}: {widget_error}")
                return
                
            try:
                current_row = table.currentRow()
                if current_row < 0:
                    app_logger.debug(f"No row selected in {test_type} table")
                    return
            except Exception as row_error:
                app_logger.error(f"Error getting current row from {test_type} table: {row_error}")
                return
                
            # Get test data
            try:
                if not hasattr(self, 'filtered_data') or not self.filtered_data:
                    app_logger.warning("No filtered data available for test details")
                    return
                    
                tests = self.filtered_data.get(test_type, [])
                if current_row >= len(tests):
                    app_logger.warning(f"Row {current_row} out of range for {test_type} tests (max: {len(tests)})")
                    return
                    
                test_data = tests[current_row]
            except Exception as data_error:
                app_logger.error(f"Error getting test data: {data_error}")
                return
            
            # Format detailed information
            try:
                details = self.format_test_details(test_data, test_type)
                details_text.setHtml(details)
                app_logger.debug(f"Test details displayed for {test_type} test")
            except Exception as format_error:
                app_logger.error(f"Error formatting test details: {format_error}", exc_info=True)
                details_text.setHtml("<p>Error loading test details</p>")
            
            # Switch to the appropriate tab
            try:
                if hasattr(self, 'tab_widget'):
                    for i in range(self.tab_widget.count()):
                        if test_type in self.tab_widget.tabText(i).lower():
                            self.tab_widget.setCurrentIndex(i)
                            break
            except Exception as tab_error:
                app_logger.warning(f"Error switching to {test_type} tab: {tab_error}")
                
        except Exception as e:
            app_logger.error(f"Error viewing test details: {e}", exc_info=True)
                
    def format_test_details(self, test_data: dict, test_type: str) -> str:
        """Format test data into HTML for display."""
        try:
            app_logger.debug(f"Formatting test details for {test_type}")
            
            if not isinstance(test_data, dict):
                app_logger.warning(f"Invalid test data type: {type(test_data)}")
                return "<p>Invalid test data</p>"
            
            # Safely get values with error handling
            try:
                file_name = test_data.get('file_name', 'N/A')
                book = test_data.get('book', 'N/A')
                test_number = test_data.get('test_number', 'N/A')
                timestamp = test_data.get('timestamp', 'N/A')
                time_spent = test_data.get('time_spent_seconds', 0)
                
                metadata = test_data.get('metadata', {})
                completion_status = metadata.get('completion_status', 'Unknown') if isinstance(metadata, dict) else 'Unknown'
                
                grade = test_data.get('grade', 'Not graded yet')
                teacher_comment = test_data.get('teacher_comment', 'No comment yet')
                
                # Format test content
                test_content = self.format_test_content(test_data, test_type)
                
            except Exception as data_error:
                app_logger.warning(f"Error extracting test data fields: {data_error}")
                return "<p>Error processing test data</p>"
            
            html = f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h3 style="color: #2c3e50; margin-bottom: 15px;">
                    {test_type.capitalize()} Test Details
                </h3>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="font-weight: bold; padding: 5px; border-bottom: 1px solid #eee;">File:</td>
                        <td style="padding: 5px; border-bottom: 1px solid #eee;">{file_name}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; padding: 5px; border-bottom: 1px solid #eee;">Book:</td>
                        <td style="padding: 5px; border-bottom: 1px solid #eee;">{book}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; padding: 5px; border-bottom: 1px solid #eee;">Test Number:</td>
                        <td style="padding: 5px; border-bottom: 1px solid #eee;">{test_number}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; padding: 5px; border-bottom: 1px solid #eee;">Timestamp:</td>
                        <td style="padding: 5px; border-bottom: 1px solid #eee;">{timestamp}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; padding: 5px; border-bottom: 1px solid #eee;">Duration:</td>
                        <td style="padding: 5px; border-bottom: 1px solid #eee;">{time_spent} seconds</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; padding: 5px; border-bottom: 1px solid #eee;">Status:</td>
                        <td style="padding: 5px; border-bottom: 1px solid #eee;">{completion_status}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; padding: 5px; border-bottom: 1px solid #eee;">Grade:</td>
                        <td style="padding: 5px; border-bottom: 1px solid #eee; color: #7f8c8d; font-style: italic;">{grade}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; padding: 5px; border-bottom: 1px solid #eee;">Teacher Comment:</td>
                        <td style="padding: 5px; border-bottom: 1px solid #eee; color: #7f8c8d; font-style: italic;">{teacher_comment}</td>
                    </tr>
                </table>
                
                <h4 style="color: #34495e; margin-top: 20px; margin-bottom: 10px;">Test Content:</h4>
                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; border-left: 4px solid #3498db;">
                    {test_content}
                </div>
            </div>
            """
            return html
            
        except Exception as e:
            app_logger.error(f"Error formatting test details: {e}", exc_info=True)
            return "<p>Error formatting test details</p>"
        
    def format_test_content(self, test_data: dict, test_type: str) -> str:
        """Format test-specific content."""
        try:
            app_logger.debug(f"Formatting test content for {test_type}")
            
            if not isinstance(test_data, dict):
                app_logger.warning(f"Invalid test data type for content formatting: {type(test_data)}")
                return "Invalid test data"
            
            if not test_type:
                app_logger.warning("Empty test type provided for content formatting")
                return "Unknown test type"
            
            try:
                answers = test_data.get('answers', {})
                if not isinstance(answers, dict):
                    app_logger.warning(f"Invalid answers data type: {type(answers)}")
                    answers = {}
                
                if test_type == 'writing':
                    content = ""
                    try:
                        for task, task_data in answers.items():
                            if isinstance(task_data, dict):
                                word_count = task_data.get('word_count', 0)
                                char_count = task_data.get('character_count', 0)
                                
                                # Validate numeric values
                                if not isinstance(word_count, (int, float)):
                                    app_logger.warning(f"Invalid word count type for {task}: {type(word_count)}")
                                    word_count = 0
                                if not isinstance(char_count, (int, float)):
                                    app_logger.warning(f"Invalid character count type for {task}: {type(char_count)}")
                                    char_count = 0
                                
                                content += f"<strong>{task.capitalize()}:</strong> {word_count} words, {char_count} characters<br>"
                    except Exception as writing_error:
                        app_logger.warning(f"Error processing writing content: {writing_error}")
                        return "Error processing writing data"
                    
                    return content or "No writing data available"
                    
                elif test_type == 'speaking':
                    try:
                        recordings = test_data.get('recordings', {})
                        if not isinstance(recordings, dict):
                            app_logger.warning(f"Invalid recordings data type: {type(recordings)}")
                            recordings = {}
                        
                        content = f"<strong>Parts completed:</strong> {len(answers)}<br>"
                        content += f"<strong>Recordings:</strong> {len(recordings)}<br>"
                        return content
                    except Exception as speaking_error:
                        app_logger.warning(f"Error processing speaking content: {speaking_error}")
                        return "Error processing speaking data"
                    
                elif test_type in ['listening', 'reading']:
                    try:
                        content = f"<strong>Sections/Passages:</strong> {len(answers)}<br>"
                        total_questions = 0
                        
                        for section_data in answers.values():
                            if isinstance(section_data, dict):
                                section_answers = section_data.get('answers', {})
                                if isinstance(section_answers, dict):
                                    total_questions += len(section_answers)
                                else:
                                    app_logger.warning(f"Invalid section answers type: {type(section_answers)}")
                        
                        content += f"<strong>Total Questions:</strong> {total_questions}<br>"
                        return content
                    except Exception as lr_error:
                        app_logger.warning(f"Error processing {test_type} content: {lr_error}")
                        return f"Error processing {test_type} data"
                
                else:
                    app_logger.debug(f"Unknown test type for content formatting: {test_type}")
                    return "No content data available"
                    
            except Exception as content_error:
                app_logger.warning(f"Error processing test content data: {content_error}")
                return "Error processing test content"
            
        except Exception as e:
            app_logger.error(f"Error formatting test content: {e}", exc_info=True)
            return "Error formatting content"
        
    def export_report(self):
        """Export test results to a file."""
        try:
            app_logger.debug("Starting export report process")
            
            # Check if filtered_data exists and has content
            if not hasattr(self, 'filtered_data'):
                app_logger.warning("No filtered_data attribute found")
                QMessageBox.warning(self, "Export Error", "No data available to export")
                return
            
            if not self.filtered_data:
                app_logger.warning("Filtered data is empty")
                QMessageBox.warning(self, "Export Error", "No data available to export")
                return
            
            try:
                # Generate default filename with error handling
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    default_filename = f"ielts_test_results_{timestamp}.json"
                except Exception as time_error:
                    app_logger.warning(f"Error generating timestamp: {time_error}")
                    default_filename = "ielts_test_results.json"
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 
                    "Export Test Results", 
                    default_filename,
                    "JSON Files (*.json);;CSV Files (*.csv);;All Files (*)"
                )
                
            except Exception as dialog_error:
                app_logger.error(f"Error opening file dialog: {dialog_error}")
                QMessageBox.critical(self, "Export Error", "Failed to open file selection dialog")
                return
            
            if file_path:
                app_logger.info(f"Exporting data to: {file_path}")
                
                try:
                    if file_path.endswith('.json'):
                        # JSON export with comprehensive error handling
                        try:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                json.dump(self.filtered_data, f, indent=2, ensure_ascii=False)
                            
                            app_logger.info(f"Successfully exported {len(self.filtered_data)} records to JSON")
                            
                        except PermissionError:
                            app_logger.error(f"Permission denied writing to: {file_path}")
                            QMessageBox.critical(self, "Export Error", 
                                               f"Permission denied. Cannot write to:\n{file_path}")
                            return
                        except OSError as os_error:
                            app_logger.error(f"OS error writing file: {os_error}")
                            QMessageBox.critical(self, "Export Error", 
                                               f"System error writing file:\n{str(os_error)}")
                            return
                        except json.JSONEncodeError as json_error:
                            app_logger.error(f"JSON encoding error: {json_error}")
                            QMessageBox.critical(self, "Export Error", 
                                               f"Error encoding data to JSON:\n{str(json_error)}")
                            return
                        except UnicodeEncodeError as unicode_error:
                            app_logger.error(f"Unicode encoding error: {unicode_error}")
                            QMessageBox.critical(self, "Export Error", 
                                               f"Text encoding error:\n{str(unicode_error)}")
                            return
                            
                    elif file_path.endswith('.csv'):
                        # CSV export placeholder with logging
                        app_logger.warning("CSV export not yet implemented")
                        QMessageBox.information(self, "Export Info", 
                                              "CSV export feature is not yet implemented.\nPlease use JSON format.")
                        return
                    else:
                        app_logger.warning(f"Unsupported file format: {file_path}")
                        QMessageBox.warning(self, "Export Warning", 
                                          "Unsupported file format. Please use .json extension.")
                        return
                    
                    # Success message
                    QMessageBox.information(self, "Export Complete", 
                                          f"Results exported successfully to:\n{file_path}")
                    
                except Exception as file_error:
                    app_logger.error(f"Unexpected error during file operations: {file_error}", exc_info=True)
                    QMessageBox.critical(self, "Export Error", 
                                       f"Unexpected error during export:\n{str(file_error)}")
            else:
                app_logger.debug("Export cancelled by user")
                
        except Exception as e:
            app_logger.error(f"Critical error in export_report: {e}", exc_info=True)
            QMessageBox.critical(self, "Export Error", f"Failed to export results:\n{str(e)}")
            
    def show_settings(self):
        """Show settings dialog."""
        try:
            app_logger.debug("Opening settings dialog")
            QMessageBox.information(self, "Settings", "Settings panel coming soon!")
        except Exception as e:
            app_logger.error(f"Error showing settings dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", "Failed to open settings dialog")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminPanelUI()
    window.show()
    sys.exit(app.exec_())