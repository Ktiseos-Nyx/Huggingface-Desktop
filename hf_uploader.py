import logging
import os
import glob
import traceback

from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFileDialog, QTextEdit,
                             QCheckBox, QComboBox, QListWidget, QProgressBar, QApplication)  # Import QApplication
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QThread, pyqtSignal  # Import QThread and pyqtSignal

from huggingface_hub import HfApi
#from huggingface_hub import upload_folder #Removed
from config_manager import config  # Needed for Config
from config_dialog import ConfigDialog  # Needed for config
# from keyring_manager import get_api_token, set_api_token, delete_api_token
logger = logging.getLogger(__name__)


def obfuscate_token(token):
    """A simple obfuscation function (DO NOT RELY ON THIS FOR SECURITY)."""
    obfuscated = ''.join([chr(ord(c) + 5) for c in token])  # Shift each character by 5
    return obfuscated


def deobfuscate_token(obfuscated):
    """Reverses the obfuscation (DO NOT RELY ON THIS FOR SECURITY)."""
    original = ''.join([chr(ord(c) - 5) for c in obfuscated])
    return original


class HFUploaderThread(QThread):
    """Thread for uploading files to Hugging Face Hub."""
    signal_status = pyqtSignal(str)
    signal_progress = pyqtSignal(int)
    signal_output = pyqtSignal(str)
    signal_finished = pyqtSignal()

    def __init__(self, api, repo_id, selected_files, repo_type, repo_folder,
                 current_directory, commit_msg, create_pr, rate_limit_delay):
        super().__init__()
        self.api = api
        self.repo_id = repo_id
        self.selected_files = selected_files
        self.repo_type = repo_type
        self.repo_folder = repo_folder
        self.current_directory = current_directory
        self.commit_msg = commit_msg
        self.create_pr = create_pr
        self.rate_limit_delay = rate_limit_delay
        self.stop_flag = False

    def stop(self):
        self.stop_flag = True

    def run(self):
        try:
            total_files = len(self.selected_files)
            uploaded_files = 0

            for file_path in self.selected_files:
                if self.stop_flag:
                    break

                relative_path = os.path.relpath(file_path, self.current_directory)
                repo_path = os.path.join(self.repo_folder, relative_path) if self.repo_folder else relative_path

                self.signal_status.emit(f"Uploading {file_path} to {repo_path}...")

                try:
                    # Simulate a delay for rate limiting
                    import time
                    time.sleep(float(self.rate_limit_delay)) #Rate limit is now a float

                    self.api.upload_file(
                        path_or_fileobj=file_path,  # The actual file path
                        path_in_repo=repo_path,  # Where it goes in the repo
                        repo_id=self.repo_id,
                        repo_type=self.repo_type,
                        commit_message=self.commit_msg,
                        commit_info={"message": self.commit_msg}
                    )

                    uploaded_files += 1
                    progress_percentage = int((uploaded_files / total_files) * 100)
                    self.signal_progress.emit(progress_percentage)
                    self.signal_output.emit(f"Uploaded {file_path} to {self.repo_id}/{repo_path}")

                except Exception as upload_error:
                    logger.error(f"Error uploading {file_path}: {upload_error}", exc_info=True)
                    self.signal_output.emit(f"❌ Error uploading {file_path}: {str(upload_error)}")
                    # Consider whether to stop the entire upload on an error or continue

            self.signal_status.emit("Upload completed.")
            self.signal_finished.emit()

        except Exception as e:
            logger.error(f"Upload error: {e}", exc_info=True)
            self.signal_output.emit(f"❌ Upload error: {str(e)}")
            self.signal_finished.emit()  # Ensure finished signal is always emitted.


class HuggingFaceUploader(QWidget):
    """Widget for uploading files to Hugging Face Hub."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hugging Face Uploader")
        self.uploader_thread = None
        self.config_dialog = None  # Needed for it to be instantiated

        # Initialize current_directory here!
        self.current_directory = ""  # Initialize with a default value (empty string) or os.getcwd()

        # Widgets
        self.config_button = QPushButton("Edit Config (API Token)")
        self.org_label = QLabel("Owner:")
        self.org_input = QLineEdit()
        self.repo_label = QLabel("Repo:")
        self.repo_input = QLineEdit()
        self.repo_type_label = QLabel("Repo Type:")
        self.repo_type_dropdown = QComboBox()
        self.repo_type_dropdown.addItems(['model', 'dataset', 'space'])
        self.repo_folder_label = QLabel("Subfolder:")
        self.repo_folder_input = QLineEdit()
        self.file_type_label = QLabel("File Type:")
        self.file_type_dropdown = QComboBox()
        self.file_types = [
            ('SafeTensors', 'safetensors'),
            ('PyTorch Models', 'pt'),
            ('PyTorch Legacy', 'pth'),
            ('ONNX Models', 'onnx'),
            ('TensorFlow Models', 'pb'),
            ('Keras Models', 'h5'),
            ('Checkpoints', 'ckpt'),
            ('Binary Files', 'bin'),
            ('JSON Files', 'json'),
            ('YAML Files', 'yaml'),
            ('YAML Alt', 'yml'),
            ('Text Files', 'txt'),
            ('CSV Files', 'csv'),
            ('Pickle Files', 'pkl'),
            ('PNG Images', 'png'),
            ('JPEG Images', 'jpg'),
            ('JPEG Alt', 'jpeg'),
            ('WebP Images', 'webp'),
            ('GIF Images', 'gif'),
            ('ZIP Archives', 'zip'),
            ('TAR Files', 'gz')
        ]
        for name, ext in self.file_types:
            self.file_type_dropdown.addItem(name, ext)
        self.sort_by_label = QLabel("Sort By:")
        self.sort_by_dropdown = QComboBox()
        self.sort_by_dropdown.addItems(['name', 'date'])

        # Add directory selection button
        self.directory_label = QLabel(f"Current Directory: {self.current_directory}")
        self.directory_input = QLineEdit(self.current_directory)
        self.directory_select_button = QPushButton("Select Directory")  # New
        self.directory_update_button = QPushButton("Update Dir")

        self.commit_message_label = QLabel("Commit Message:")
        self.commit_message_input = QTextEdit("Upload with Earth & Dusk Huggingface 🤗 Backup")
        self.create_pr_checkbox = QCheckBox("Create Pull Request")
        self.clear_after_checkbox = QCheckBox("Clear output after upload")
        self.clear_after_checkbox.setChecked(True)
        self.update_files_button = QPushButton("Update Files")
        self.upload_button = QPushButton("Upload")
        self.cancel_upload_button = QPushButton("Cancel Upload")
        self.cancel_upload_button.setEnabled(False)
        self.clear_output_button = QPushButton("Clear Output")
        self.file_list = QListWidget()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Ready.")
        self.progress_percent_label = QLabel("0%")

        # Layout
        config_layout = QHBoxLayout()
        config_layout.addWidget(self.config_button)

        repo_layout = QHBoxLayout()
        repo_layout.addWidget(self.org_label)
        repo_layout.addWidget(self.org_input)
        repo_layout.addWidget(self.repo_label)
        repo_layout.addWidget(self.repo_input)
        repo_layout.addWidget(self.repo_type_label)
        repo_layout.addWidget(self.repo_type_dropdown)

        file_type_layout = QHBoxLayout()
        file_type_layout.addWidget(self.file_type_label)
        file_type_layout.addWidget(self.file_type_dropdown)
        file_type_layout.addWidget(self.sort_by_label)
        file_type_layout.addWidget(self.sort_by_dropdown)

        # Update Directory Layout
        directory_layout = QHBoxLayout()
        directory_layout.addWidget(self.directory_label)
        directory_layout.addWidget(self.directory_input)
        directory_layout.addWidget(self.directory_select_button)  # Added button
        directory_layout.addWidget(self.directory_update_button)

        commit_layout = QVBoxLayout()
        commit_layout.addWidget(self.commit_message_label)
        commit_layout.addWidget(self.commit_message_input)

        upload_options_layout = QHBoxLayout()
        upload_options_layout.addWidget(self.create_pr_checkbox)
        upload_options_layout.addWidget(self.clear_after_checkbox)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.update_files_button)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.cancel_upload_button)
        button_layout.addWidget(self.clear_output_button)

        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_percent_label)

        main_layout = QVBoxLayout()
        main_layout.addLayout(config_layout)
        main_layout.addLayout(repo_layout)
        main_layout.addWidget(self.repo_folder_label)
        main_layout.addWidget(self.repo_folder_input)
        main_layout.addLayout(file_type_layout)
        main_layout.addLayout(directory_layout)
        main_layout.addLayout(commit_layout)
        main_layout.addLayout(upload_options_layout)
        main_layout.addWidget(self.update_files_button)
        main_layout.addWidget(self.file_list)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(progress_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.output_text)

        self.setLayout(main_layout)

        # Connections
        self.config_button.clicked.connect(self.edit_config)
        self.directory_select_button.clicked.connect(self.select_directory)  # Add connection for new button
        self.directory_update_button.clicked.connect(self.update_directory)
        self.update_files_button.clicked.connect(self.update_files)
        self.upload_button.clicked.connect(self.start_upload)
        self.cancel_upload_button.clicked.connect(self.cancel_upload)
        self.file_type_dropdown.currentIndexChanged.connect(self.update_files)

    def edit_config(self):
        """Opens the configuration dialog."""
        self.config_dialog = ConfigDialog()  # Initialized here
        self.config_dialog.show()

    def select_directory(self):
        """Opens a dialog to select a directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select a Directory")
        if directory:
            self.directory_input.setText(directory)

    def update_directory(self):
        """Updates the current directory and file list."""
        new_dir = self.directory_input.text()
        if os.path.isdir(new_dir):
            self.current_directory = new_dir
            self.directory_label.setText(f"Current Directory: {self.current_directory}")
            self.update_files()
        else:
            self.output_text.append("❌ Invalid Directory")

    def update_files(self):
        """Updates the file list based on the selected file type."""
        self.file_list.clear()
        file_extension = self.file_type_dropdown.currentData()
        try:
            all_files = glob.glob(os.path.join(self.current_directory, f"*.{file_extension}"))
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
                key=os.path.getmtime if self.sort_by_dropdown.currentText() == 'date' else str
            )

            self.file_list.addItems(all_ckpts)
            self.output_text.append(f"✨ Found {len(all_ckpts)} {file_extension} files in {self.current_directory}")

        except Exception as e:
            logger.error(f"File listing error: {e}", exc_info=True)  # Log
            self.output_text.append(f"❌ Error listing files: {str(e)}")

    def start_upload(self):
        """Starts the upload process in a separate thread."""
        org = self.org_input.text()
        repo = self.repo_input.text()

        if not org or not repo:
            self.output_text.append("❗ Please fill in both Organization/Username and Repository name")
            return

        repo_id = f"{org}/{repo}"
        selected_files = [item.text() for item in self.file_list.selectedItems()]
        repo_type = self.repo_type_dropdown.currentText()
        repo_folder = self.repo_folder_input.text().strip()
        current_directory = self.directory_input.text()
        commit_msg = self.commit_message_input.toPlainText()

        rate_limit_delay = config['HuggingFace']['rate_limit_delay']  # Pull from config
        obfuscated_token = config['HuggingFace']['api_token']  # Obfuscated token from config

        # Deobfuscate:
        api_token = deobfuscate_token(obfuscated_token)

        # Debug: Print the token (remove after verifying!)
        print(f"Deobfuscated token: {api_token}")

        self.upload_button.setEnabled(False)
        self.cancel_upload_button.setEnabled(True) # Enable cancel button

        # Initialize Hugging Face API (Moved here)
        self.api = HfApi(token=api_token)  # Pass the token here to HfApi

        self.uploader_thread = HFUploaderThread(self.api, repo_id, selected_files, repo_type, repo_folder,
                                                 current_directory, commit_msg, False,
                                                 rate_limit_delay)  # Removed create_pr_checkbox

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


if __name__ == '__main__':
    app = QApplication([])
    window = HuggingFaceUploader()
    window.show()
    app.exec()