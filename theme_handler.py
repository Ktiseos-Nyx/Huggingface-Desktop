import logging
import importlib
from qt_material import apply_stylesheet, list_themes
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


def apply_theme(widget, theme_name="dark_teal.xml"):
    """Applies the specified theme to the given widget."""
    try:
        apply_stylesheet(widget, theme=theme_name)
        logger.info(f"Successfully applied theme: {theme_name}")
    except Exception as e:
        logger.error(f"Error applying theme {theme_name}: {e}", exc_info=True)
        QMessageBox.critical(
            widget, "Error", f"Failed to apply theme {theme_name}: {e}"
        )


def get_available_themes():
    """Returns a list of available themes."""
    try:
        themes = list_themes()
        logger.info(f"Available themes: {themes}")
        return themes
    except Exception as e:
        logger.error(f"Error listing themes: {e}", exc_info=True)
        return []  # Return an empty list in case of error


def check_qt_material():
    """Checks if the qt_material library is installed."""
    try:
        importlib.import_module("qt_material")
        return True
    except ImportError:
        logger.error("qt_material library is not installed.")
        return False


# Example usage in MainWindow:
# if check_qt_material():
#     apply_theme(self.app, theme_name='dark_teal.xml')
# else:
#     QMessageBox.critical(self, "Error", "qt_material library is not installed.")
