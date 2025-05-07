# hf_backup_tool/main.py
import importlib
import logging
import os
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox
from qt_material import apply_stylesheet  # Removed

from custom_exceptions import ConfigError
from main_window import MainWindow
from theme_handler import apply_theme, check_qt_material

# from hf_backup_tool.ui.theme_handler import apply_theme, check_qt_material #Imported
# from hf_backup_tool.exceptions.custom_exceptions import ConfigError #Import config error


# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info("Starting Hugging Face Backup Tool...")
    app = QApplication(sys.argv)
    logger.info("QApplication created.")

    try:  # Add try statement
        # Check if qt_material is installed
        if check_qt_material():
            apply_theme(app, theme_name="dark_teal.xml")  # Apply the theme
            logger.info("Stylesheet applied.")
        else:
            QMessageBox.critical(None, "Error", "qt_material library is not installed.")
            sys.exit(1)

        window = MainWindow(app)  # Passed the app
        logger.info("MainWindow created.")

        window.show()
        logger.info("MainWindow shown.")

        logger.info("Starting QApplication event loop...")
        sys.exit(app.exec())

    except ConfigError as e:  # Catch config error
        logger.error(f"Configuration error: {e}", exc_info=True)
        QMessageBox.critical(None, "Error", f"A configuration error occurred: {e}")
        sys.exit(1)

    except Exception as e:  # Catch any other error
        logger.error(f"An unhandled exception occurred: {e}", exc_info=True)
        QMessageBox.critical(None, "Error", f"An unexpected error occurred: {e}")
        sys.exit(1)
