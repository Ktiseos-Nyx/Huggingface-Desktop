import logging
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from custom_exceptions import ConfigError  # Import ConfigError
from config_manager import (
    config,
    set_api_token,
    get_api_token,
    get_rate_limit_delay,
    set_rate_limit_delay,  # Make sure this is imported
    set_proxy,
    get_proxy,
    # save_config # You don't really need to import save_config directly in the ConfigDialog
)


logger = logging.getLogger(__name__)


def obfuscate_token(token):
    """A simple obfuscation function (DO NOT RELY ON THIS FOR SECURITY)."""
    obfuscated = "".join([chr(ord(c) + 5) for c in token])  # Shift each character by 5
    return obfuscated


def deobfuscate_token(obfuscated):
    """Reverses the obfuscation (DO NOT RELY ON THIS FOR SECURITY)."""
    original = "".join([chr(ord(c) - 5) for c in obfuscated])
    return original


class ConfigDialog(QWidget):
    """Dialog for configuring settings."""

    def __init__(self):
        """Initializes the configuration dialog."""
        super().__init__()
        self.setWindowTitle("Configuration")
        self.init_ui()
        self.load_config_values()

    def init_ui(self):
        """Initializes the user interface elements and layout."""
        # --- API Token Section ---
        self.api_token_label = QLabel("Hugging Face API Token:")
        self.api_token_input = QLineEdit()  # No default
        self.api_token_input.setEchoMode(QLineEdit.EchoMode.Password)  # Mask the token

        # --- Proxy Section ---
        self.use_proxy_checkbox = QCheckBox("Use Proxy")
        # self.use_proxy_checkbox.setChecked(config.getboolean("Proxy", "use_proxy"))
        self.http_proxy_label = QLabel("HTTP Proxy:")
        self.http_proxy_input = QLineEdit()  # No default - filled from load
        self.https_proxy_label = QLabel("HTTPS Proxy:")
        self.https_proxy_input = QLineEdit()  # No default - filled from load
        self.rate_limit_label = QLabel("Rate Limit Delay (seconds):")
        self.rate_limit_input = QLineEdit()

        # --- Buttons ---
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        # Layout
        layout = QVBoxLayout()

        # API Token section
        layout.addWidget(self.api_token_label)
        layout.addWidget(self.api_token_input)

        # Proxy Section
        layout.addWidget(self.use_proxy_checkbox)
        layout.addWidget(self.http_proxy_label)
        layout.addWidget(self.http_proxy_input)
        layout.addWidget(self.https_proxy_label)
        layout.addWidget(self.https_proxy_input)

        layout.addWidget(self.rate_limit_label)
        layout.addWidget(self.rate_limit_input)

        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connections
        self.save_button.clicked.connect(self.save_config)
        self.cancel_button.clicked.connect(self.close)

    def load_config_values(self):
        """Loads configuration values from the config manager and populates the UI."""
        # Load API token
        self.api_token_input.setText(get_api_token() or "")  # Load the API token
        # Load Proxy settings
        proxy_settings = get_proxy()
        self.use_proxy_checkbox.setChecked(
            proxy_settings.get("use_proxy", "False") == "True"
        )
        self.http_proxy_input.setText(proxy_settings.get("http", ""))
        self.https_proxy_input.setText(proxy_settings.get("https", ""))
        # Load Rate limit delay
        self.rate_limit_input.setText(str(get_rate_limit_delay()))

    def save_config(self):
        """Saves the configuration settings."""
        api_token = self.api_token_input.text()

        # Input validation for rate limit delay
        try:
            rate_limit_delay = float(self.rate_limit_input.text())
            if rate_limit_delay < 0:
                raise ValueError("Rate limit delay must be a non-negative number.")
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        # Save the config values
        try:
            # Set API token
            set_api_token(api_token)  # Store the api token in the manager

            # Save proxy settings
            proxy_settings = {
                "use_proxy": str(self.use_proxy_checkbox.isChecked()),
                "http": self.http_proxy_input.text(),
                "https": self.https_proxy_input.text(),
            }
            set_proxy(proxy_settings)  #  save proxy settings
            # Save rate limit
            # config["HuggingFace"]["rate_limit_delay"] = str(rate_limit_delay)
            set_rate_limit_delay(rate_limit_delay)
            QMessageBox.information(
                self, "Success", "Configuration saved successfully."
            )
            self.close()
        except ConfigError as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
        except Exception as e:
            # Catch any unexpected errors
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
