import logging
from config_dialog import ConfigDialog
from download_app import DownloadApp
from hf_upload import HuggingFaceUploader  # Corrected import
from zip_app import ZipApp
from theme_handler import apply_theme, get_available_themes
from PyQt6.QtGui import QAction, QIcon, QAction
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QTabWidget,
)
from config_manager import get_window_width, get_window_height, set_window_size # Import window functions

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()
        logger.info("MainWindow initializing...")
        self.setWindowTitle("Hugging Face Backup Tool")
        self.app = app
        self.uploader_thread = None
        logger.debug("Creating widget instances")
        self.zip_app = ZipApp()
        self.hf_uploader = HuggingFaceUploader()
        self.download_app = DownloadApp()
        self.config_dialog = None
        logger.debug("Creating tab widget")
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.hf_uploader, "Hugging Face Uploader")
        self.tab_widget.addTab(self.zip_app, "Zip Folder")
        self.tab_widget.addTab(self.download_app, "Download")
        self.create_layout_and_widgets()

        # Load window size from config
        width = get_window_width()  # Use get_window_width()
        height = get_window_height() # Use get_window_height()
        self.resize(width, height)  # Load window dimensions

        try:
            apply_theme(self.app, theme_name="dark_teal.xml")
        except Exception as e:
            logger.error(f"Error applying initial theme: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply default theme: {e}")
        logger.info("MainWindow initialized")

    def create_layout_and_widgets(self):
        logger.debug("Creating menu bar and theme menu")
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        self.theme_menu = QMenu("Theme", self)
        self.menu_bar.addMenu(self.theme_menu)
        self.file_menu = QMenu("File", self)
        self.menu_bar.addMenu(self.file_menu)
        self.config_action = QAction("Configure", self)
        self.config_action.triggered.connect(self.show_config_dialog)
        self.file_menu.addAction(self.config_action)
        logger.debug("Listing available themes")
        available_themes = get_available_themes()
        self.theme_actions = {}
        for theme in available_themes:
            logger.debug(f"Creating action for theme: {theme}")
            action = QAction(theme, self)
            action.triggered.connect(
                lambda checked=False, theme_name=theme: self.change_theme(theme_name)
            )
            self.theme_menu.addAction(action)
            self.theme_actions[theme] = action
        logger.debug("Setting tab widget as central widget")
        self.setCentralWidget(self.tab_widget)

        self.resolution_menu = QMenu("Resolution", self)  # NEW
        self.menu_bar.addMenu(self.resolution_menu)  # NEW
        self.create_resolution_actions()  # NEW

        self.central_widget = QWidget()  # Create a central widget
        main_layout = QVBoxLayout(self.central_widget) # This line has to change
        self.setCentralWidget(self.central_widget)  # And this one.
        main_layout.setContentsMargins(10, 10, 10, 10)
        # Set a minimum size for the main window,
        main_layout.setSpacing(10)
        # Add the resolution items.

    def show_config_dialog(self):
        if not self.config_dialog:
            self.config_dialog = ConfigDialog()
        if self.config_dialog.exec():
             self.resize(get_window_width(), get_window_height()) # resize the window if the values are changed.

    def change_theme(self, theme_name):
        try:
            apply_theme(self.app, theme_name)
            logger.info(f"Theme changed to {theme_name}")
        except Exception as e:
            logger.error(f"Error changing theme: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply theme: {e}")

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            logger.debug("Close event accepted")
            if self.hf_uploader:
                self.hf_uploader.closeEvent(event)
                if not event.isAccepted():
                    return
            event.accept()
        else:
            event.ignore()

    def __del__(self):
        logger.debug("MainWindow is being destroyed")

    def create_resolution_actions(self):
        self.resolution_actions = {}
        resolutions = [  # Define your resolution options here
            (640, 480),
            (800, 600),
            (1024, 768),
            (1280, 720),
            (1920, 1080),
            # ... add other resolutions
        ]

        for width, height in resolutions:
            action_text = f"{width} x {height}"
            action = QAction(action_text, self)
            action.triggered.connect(lambda checked=False, w=width, h=height: self.set_window_size(w, h)) # CONNECTS TO FUNCTION
            self.resolution_menu.addAction(action)
            self.resolution_actions[(width, height)] = action  # Store for later use
    def set_window_size(self, width: int, height: int):
        """Sets the window size."""
        self.resize(width, height) # Sets the dimensions
        set_window_size(width, height)