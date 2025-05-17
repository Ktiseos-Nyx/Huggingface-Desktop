import logging
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from custom_exceptions import ConfigError
from main_window import MainWindow
from theme_handler import apply_theme, check_qt_material

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def start_application():
    logger.info("Starting Hugging Face Backup Tool...")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    logger.info("QApplication retrieved or created.")
    try:
        if check_qt_material():
            apply_theme(app, theme_name="dark_teal.xml")
            logger.info("Stylesheet applied.")
        else:
            QMessageBox.critical(None, "Error", "qt_material library is not installed.")
            sys.exit(1)
        window = MainWindow(app)
        logger.info("MainWindow created.")
        window.show()
        logger.info("MainWindow shown.")
        logger.info("Starting QApplication event loop...")
        app.exec()
    except ConfigError as e:
        logger.error(f"Configuration error: {e}", exc_info=True)
        QMessageBox.critical(None, "Error", f"A configuration error occurred: {e}")
        return 1
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {e}", exc_info=True)
        QMessageBox.critical(None, "Error", f"An unexpected error occurred: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(start_application())
