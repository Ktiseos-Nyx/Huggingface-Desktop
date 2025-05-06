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
from config_manager import config, save_config


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
        super().__init__()
        self.setWindowTitle("Configuration")

        # --- API Token Section ---
        self.api_token_label = QLabel("Hugging Face API Token:")
        self.api_token_input = QLineEdit()  # No default
        self.api_token_input.setEchoMode(QLineEdit.EchoMode.Password)  # Mask the token

        # --- Proxy Section ---
        self.use_proxy_checkbox = QCheckBox("Use Proxy")
        self.use_proxy_checkbox.setChecked(config.getboolean("Proxy", "use_proxy"))
        self.http_proxy_label = QLabel("HTTP Proxy:")
        self.http_proxy_input = QLineEdit(config["Proxy"]["http"])
        self.https_proxy_label = QLabel("HTTPS Proxy:")
        self.https_proxy_input = QLineEdit(config["Proxy"]["https"])
        self.rate_limit_label = QLabel("Rate Limit Delay (seconds):")
        self.rate_limit_input = QLineEdit(config["HuggingFace"]["rate_limit_delay"])

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

        # Obfuscate the API token
        obfuscated_token = obfuscate_token(api_token)

        # Save proxy settings
        config["Proxy"]["use_proxy"] = str(self.use_proxy_checkbox.isChecked())
        config["Proxy"]["http"] = self.http_proxy_input.text()
        config["Proxy"]["https"] = self.https_proxy_input.text()
        config["HuggingFace"]["rate_limit_delay"] = str(
            rate_limit_delay
        )  # Store as string
        config["HuggingFace"]["api_token"] = obfuscated_token  # Obfuscated API token

        # Write to config file
        try:
            if save_config():  # Call save_config and check for success
                QMessageBox.information(
                    self, "Success", "Configuration saved successfully."
                )
                self.close()
            else:
                QMessageBox.critical(self, "Error", "Failed to save configuration.")
        except ConfigError as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")