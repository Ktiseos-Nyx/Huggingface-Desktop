# hf_backup_tool/ui/hf_uploader.py
import logging
import subprocess
import os
import glob
import traceback

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QTextEdit,
    QCheckBox,
    QComboBox,
    QListWidget,
    QProgressBar,
)
from PyQt6.QtGui import QAction
from hf_uploader_thread import HFUploaderThread
from config_manager import config

logger = logging.getLogger(__name__)


class HuggingFaceUploader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hugging Face Uploader")
        self.init_ui()

    def init_ui(self):
        # Main vertical layout to stack all sections
        # Set margins and spacing for the main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(
            10, 10, 10, 10
        )  # Margins around the whole layout
        main_layout.setSpacing(10)  # Space between widgets

        # --- Config Section ---
        header_config = QLabel("Configuration")
        header_config.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_config)
        # Button to edit API token
        config_layout = QHBoxLayout()
        self.edit_config_button = QPushButton("Edit HF API Token")
        config_layout.addWidget(self.edit_config_button)
        main_layout.addLayout(config_layout)

        # --- Repository Info ---
        header_repo = QLabel("Repository Information")
        header_repo.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_repo)
        # Owner, Repo, and Repo Type
        repo_layout = QGridLayout()
        self.org_label = QLabel("Owner:")
        self.org_input = QLineEdit()
        self.repo_label = QLabel("Repo:")
        self.repo_input = QLineEdit()
        self.repo_type_label = QLabel("Repo Type:")
        self.repo_type_dropdown = QComboBox()
        self.repo_type_dropdown.addItems(["model", "dataset", "space"])

        # Place widgets in grid
        repo_layout.addWidget(self.org_label, 0, 0)
        repo_layout.addWidget(self.org_input, 0, 1)
        repo_layout.addWidget(self.repo_label, 0, 2)
        repo_layout.addWidget(self.repo_input, 0, 3)
        repo_layout.addWidget(self.repo_type_label, 1, 0)
        repo_layout.addWidget(self.repo_type_dropdown, 1, 1)
        main_layout.addLayout(repo_layout)

        # --- Directory Selection ---
        header_dir = QLabel("Directory Selection")
        header_dir.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_dir)
        dir_layout = QHBoxLayout()
        self.directory_label = QLabel("Current Directory:")
        self.directory_input = QLineEdit(os.getcwd())  # Default to current dir
        self.select_dir_button = QPushButton("Select Directory")
        self.update_dir_button = QPushButton("Update Dir")
        dir_layout.addWidget(self.directory_label)
        dir_layout.addWidget(self.directory_input)
        dir_layout.addWidget(self.select_dir_button)
        dir_layout.addWidget(self.update_dir_button)
        main_layout.addLayout(dir_layout)

        # --- File Type and Sorting ---
        header_files = QLabel("File Settings")
        header_files.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_files)
        file_type_layout = QHBoxLayout()
        self.file_type_label = QLabel("File Type:")
        self.file_type_dropdown = QComboBox()
        # Add file types (name, extension)
        self.file_types = [
            ("SafeTensors", "safetensors"),
            ("PyTorch Models", "pt"),
            ("PyTorch Legacy", "pth"),
            ("ONNX Models", "onnx"),
            ("TensorFlow Models", "pb"),
            ("Keras Models", "h5"),
            ("Checkpoints", "ckpt"),
            ("Binary Files", "bin"),
            ("JSON Files", "json"),
            ("YAML Files", "yaml"),
            ("YAML Alt", "yml"),
            ("Text Files", "txt"),
            ("CSV Files", "csv"),
            ("Pickle Files", "pkl"),
            ("PNG Images", "png"),
            ("JPEG Images", "jpg"),
            ("JPEG Alt", "jpeg"),
            ("WebP Images", "webp"),
            ("GIF Images", "gif"),
            ("ZIP Archives", "zip"),
            ("TAR Files", "tar"),
            ("GZ Archives", "gz"),
        ]
        for name, ext in self.file_types:
            self.file_type_dropdown.addItem(name, ext)

        self.sort_by_label = QLabel("Sort By:")
        self.sort_by_dropdown = QComboBox()
        self.sort_by_dropdown.addItems(["name", "date"])

        file_type_layout.addWidget(self.file_type_label)
        file_type_layout.addWidget(self.file_type_dropdown)
        file_type_layout.addWidget(self.sort_by_label)
        file_type_layout.addWidget(self.sort_by_dropdown)
        main_layout.addLayout(file_type_layout)

        # --- Commit Message ---
        header_commit = QLabel("Commit Message")
        header_commit.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_commit)
        commit_layout = QVBoxLayout()
        self.commit_message_label = QLabel("Commit Message:")
        self.commit_message_input = QTextEdit(
            "Upload with Earth & Dusk Huggingface 🤗 Backup"
        )
        commit_layout.addWidget(self.commit_message_label)
        commit_layout.addWidget(self.commit_message_input)
        main_layout.addLayout(commit_layout)

        # --- Options ---
        header_options = QLabel("Options")
        header_options.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_options)
        options_layout = QHBoxLayout()
        self.create_pr_checkbox = QCheckBox("Create Pull Request")
        self.check_repo_exists_checkbox = QCheckBox("Check if Repo Exists")
        self.create_repo_checkbox = QCheckBox("Create Repository if it doesn't exist")
        self.create_repo_checkbox.setEnabled(False)
        self.clear_after_checkbox = QCheckBox("Clear output after upload")
        self.clear_after_checkbox.setChecked(True)
        options_layout.addWidget(self.create_pr_checkbox)
        options_layout.addWidget(self.check_repo_exists_checkbox)
        options_layout.addWidget(self.create_repo_checkbox)
        options_layout.addWidget(self.clear_after_checkbox)
        main_layout.addLayout(options_layout)

        # --- File List ---
        header_files_list = QLabel("Files to Upload")
        header_files_list.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_files_list)
        self.file_list = QListWidget()
        main_layout.addWidget(QLabel("Files to Upload:"))
        main_layout.addWidget(self.file_list)

        # --- Output and Progress ---
        header_output = QLabel("Output & Progress")
        header_output.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_output)
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Status: Ready")
        self.progress_percent_label = QLabel("0%")
        output_layout.addWidget(self.output_text)
        output_layout.addWidget(self.progress_bar)
        output_layout.addWidget(self.progress_label)
        output_layout.addWidget(self.progress_percent_label)
        main_layout.addLayout(output_layout)

        # --- Buttons ---
        header_buttons = QLabel("Buttons")
        header_buttons.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_buttons)
        button_layout = QHBoxLayout()
        self.update_files_button = QPushButton("Update Files")
        self.upload_button = QPushButton("Upload")
        self.cancel_button = QPushButton("Cancel")
        self.clear_output_button = QPushButton("Clear Output")
        button_layout.addWidget(self.update_files_button)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.clear_output_button)

        # Set the main layout
        self.setLayout(main_layout)

        # --- Connect signals to slots ---
        self.edit_config_button.clicked.connect(self.edit_config)
        self.select_dir_button.clicked.connect(self.select_directory)
        self.update_dir_button.clicked.connect(self.update_directory)
        self.update_files_button.clicked.connect(self.update_files)
        self.upload_button.clicked.connect(self.start_upload)
        self.cancel_button.clicked.connect(self.cancel_upload)
        self.clear_output_button.clicked.connect(self.clear_output)

        # Additional initializations if needed
        # e.g., self.file_types = [...] (already defined above)

    def edit_config(self):
        """Opens the configuration dialog."""
        self.config_dialog = ConfigDialog()  # Make it a class member
        self.config_dialog.show()

    def select_directory(self):
        """Opens a dialog to select a directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select a Directory")
        if directory:
            self.directory_input.setText(directory)
            self.current_directory = directory
            self.directory_label.setText(f"Current Directory: {self.current_directory}")
            self.update_files()

    def update_directory(self):
        """Updates the current directory and file list."""
        new_dir = self.directory_input.text()
        if os.path.isdir(new_dir):
            self.current_directory = new_dir
            self.directory_label.setText(f"Current Directory: {self.current_directory}")
            self.update_files()
        else:
            self.output_text.append("❌ Invalid Directory")

    def toggle_create_repo_checkbox(self, state):
        """Enables/disables the create repo checkbox based on the check repo checkbox."""
        if state == 0:  # Unchecked
            self.create_repo_checkbox.setChecked(False)
            self.create_repo_checkbox.setEnabled(False)
        else:
            self.create_repo_checkbox.setEnabled(True)

    def update_files(self):
        """Updates the file list based on the selected file type."""
        self.file_list.clear()
        file_extension = self.file_type_dropdown.currentData()
        try:
            all_files = glob.glob(
                os.path.join(self.current_directory, f"*.{file_extension}")
            )
            filtered_files = []
            for file_path in all_files:
                if os.path.islink(file_path):
                    self.output_text.append(f"ℹ️ Skipping symlink: {file_path}")
                    continue
                if not os.path.isfile(file_path):
                    self.output_text.append(f"ℹ️ Skipping non-file: {file_path}")
                    continue
                filtered_files.append(file_path)

            all_ckpts = sorted(
                filtered_files,
                key=(
                    os.path.getmtime
                    if self.sort_by_dropdown.currentText() == "date"
                    else str
                ),
            )

            self.file_list.addItems(all_ckpts)
            self.output_text.append(
                f"✨ Found {len(all_ckpts)} {file_extension} files in {self.current_directory}"
            )

        except Exception as e:
            logger.error(f"File listing error: {e}", exc_info=True)  # Log
            self.output_text.append(f"❌ Error listing files: {str(e)}")

    def start_upload(self):
        """Starts the upload process in a separate thread."""
        if not self.org_input.text() or not self.repo_input.text():
            self.output_text.append(
                "❗ Please fill in both Organization/Username and Repository name"
            )
            return

        if self.check_repo_exists_checkbox.isChecked() and not self.repo_exists(
            f"{self.org_input.text()}/{self.repo_input.text()}"
        ):
            if not self.create_repo_checkbox.isChecked():
                self.output_text.append(
                    "❗ Repository does not exist and creation is not enabled."
                )
                return

        repo_id = f"{self.org_input.text()}/{self.repo_input.text()}"
        selected_files = [item.text() for item in self.file_list.selectedItems()]
        repo_type = self.repo_type_dropdown.currentText()
        repo_folder = self.repo_folder_input.text().strip()
        current_directory = self.directory_input.text()
        commit_msg = self.commit_message_input.toPlainText()
        rate_limit_delay = config["HuggingFace"]["rate_limit_delay"]

        if not selected_files:
            self.output_text.append(
                "📝 Nothing selected for upload. Please select files from the list."
            )
            return

        self.upload_button.setEnabled(False)
        self.cancel_upload_button.setEnabled(True)

        self.uploader_thread = HFUploaderThread(
            self.api,
            repo_id,
            selected_files,
            repo_type,
            repo_folder,
            current_directory,
            commit_msg,
            self.create_pr_checkbox.isChecked(),
            rate_limit_delay,
        )

        self.uploader_thread.signal_status.connect(self.update_status)
        self.uploader_thread.signal_progress.connect(self.update_progress)
        self.uploader_thread.signal_output.connect(self.update_output)
        self.uploader_thread.signal_finished.connect(self.upload_finished)
        self.uploader_thread.start()

    def cancel_upload(self):
        """Cancels the upload process."""
        if self.uploader_thread and self.uploader_thread.isRunning():
            self.uploader_thread.stop()
            self.uploader_thread.wait()
            self.upload_finished()

    def update_status(self, message):
        """Updates the status label."""
        self.progress_label.setText(message)

    def update_progress(self, value):
        """Updates the progress bar."""
        self.progress_bar.setValue(value)
        self.progress_percent_label.setText(f"{value}%")

    def update_output(self, message):
        """Appends a message to the output text."""
        self.output_text.append(message)

    def upload_finished(self):
        """Resets the UI after the upload is finished."""
        self.upload_button.setEnabled(True)
        self.cancel_upload_button.setEnabled(False)
        self.progress_label.setText("Ready.")
        self.progress_percent_label.setText("0%")
        if self.clear_after_checkbox.isChecked():
            self.clear_output()

    def clear_output(self):
        """Clears the output text."""
        self.output_text.clear()

    def repo_exists(self, repo_id):
        """Checks if a repository exists on Hugging Face Hub."""
        try:
            # Use the 'huggingface-cli' command to check repository existence.
            result = subprocess.run(
                ["huggingface-cli", "repo", "info", repo_id, "--json"],
                capture_output=True,
                text=True,
                check=True,
            )
            # If the command succeeds, the repo exists.  We don't parse the JSON.
            return True
        except subprocess.CalledProcessError as e:
            # Repo doesn't exist or other error.  We'll check for 404 specifically.
            if (
                "404 Client Error" in e.stderr
            ):  # Or check for a more specific error message
                return False
            else:
                return False  # Other errors, consider repo doesn't exist, or handle differently
        except FileNotFoundError:
            # huggingface-cli not found.  Handle this case.
            QMessageBox.critical(
                self,
                "Error",
                "The 'huggingface-cli' command was not found. Please ensure you have the Hugging Face CLI installed and in your PATH.",
            )
            return False
