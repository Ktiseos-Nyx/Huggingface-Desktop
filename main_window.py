import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QPushButton,
                             QMessageBox, QSizePolicy, QMenuBar, QMenu, QApplication)
from PyQt6.QtGui import QAction
from zip_app import ZipApp
from hf_uploader import HuggingFaceUploader
from download_app import DownloadApp
from theme_handler import apply_theme, get_available_themes
from custom_exceptions import ConfigError
logger = logging.getLogger(__name__)

class MainWindow(QWidget):
    """Main application window."""

    def __init__(self, app):  # Accept the QApplication instance
        super().__init__()
        logger.info("MainWindow initializing...")
        self.setWindowTitle("Hugging Face Backup Tool")
        self.app = app  # Store the QApplication instance

        # Create instances of your widgets
        logger.info("Creating widget instances...")
        self.zip_app = ZipApp()
        logger.info("ZipApp created")
        self.hf_uploader = HuggingFaceUploader()
        logger.info("HuggingFaceUploader created")
        self.download_app = DownloadApp()
        logger.info("DownloadApp created")
        self.config_dialog = None

        # Tab widget
        logger.info("Creating tab widget...")
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.hf_uploader, "Hugging Face Uploader")
        logger.info("HF Uploader tab added")
        self.tab_widget.addTab(self.zip_app, "Zip Folder")
        logger.info("ZipApp tab added")
        self.tab_widget.addTab(self.download_app, "Download")
        logger.info("DownloadApp Tab Added")

        # Set the initial tab
        self.tab_widget.setCurrentIndex(0)
        logger.info("Initial tab set")

        # Exit Button
        logger.info("Creating exit button...")
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        logger.info("Exit button created and connected")

        # Create Menu Bar
        logger.info("Creating menu bar...")
        self.menu_bar = QMenuBar(self)
        self.theme_menu = QMenu("Theme", self)
        self.menu_bar.addMenu(self.theme_menu)
        logger.info("Menu bar and theme menu created")

        # List available themes
        logger.info("Listing available themes...")
        available_themes = get_available_themes()
        self.theme_actions = {}

        logger.info(f"Found themes: {available_themes}")

        logger.info("Creating theme actions...")
        for theme in available_themes:
            logger.info(f"Processing theme: {theme}")
            action = QAction(theme, self)
            action.triggered.connect(lambda checked=False, theme_name=theme: self.change_theme(theme_name))
            self.theme_menu.addAction(action)
            self.theme_actions[theme] = action
            logger.info(f"Action created for theme: {theme}")

        logger.info("Theme actions created")

        # Layout Setup
        # Create a layout for the main window
        logger.info("Creating main layout...")
        main_layout = QVBoxLayout()
        main_layout.setMenuBar(self.menu_bar)
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(self.exit_button)
        logger.info("Main layout created")

        # Make the window resizable
        logger.info("Setting size policy...")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        logger.info("Size policy set")

        # Set the layout for the main window
        logger.info("Setting layout...")
        self.setLayout(main_layout)
        logger.info("Layout set")

        # Set the initial size of the window
        logger.info("Setting initial size...")
        self.resize(800, 600)
        logger.info("Initial size set")

        logger.info("MainWindow initialized")

        # Load Theme
        apply_theme(self.app, theme_name='dark_teal.xml')  # Apply the theme

    def change_theme(self, theme_name):
        """Changes the application theme at runtime."""
        apply_theme(self.app, theme_name=theme_name)
        logger.info(f"Theme changed to {theme_name}")

    def closeEvent(self, event):
        """Handles the window close event."""
        reply = QMessageBox.question(self, 'Exit',
                                     "Are you sure you want to exit?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()