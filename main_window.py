import logging

from config_dialog import ConfigDialog
from config_manager import config
from custom_exceptions import APIKeyError, ConfigError
from download_app import DownloadApp
from hf_uploader import HuggingFaceUploader
from huggingface_hub import HfApi, upload_folder

# from huggingface_hub.utils import get_hf_home_dir
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QApplication,
)
from theme_handler import apply_theme, get_available_themes
from zip_app import ZipApp

logger = logging.getLogger(__name__)


class MainWindow(QWidget):
    """Main application window."""

    def __init__(self, app: QApplication):  # Accept the QApplication instance
        """Initializes the main window."""
        super().__init__()
        logger.info("MainWindow initializing...")
        self.setWindowTitle("Hugging Face Backup Tool")
        self.app = app  # Store the QApplication instance
        self.uploader_thread = None  # Store the upload thread

        # Create widget instances
        logger.debug("Creating widget instances")
        self.zip_app = ZipApp()
        self.hf_uploader = HuggingFaceUploader()
        self.download_app = DownloadApp()
        self.config_dialog = None

        # Create Tab Widget and add tabs
        logger.debug("Creating tab widget")
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.hf_uploader, "Hugging Face Uploader")
        # Uncomment if you add these tabs later
        # self.tab_widget.addTab(self.zip_app, "Zip Folder")
        # self.tab_widget.addTab(self.download_app, "Download")

        # Exit Button
        logger.debug("Creating exit button")
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)

        # Apply the layouts
        main_layout = self.create_layout()
        self.setLayout(main_layout)

        # Set initial size
        self.resize(800, 600)

        # Apply default theme
        try:
            apply_theme(self.app, theme_name="dark_teal.xml")
        except Exception as e:  # Handle errors during theme application
            logger.error(f"Error applying initial theme: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply default theme: {e}")

        logger.info("MainWindow initialized")

    def create_layout(self):
        """Creates and returns the main layout of the window."""
        # Create Menu Bar for theme selection
        logger.debug("Creating menu bar and theme menu")
        self.menu_bar = QMenuBar(self)
        self.theme_menu = QMenu("Theme", self)
        self.menu_bar.addMenu(self.theme_menu)

        # Create File Menu
        self.file_menu = QMenu("File", self)  # Create the File menu
        self.menu_bar.addMenu(self.file_menu)

        # Add Configure Action (Config Dialog)
        self.config_action = QAction("Configure", self)
        self.config_action.triggered.connect(self.show_config_dialog)
        self.file_menu.addAction(self.config_action)  # Add the action to the File menu

        # List available themes
        logger.debug("Listing available themes")
        available_themes = get_available_themes()
        self.theme_actions = {}
        for theme in available_themes:
            logger.debug(f"Creating action for theme: {theme}")
            action = QAction(theme, self)
            # Use lambda with default argument to capture current theme
            action.triggered.connect(
                lambda checked=False, theme_name=theme: self.change_theme(theme_name)
            )
            self.theme_menu.addAction(action)
            self.theme_actions[theme] = action

        # Create main layout
        logger.debug("Creating main layout")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(
            15, 15, 15, 15
        )  # Margins around the whole layout
        main_layout.setSpacing(12)  # Space between widgets

        # Add menu bar at the top
        main_layout.setMenuBar(self.menu_bar)

        # Add tab widget with stretch factor (more space)
        main_layout.addWidget(self.tab_widget, stretch=8)

        # Add Exit button with less stretch
        main_layout.addWidget(self.exit_button, stretch=1)
        return main_layout

    def show_config_dialog(self):
        """Shows the configuration dialog."""
        if not self.config_dialog:
            self.config_dialog = ConfigDialog()  # Create the dialog
        self.config_dialog.exec()  # Show the dialog
        # Optional: You could refresh some UI elements here if config changes affect them
        # self.hf_uploader.refresh_ui() # example

    def change_theme(self, theme_name):
        """Change the application's theme at runtime."""
        try:
            apply_theme(self.app, theme_name)
            logger.info(f"Theme changed to {theme_name}")
        except Exception as e:
            logger.error(f"Error changing theme: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply theme: {e}")

    def closeEvent(self, event):
        """Handle window close with confirmation."""
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            logger.debug("Close event accepted")
            event.accept()
        else:
            event.ignore()

    def __del__(self):
        logger.debug("MainWindow is being destroyed")
