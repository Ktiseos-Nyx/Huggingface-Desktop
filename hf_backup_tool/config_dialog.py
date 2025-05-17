import logging
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QMessageBox,
)
from custom_exceptions import ConfigError
from config_manager import (
    set_api_token,
    get_api_token,
    get_rate_limit_delay,
    set_rate_limit_delay,
    set_proxy,
    get_proxy,
    get_max_concurrent_downloads,
    set_max_concurrent_downloads,
    get_auto_clear_completed_downloads,
    set_auto_clear_completed_downloads,
    get_max_concurrent_upload_jobs,
    set_max_concurrent_upload_jobs,
    get_auto_clear_completed_uploads,
    set_auto_clear_completed_uploads,
)

logger = logging.getLogger(__name__)

def obfuscate_token(token):
    obfuscated = "".join([chr(ord(c) + 5) for c in token])
    return obfuscated

def deobfuscate_token(obfuscated):
    original = "".join([chr(ord(c) - 5) for c in obfuscated])
    return original

class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuration")
        self.init_ui()
        self.load_config_values()

    def init_ui(self):
        self.api_token_label = QLabel("Hugging Face API Token:")
        self.api_token_input = QLineEdit()
        self.api_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.use_proxy_checkbox = QCheckBox("Use Proxy")
        self.http_proxy_label = QLabel("HTTP Proxy:")
        self.http_proxy_input = QLineEdit()
        self.https_proxy_label = QLabel("HTTPS Proxy:")
        self.https_proxy_input = QLineEdit()
        self.rate_limit_label = QLabel("Rate Limit Delay (seconds):")
        self.rate_limit_input = QLineEdit()
        self.max_concurrent_label = QLabel("Max Concurrent Downloads:")
        self.max_concurrent_input = QLineEdit()
        self.auto_clear_checkbox = QCheckBox("Auto-clear completed downloads")
        self.max_concurrent_upload_label = QLabel("Max Concurrent Upload Jobs:")
        self.max_concurrent_upload_input = QLineEdit()
        self.auto_clear_upload_checkbox = QCheckBox("Auto-clear completed uploads")
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        layout = QVBoxLayout()
        layout.addWidget(self.api_token_label)
        layout.addWidget(self.api_token_input)
        layout.addWidget(self.use_proxy_checkbox)
        layout.addWidget(self.http_proxy_label)
        layout.addWidget(self.http_proxy_input)
        layout.addWidget(self.https_proxy_label)
        layout.addWidget(self.https_proxy_input)
        layout.addWidget(self.rate_limit_label)
        layout.addWidget(self.rate_limit_input)
        layout.addWidget(self.max_concurrent_label)
        layout.addWidget(self.max_concurrent_input)
        layout.addWidget(self.auto_clear_checkbox)
        layout.addWidget(self.max_concurrent_upload_label)
        layout.addWidget(self.max_concurrent_upload_input)
        layout.addWidget(self.auto_clear_upload_checkbox)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.save_button.clicked.connect(self.save_config)
        self.cancel_button.clicked.connect(self.close)

    def load_config_values(self):
        self.api_token_input.setText(get_api_token() or "")
        proxy_settings = get_proxy()
        self.use_proxy_checkbox.setChecked(
            proxy_settings.get("use_proxy", "False") == "True"
        )
        self.http_proxy_input.setText(proxy_settings.get("http", ""))
        self.https_proxy_input.setText(proxy_settings.get("https", ""))
        self.rate_limit_input.setText(str(get_rate_limit_delay()))
        self.max_concurrent_input.setText(str(get_max_concurrent_downloads()))
        self.auto_clear_checkbox.setChecked(get_auto_clear_completed_downloads())
        self.max_concurrent_upload_input.setText(str(get_max_concurrent_upload_jobs()))
        self.auto_clear_upload_checkbox.setChecked(get_auto_clear_completed_uploads())

    def save_config(self):
        api_token = self.api_token_input.text()
        try:
            rate_limit_delay = float(self.rate_limit_input.text())
            if rate_limit_delay < 0:
                raise ValueError("Rate limit delay must be a non-negative number.")
            max_concurrent_downloads = int(self.max_concurrent_input.text())
            if max_concurrent_downloads <= 0:
                raise ValueError("Max concurrent downloads must be a positive integer.")
            max_concurrent_upload_jobs = int(self.max_concurrent_upload_input.text())
            if max_concurrent_upload_jobs <= 0:
                raise ValueError("Max concurrent upload jobs must be a positive integer.")
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        try:
            set_api_token(api_token)
            proxy_settings = {
                "use_proxy": str(self.use_proxy_checkbox.isChecked()),
                "http": self.http_proxy_input.text(),
                "https": self.https_proxy_input.text(),
            }
            set_proxy(proxy_settings)
            set_rate_limit_delay(rate_limit_delay)
            set_max_concurrent_downloads(max_concurrent_downloads)
            set_auto_clear_completed_downloads(self.auto_clear_checkbox.isChecked())
            set_max_concurrent_upload_jobs(max_concurrent_upload_jobs)
            set_auto_clear_completed_uploads(self.auto_clear_upload_checkbox.isChecked())
            QMessageBox.information(
                self, "Success", "Configuration saved successfully."
            )
            self.accept()
        except ConfigError as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
