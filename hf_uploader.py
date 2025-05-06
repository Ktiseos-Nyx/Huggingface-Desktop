import logging
import os
import glob
import traceback
import time  # Import time

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QTextEdit,
    QCheckBox,
    QComboBox,
    QListWidget,
    QProgressBar,
    QApplication,
    QMessageBox,  # Import QMessageBox
    QStackedWidget # Add for showing different widgets
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QThread, pyqtSignal, QObject  # Import QThread and pyqtSignal

from huggingface_hub import HfApi, RepoUrl, upload_file, upload_folder, create_repo  # Import necessary Hugging Face Hub functions
from huggingface_hub.utils import HFValidationError
from requests import HTTPError
from tqdm import tqdm #import tqdm
from config_manager import config  # Needed for Config
from config_dialog import ConfigDialog  # Needed for config
from custom_exceptions import UploadError, APIKeyError

# from keyring_manager import get_api_token, set_api_token, delete_api_token
logger = logging.getLogger(__name__)


def obfuscate_token(token):
    """A simple obfuscation function (DO NOT RELY ON THIS FOR SECURITY)."""
    obfuscated = "".join([chr(ord(c) + 5) for c in token])  # Shift each character by 5
    return obfuscated


def deobfuscate_token(obfuscated):
    """Reverses the obfuscation (DO NOT RELY ON THIS FOR SECURITY)."""
    original = "".join([chr(ord(c) - 5) for c in obfuscated])
    return original

# Custom Progress Callback
class CustomProgressCallback:
    def __init__(self, signal_progress, signal_output, filename):
        self.signal_progress = signal_progress
        self.signal_output = signal_output
        self.filename = filename
        self.tqdm = None

    def __call__(self, bytes_amount: int, total_bytes: int):
        if self.tqdm is None:
            self.tqdm = tqdm(
                desc=f"Uploading {self.filename}",
                total=total_bytes,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )
        self.tqdm.update(bytes_amount)
        percentage = (self.tqdm.n / total_bytes) * 100
        self.signal_progress.emit(int(percentage))
        self.signal_output.emit(f"Uploaded {self.tqdm.n}/{total_bytes} bytes")
        if self.tqdm.n >= total_bytes:
            self.tqdm.close()


class HFUploaderThread(QThread):
    """Thread for uploading files to Hugging Face Hub."""

    signal_status = pyqtSignal(str)
    signal_progress = pyqtSignal(int)
    signal_output = pyqtSignal(str)
    signal_finished = pyqtSignal()

    def __init__(
        self,
        api_token, #added
        repo_id,
        upload_path,  #  Can be a file or a folder
        repo_type,
        repo_folder,
        current_directory,
        commit_msg,
        create_pr,
        rate_limit_delay,
        is_folder, # boolean to know it's a folder or not
    ):
        super().__init__()
        self.api_token = api_token #added
        self.repo_id = repo_id
        self.upload_path = upload_path # added
        self.repo_type = repo_type
        self.repo_folder = repo_folder
        self.current_directory = current_directory
        self.commit_msg = commit_msg
        self.create_pr = create_pr
        self.rate_limit_delay = rate_limit_delay
        self.stop_flag = False
        self.is_folder = is_folder # added
        # Signal Initializations
        self.signal_status = pyqtSignal(str)
        self.signal_output = pyqtSignal(str)

    def stop(self):
        self.stop_flag = True

    def run(self):
        try:
            # repo_url = create_repo(repo_id=self.repo_id, repo_type=self.repo_type, exist_ok=True) #removed
            #Verify correct code is running

            if self.is_folder:
                # Upload folder logic
                if not os.path.isdir(self.upload_path):
                    self.signal_output.emit(f"❌ Error: Folder '{self.upload_path}' does not exist.")
                    self.signal_finished.emit()
                    return

                self.signal_status.emit(f"Uploading folder {self.upload_path}...")
                try:
                    # Simulate a delay for rate limiting
                    time.sleep(
                        float(self.rate_limit_delay)
                    )  # Rate limit is now a float

                    # Configure the progress callback
                    progress_callback = CustomProgressCallback(
                        self.signal_progress,
                        self.signal_output,
                        os.path.basename(self.upload_path),
                    )

                    upload_folder(
                        folder_path=self.upload_path,  # The actual folder path
                        repo_id=self.repo_id,
                        repo_type=self.repo_type,
                        commit_message=self.commit_msg,
                        commit_info={"message": self.commit_msg},
                        token=self.api_token,  # Use the token here to avoid passing the HfApi instance.
                        progress_callback=progress_callback,
                        path_in_repo = self.repo_folder if self.repo_folder else "."
                    )

                    self.signal_output.emit(
                        f"Uploaded folder {self.upload_path} to {self.repo_id}/{self.repo_folder}"
                    )

                except Exception as upload_error:
                    logger.error(
                        f"Error uploading {self.upload_path}: {upload_error}", exc_info=True
                    )
                    self.signal_output.emit(
                        f"❌ Error uploading {self.upload_path}: {str(upload_error)}"
                    )

            else:
                # Upload file logic
                if not os.path.isfile(self.upload_path):
                    self.signal_output.emit(f"❌ Error: File '{self.upload_path}' does not exist.")
                    self.signal_finished.emit()
                    return

                relative_path = os.path.relpath(self.upload_path, self.current_directory)
                repo_path = (
                    os.path.join(self.repo_folder, relative_path)
                    if self.repo_folder
                    else relative_path
                )

                self.signal_status.emit(f"Uploading {self.upload_path} to {repo_path}...")

                try:
                    # Simulate a delay for rate limiting
                    time.sleep(
                        float(self.rate_limit_delay)
                    )  # Rate limit is now a float

                    # Configure the progress callback
                    progress_callback = CustomProgressCallback(
                        self.signal_progress,
                        self.signal_output,
                        os.path.basename(self.upload_path),
                    )

                    upload_file(
                        path_or_fileobj=self.upload_path,  # The actual file path
                        path_in_repo=repo_path,  # Where it goes in the repo
                        repo_id=self.repo_id,
                        repo_type=self.repo_type,
                        commit_message=self.commit_msg,
                        commit_info={"message": self.commit_msg},
                        token=self.api_token,  # Use the token here to avoid passing the HfApi instance.
                        progress_callback=progress_callback
                    )

                    self.signal_output.emit(
                        f"Uploaded {self.upload_path} to {self.repo_id}/{repo_path}"
                    )

                except Exception as upload_error:
                    logger.error(
                        f"Error uploading {self.upload_path}: {upload_error}", exc_info=True
                    )
                    self.signal_output.emit(
                        f"❌ Error uploading {self.upload_path}: {str(upload_error)}"
                    )
                    # Consider whether to stop the entire upload on an error or continue

            self.signal_status.emit("Upload completed.")
            self.signal_finished.emit()

        except Exception as e:
            logger.error(f"Upload error: {e}", exc_info=True)
            self.signal_output.emit(f"❌ Upload error: {str(e)}")
            self.signal_finished.emit()  # Ensure finished signal is always emitted.

class HuggingFaceUploader(QWidget):
    """Widget for uploading files to Hugging Face Hub."""
    class LogSignal(QObject):
        """Propagates text to window for output display."""
        sig_msg = pyqtSignal(str)
        sig_stat = pyqtSignal(str)

    LogSignal = LogSignal() # Create the instance here

    def __init__(self):
        super().__init__()

        #self.LogSignal = self.LogSignal() #REMOVE

        self.setWindowTitle("Hugging Face Uploader")
        self.uploader_thread = None
        self.config_dialog = None  # Needed for it to be instantiated
        self.api = None

        # Initialize current_directory here!
        self.current_directory = (
            ""  # Initialize with a default value (empty string) or os.getcwd()
        )

        # Widgets
        self.config_button = QPushButton("Edit Config (API Token)")

        # Repo Management Widgets
        self.repo_management_label = QLabel("Repository Management")
        self.repo_exists_button = QPushButton("Check if Repo Exists")
        self.create_repo_button = QPushButton("Create Repository")
        self.repo_status_label = QLabel("")

        self.org_label = QLabel("Owner:")
        self.org_input = QLineEdit()
        self.repo_label = QLabel("Repo:")
        self.repo_input = QLineEdit()
        self.repo_type_label = QLabel("Repo Type:")
        self.repo_type_dropdown = QComboBox()
        self.repo_type_dropdown.addItems(["model", "dataset", "space"])
        self.repo_folder_label = QLabel("Subfolder:")
        self.repo_folder_input = QLineEdit()

        self.file_type_label = QLabel("File Type:")
        self.file_type_dropdown = QComboBox()
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
            ("TAR Files", "gz"),
        ]
        for name, ext in self.file_types:
            self.file_type_dropdown.addItem(name, ext)
        self.sort_by_label = QLabel("Sort By:")
        self.sort_by_dropdown = QComboBox()
        self.sort_by_dropdown.addItems(["name", "date"])

        # Add directory selection button
        self.directory_label = QLabel(f"Current Directory: {self.current_directory}")
        self.directory_input = QLineEdit(self.current_directory)
        self.directory_select_button = QPushButton("Select Directory")  # New
        self.directory_update_button = QPushButton("Update Dir")

        # File/Folder Selection
        self.select_file_button = QPushButton("Select File")
        self.selected_file_label = QLabel("No file selected")
        self.selected_file = None

        self.folder_select_button = QPushButton("Select Folder")
        self.folder_label = QLabel("No folder selected")
        self.selected_folder = None
        self.upload_type_dropdown = QComboBox()  # Files or Folder
        self.upload_type_dropdown.addItems(["File", "Folder"])  # Corrected "Files" to "File"

        self.commit_message_label = QLabel("Commit Message:")
        self.commit_message_input = QTextEdit(
            "Upload with Earth & Dusk Huggingface 🤗 Backup"
        )
        self.create_pr_checkbox = QCheckBox("Create Pull Request")
        self.clear_after_checkbox = QCheckBox("Clear output after upload")
        self.clear_after_checkbox.setChecked(True)
        self.update_files_button = QPushButton("Update Files") #only updates filelist
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

        #Repo layout
        repo_management_layout = QVBoxLayout()
        repo_management_layout.addWidget(self.repo_management_label)
        repo_management_layout.addWidget(self.repo_exists_button)
        repo_management_layout.addWidget(self.create_repo_button)
        repo_management_layout.addWidget(self.repo_status_label)

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

        # NEW - Single File Selector Layout
        file_select_layout = QHBoxLayout()
        file_select_layout.addWidget(self.select_file_button)
        file_select_layout.addWidget(self.selected_file_label)

        # New Folder Selector
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_select_button)
        folder_layout.addWidget(self.folder_label)
        # New Upload type selector
        upload_type_layout = QHBoxLayout()
        upload_type_layout.addWidget(QLabel("Upload Type:"))
        upload_type_layout.addWidget(self.upload_type_dropdown)

        commit_layout = QVBoxLayout()
        commit_layout.addWidget(self.commit_message_label)
        commit_layout.addWidget(self.commit_message_input)

        upload_options_layout = QHBoxLayout()
        upload_options_layout.addWidget(self.create_pr_checkbox)
        upload_options_layout.addWidget(self.clear_after_checkbox)

        button_layout = QHBoxLayout()
        #button_layout.addWidget(self.update_files_button)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.cancel_upload_button)
        button_layout.addWidget(self.clear_output_button)

        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_percent_label)

        # Add a QStackedWidget to hold the file/folder selection widgets
        self.selection_stack = QStackedWidget()
        self.selection_stack.addWidget(QWidget())  # Empty widget as placeholder
        self.selection_stack.addWidget(QWidget())  # Empty widget as placeholder #changed

        main_layout = QVBoxLayout()
        main_layout.addLayout(config_layout)
        main_layout.addLayout(repo_management_layout)
        main_layout.addLayout(repo_layout)
        main_layout.addWidget(self.repo_folder_label)
        main_layout.addWidget(self.repo_folder_input)
        main_layout.addLayout(upload_type_layout)
        main_layout.addLayout(file_select_layout) #new
        main_layout.addLayout(directory_layout)
        main_layout.addLayout(folder_layout)
        #main_layout.addWidget(self.selection_stack)
        main_layout.addLayout(commit_layout)
        main_layout.addLayout(upload_options_layout)
        main_layout.addWidget(self.update_files_button)
        main_layout.addWidget(self.file_list)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(progress_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.output_text)
        #self.LogSignal = self.LogSignal() #REMOVED
        self.LogSignal.sig_msg.connect(self.append_output)
        self.LogSignal.sig_stat.connect(self.update_status)
        self.setLayout(main_layout)

        # Connections
        self.config_button.clicked.connect(self.edit_config)
        self.repo_exists_button.clicked.connect(self.check_repo_exists)
        self.create_repo_button.clicked.connect(self.create_repo)
        self.directory_select_button.clicked.connect(
            self.select_directory
        )  # Add connection for new button
        self.directory_update_button.clicked.connect(self.update_directory)
        self.update_files_button.clicked.connect(self.update_files)
        self.upload_button.clicked.connect(self.start_upload)
        self.cancel_upload_button.clicked.connect(self.cancel_upload)
        self.file_type_dropdown.currentIndexChanged.connect(self.update_files)

        # new
        self.select_file_button.clicked.connect(self.select_file)
        self.folder_select_button.clicked.connect(self.select_folder)
        self.upload_type_dropdown.currentIndexChanged.connect(self.update_ui_for_upload_type)
        self.update_ui_for_upload_type() # Initial UI update

    def edit_config(self):
        """Opens the configuration dialog."""
        self.config_dialog = ConfigDialog()  # Initialized here
        self.config_dialog.show()

    def check_repo_exists(self):
         """Checks if the repository exists on Hugging Face Hub."""
         org = self.org_input.text()
         repo = self.repo_input.text()
         repo_type = self.repo_type_dropdown.currentText()

         if not org or not repo:
              QMessageBox.critical(self, "Error", "Please fill in both Organization/Username and Repository name")
              return

         repo_id = f"{org}/{repo}"

         try:
              # Deobfuscate API token
              obfuscated_token = config["HuggingFace"]["api_token"]
              api_token = deobfuscate_token(obfuscated_token)

              # Initialize Hugging Face API
              self.api = HfApi(token=api_token)

              self.api.get_repo_info(repo_id=repo_id, repo_type=repo_type)
              self.repo_status_label.setText(f"✅ Repository '{repo_id}' exists.")
              self.output_text.append(f"✅ Repository '{repo_id}' exists.")

         except HTTPError as e:
              if e.response.status_code == 404:
                   self.repo_status_label.setText(f"❌ Repository '{repo_id}' does not exist.")
                   self.output_text.append(f"❌ Repository '{repo_id}' does not exist.")
              else:
                   self.repo_status_label.setText(f"❌ Error checking repository: {e}")
                   self.output_text.append(f"❌ Error checking repository: {e}")
         except Exception as e:
              self.repo_status_label.setText(f"❌ Error checking repository: {e}")
              self.output_text.append(f"❌ Error checking repository: {e}")

    def create_repo(self):
        """Creates a new repository on Hugging Face Hub."""
        org = self.org_input.text()
        repo = self.repo_input.text()
        repo_type = self.repo_type_dropdown.currentText()

        if not org or not repo:
            QMessageBox.critical(self, "Error", "Please fill in both Organization/Username and Repository name")
            return

        repo_id = f"{org}/{repo}"

        try:
            # Deobfuscate API token
            obfuscated_token = config["HuggingFace"]["api_token"]
            api_token = deobfuscate_token(obfuscated_token)

            # Initialize Hugging Face API
            self.api = HfApi(token=api_token)

            create_repo(repo_id=repo_id, repo_type=repo_type, token=api_token, exist_ok=True) #added exist_ok parameter
            self.repo_status_label.setText(f("✅ Repository '{repo_id}' created successfully (or already existed)."))
            self.output_text.append(f"✅ Repository '{repo_id}' created successfully (or already existed).")

        except Exception as e:
            self.repo_status_label.setText(f"❌ Error creating repository: {e}")
            self.output_text.append(f"❌ Error creating repository: {e}")

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
        #if self.upload_type_dropdown.currentText() == "Files": # Only update file list if in file upload mode
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

    def select_file(self):
        """Opens a dialog to select a single file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a File")
        if file_path:
            self.selected_file = file_path
            self.selected_file_label.setText(f"Selected File: {os.path.basename(file_path)}")

    def select_folder(self):
        """Opens a dialog to select a folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select a Folder")
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(f"Selected Folder: {os.path.basename(folder)}")

    def update_ui_for_upload_type(self):
        """Updates the UI based on the selected upload type (File or Folder)."""
        upload_type = self.upload_type_dropdown.currentText()

        if upload_type == "File":
            self.select_file_button.show()
            self.selected_file_label.show()

            self.folder_select_button.hide()
            self.folder_label.hide()
            self.update_files_button.show()
            self.file_type_label.show()
            self.file_type_dropdown.show()
            self.file_list.show()

        elif upload_type == "Folder":
            self.select_file_button.hide()
            self.selected_file_label.hide()

            self.folder_select_button.show()
            self.folder_label.show()
            self.update_files_button.hide()
            self.file_type_label.hide()
            self.file_type_dropdown.hide()
            self.file_list.hide()


    def start_upload(self):
        """Starts the upload process in a separate thread."""
        org = self.org_input.text()
        repo = self.repo_input.text()

        if not org or not repo:
            QMessageBox.critical(self, "Error", "Please fill in both Organization/Username and Repository name")
            return

        repo_id = f"{org}/{repo}"
        repo_type = self.repo_type_dropdown.currentText()
        repo_folder = self.repo_folder_input.text().strip()
        current_directory = self.directory_input.text()
        commit_msg = self.commit_message_input.toPlainText()

        try:
            rate_limit_delay = config["HuggingFace"]["rate_limit_delay"]  # Pull from config
            obfuscated_token = config["HuggingFace"][
                "api_token"
            ]  # Obfuscated token from config

            #Deobfuscate:
            api_token = deobfuscate_token(obfuscated_token)

            # Initialize Hugging Face API (Moved here)
            self.api = HfApi(token=api_token)

            self.upload_button.setEnabled(False)
            self.cancel_upload_button.setEnabled(True)  # Enable cancel button
            # Determine upload path and type
            upload_type = self.upload_type_dropdown.currentText()

            if upload_type == "File":
                upload_path = self.selected_file
                is_folder = False
                if not upload_path:
                    QMessageBox.critical(self, "Error", "Please select a file to upload.")
                    self.upload_finished()
                    return

                if not os.path.isfile(upload_path):
                    QMessageBox.critical(self, "Error", f"The selected file '{upload_path}' does not exist.")
                    self.upload_finished()
                    return

            elif upload_type == "Folder":
                upload_path = self.selected_folder
                is_folder = True
                if not upload_path:
                    QMessageBox.critical(self, "Error", "Please select a folder to upload.")
                    self.upload_finished()
                    return
                if not os.path.isdir(upload_path):
                    QMessageBox.critical(self, "Error", f"The selected folder '{upload_path}' does not exist.")
                    self.upload_finished()
                    return

            else:
                QMessageBox.critical(self, "Error", "Invalid upload type selected.")
                self.upload_finished()
                return

            # Create and start the upload thread
            self.uploader_thread = HFUploaderThread(
                api_token,
                repo_id,
                upload_path, #file or folder
                repo_type,
                repo_folder,
                current_directory,
                commit_msg,
                False,
                rate_limit_delay,
                is_folder
            )  # Removed create_pr_checkbox
            self.uploader_thread.signal_status.connect(self.update_status)
            self.uploader_thread.signal_progress.connect(self.update_progress)
            self.uploader_thread.signal_output.connect(self.update_output)
            self.uploader_thread.signal_finished.connect(self.upload_finished)
            self.uploader_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error starting upload: {e}")
            logger.exception("Error in start_upload")
            self.upload_finished()  # Clean up the UI

# Add the new functions that are called from the update functions to update the information to the output and status screens
    def update_status(self, message):
        """Updates the status label."""
        self.progress_label.setText(message)
        self.LogSignal.sig_stat.emit(message)
    def update_output(self, message):
        """Appends a message to the output text."""
        self.output_text.append(message)
        self.LogSignal.sig_msg.emit(message)
    def cancel_upload(self):
        """Cancels the upload process."""
        if self.uploader_thread and self.uploader_thread.isRunning():
            self.uploader_thread.stop()
            self.uploader_thread.wait()
            self.upload_finished()

    def update_progress(self, value):
        """Updates the progress bar."""
        self.progress_bar.setValue(value)
        self.progress_percent_label.setText(f"{value}%")

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
    def append_output(self, message):
        """Appends a message to the output text."""
        self.output_text.append(message)
if __name__ == "__main__":
    app = QApplication([])
    window = HuggingFaceUploader()
    window.show()
    app.exec()