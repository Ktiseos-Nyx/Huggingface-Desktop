import logging
from config_dialog import ConfigDialog
from download_app import DownloadApp
from hf_upload import HuggingFaceUploader  # Corrected import
from zip_app import ZipApp
from theme_handler import apply_theme, get_available_themes
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QTabWidget,
    QSizePolicy,
)

logger = logging.getLogger(__name__)

#


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
        self.tab_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.create_layout_and_widgets()
        
        # Set a reasonable default size based on screen size
        screen_size = self.app.primaryScreen().size()
        window_width = min(int(screen_size.width() * 0.7), 1000)
        window_height = min(int(screen_size.height() * 0.8), 800)
        self.resize(window_width, window_height)
        try:
            apply_theme(self.app, theme_name="dark_teal.xml")
        except Exception as e:
            logger.error(f"Error applying initial theme: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to apply default theme: {e}"
            )
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
                lambda checked=False, theme_name=theme: self.change_theme(
                    theme_name
                )
            )
            self.theme_menu.addAction(action)
            self.theme_actions[theme] = action
        logger.debug("Setting tab widget as central widget")
        self.setCentralWidget(self.tab_widget)

    def show_config_dialog(self):
        if not self.config_dialog:
            self.config_dialog = ConfigDialog()
        self.config_dialog.exec()

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
