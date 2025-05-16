import logging
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
    QGridLayout,
    QFileDialog,
    QTextEdit,
    QCheckBox,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import QTimer
from upload_worker import UploadWorker
from config_manager import config, get_api_token, save_config, get_max_concurrent_upload_jobs
from config_dialog import ConfigDialog
from huggingface_hub import HfApi, HfHubHTTPError, RepositoryNotFoundError, RevisionNotFoundError
from urllib.parse import urlparse
import requests

logger = logging.getLogger(__name__)

# Import the helper functions from git_lfs_utils.py
from git_lfs_utils import init_git_lfs, track_files, add_gitattributes

class HuggingFaceUploader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hugging Face Uploader")
        self.current_directory = os.getcwd()
        self.config_dialog = None

        self.active_workers = []
        self.upload_queue = []
        self.worker_file_map = (
            {}
        )  # Maps worker object to its file_path for context
        self.total_files_to_upload = 0
        self.files_processed_count = 0
        self.files_succeeded_count = 0
        self.max_concurrent_jobs = 1
        self.repo_id_for_upload = ""
        self.repo_type_for_upload = ""
        self.repo_folder_for_upload = ""
        self.commit_msg_for_upload = ""
        self.create_pr_for_upload = False
        self.api_token_for_upload = ""
        self._is_upload_active = False  # Flag to manage overall upload state
        self._cancel_requested = False

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self) # Pass self to the layout
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        header_config = QLabel("Configuration")
        header_config.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_config)
        config_layout = QHBoxLayout()
        self.edit_config_button = QPushButton("Edit HF API Token & Settings")
        config_layout.addWidget(self.edit_config_button)
        main_layout.addLayout(config_layout)

        header_repo = QLabel("Repository Information")
        header_repo.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_repo)
        repo_layout = QGridLayout()
        self.org_label = QLabel("Owner (User/Org):")
        self.org_input = QLineEdit(config.get("HuggingFace", "org", fallback=""))
        self.repo_label = QLabel("Repository Name:")
        self.repo_input = QLineEdit(config.get("HuggingFace", "repo", fallback=""))
        self.repo_type_label = QLabel("Repo Type:")
        self.repo_type_dropdown = QComboBox()
        self.repo_type_dropdown.addItems(["model", "dataset", "space"])
        self.repo_folder_label = QLabel("Path in Repo (Optional):")
        self.repo_folder_input = QLineEdit()

        repo_layout.addWidget(self.org_label, 0, 0)
        repo_layout.addWidget(self.org_input, 0, 1)
        repo_layout.addWidget(self.repo_label, 0, 2)
        repo_layout.addWidget(self.repo_input, 0, 3)
        repo_layout.addWidget(self.repo_type_label, 1, 0)
        repo_layout.addWidget(self.repo_type_dropdown, 1, 1)
        repo_layout.addWidget(self.repo_folder_label, 1, 2)
        repo_layout.addWidget(self.repo_folder_input, 1, 3)

        repo_layout.setColumnStretch(1, 1)  # Make owner/org take space
        repo_layout.setColumnStretch(3, 1)  # Make repo name take space
        main_layout.addLayout(repo_layout)

        header_dir = QLabel("Directory Selection")
        header_dir.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_dir)
        dir_layout = QHBoxLayout()
        self.directory_label = QLabel(f"Current Directory: {self.current_directory}")
        self.directory_label.setWordWrap(True)
        self.directory_input = QLineEdit(self.current_directory)
        self.directory_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Make the input take up more space
        self.select_dir_button = QPushButton("Select Directory")
        self.update_dir_button = QPushButton("Set Directory from Input")
        dir_layout.addWidget(self.directory_label)
        dir_layout.addWidget(self.directory_input)
        dir_layout.addWidget(self.select_dir_button)
        dir_layout.addWidget(self.update_dir_button)
        main_layout.addLayout(dir_layout)

        header_files = QLabel("File Settings")
        header_files.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_files)
        file_type_layout = QHBoxLayout()
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
            ("TAR Files", "tar"),
            ("GZ Archives", "gz"),
            ("All Files", "*"),
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

        header_commit = QLabel("Commit Message")
        header_commit.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_commit)
        commit_layout = QVBoxLayout()
        self.commit_message_label = QLabel("Commit Message:")
        self.commit_message_input = QTextEdit("Upload with Earth & Dusk Huggingface 🤗 Backup")
        self.commit_message_input.setFixedHeight(60)
        commit_layout.addWidget(self.commit_message_label)
        commit_layout.addWidget(self.commit_message_input)
        main_layout.addLayout(commit_layout)

        header_options = QLabel("Options")
        header_options.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_options)
        options_layout = QHBoxLayout()
        self.create_pr_checkbox = QCheckBox("Create Pull Request")
        self.check_repo_exists_checkbox = QCheckBox(
            "Check if Repo Exists Before Upload"
        )
        self.create_repo_checkbox = QCheckBox(
            "Create Repo if it doesn't exist (requires token with write access)"
        )
        self.create_repo_checkbox.setEnabled(False)
        self.clear_after_checkbox = QCheckBox("Clear output after upload")
        self.clear_after_checkbox.setChecked(True)
        self.use_lfs_checkbox = QCheckBox("Use Git LFS")  # ADD THE CHECKBOX
        options_layout.addWidget(self.create_pr_checkbox)
        options_layout.addWidget(self.check_repo_exists_checkbox)
        options_layout.addWidget(self.create_repo_checkbox)
        options_layout.addWidget(self.clear_after_checkbox)
        options_layout.addWidget(self.use_lfs_checkbox) # Add the check box here

        main_layout.addLayout(options_layout)

        header_files_list = QLabel("Files to Upload (Select files from the list)")
        header_files_list.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_files_list)
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list.setMinimumHeight(150)
        main_layout.addWidget(self.file_list)

        header_output = QLabel("Output & Progress")
        header_output.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_output)
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(50)  # Minimum height for output
        self.output_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Make the output text expand.
        self.progress_bar = QProgressBar()
        progress_status_layout = QHBoxLayout()
        self.progress_label = QLabel("Status: Ready")
        self.progress_percent_label = QLabel("0%")
        progress_status_layout.addWidget(self.progress_label)
        progress_status_layout.addStretch()
        progress_status_layout.addWidget(self.progress_percent_label)
        output_layout.addWidget(self.output_text)
        output_layout.addWidget(self.progress_bar)
        output_layout.addLayout(progress_status_layout)
        main_layout.addLayout(output_layout)
        # Set Stretch Factors for Vertical Space
        # main_layout.setStretchFactor(self.file_list, 2)
        main_layout.setStretchFactor(self.output_text, 1)

        self.edit_config_button.clicked.connect(self.edit_config)
        self.select_dir_button.clicked.connect(self.select_directory)
        self.update_dir_button.clicked.connect(self.update_directory_from_input)
        self.update_files_button.clicked.connect(self.update_files)
        self.upload_button.clicked.connect(self.start_upload)
        self.cancel_button.clicked.connect(self.cancel_upload)
        self.clear_output_button.clicked.connect(self.clear_output)
        self.check_repo_exists_checkbox.stateChanged.connect(self.toggle_create_repo_checkbox)
        self.file_type_dropdown.currentIndexChanged.connect(self.update_files)
        self.sort_by_dropdown.currentIndexChanged.connect(self.update_files)
        self.org_input.editingFinished.connect(self.save_repo_details_to_config)
        self.repo_input.editingFinished.connect(self.save_repo_details_to_config)
        self.use_lfs_checkbox.stateChanged.connect(self.update_files)  # Connect the checkbox.

        self.update_files()

    def save_repo_details_to_config(self):
        config.set("HuggingFace", "org", self.org_input.text())
        config.set("HuggingFace", "repo", self.repo_input.text())
        try:
            save_config()
        except Exception as e:
            logger.error(f"Error saving repo details to config: {e}")
            self.output_text.append(f"⚠️ Could not save repo details to config: {e}")

    def edit_config(self):
        if not self.config_dialog:
            self.config_dialog = ConfigDialog()
        self.config_dialog.load_config_values()
        self.config_dialog.show()

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select a Directory", self.current_directory
        )
        if directory:
            self.directory_input.setText(directory)
            self.current_directory = directory
            self.directory_label.setText(f"Current Directory: {self.current_directory}")
            self.update_files()

    def update_directory_from_input(self):
        new_dir = self.directory_input.text()
        if os.path.isdir(new_dir):
            self.current_directory = os.path.abspath(new_dir)
            self.directory_input.setText(self.current_directory)
            self.directory_label.setText(f"Current Directory: {self.current_directory}")
            self.update_files()
        else:
            self.output_text.append(f"❌ Invalid Directory: {new_dir}")
            QMessageBox.warning(
                self, "Invalid Directory", f"The specified directory does not exist: {new_dir}"
            )

    def toggle_create_repo_checkbox(self, state):
        self.create_repo_checkbox.setEnabled(state != 0)
        if state == 0:
            self.create_repo_checkbox.setChecked(False)

    def update_files(self):
        self.file_list.clear()
        file_extension_data = self.file_type_dropdown.currentData()
        search_pattern = f"*.{file_extension_data}" if file_extension_data != "*" else "*"

        if not os.path.isdir(self.current_directory):
            self.output_text.append(f"❌ Current directory is invalid: {self.current_directory}")
            return
        try:
            if self.use_lfs_checkbox.isChecked():
                # Initialize Git LFS (only if not already)
                if not init_git_lfs(self.current_directory):
                    self.output_text.append("❌ Failed to initialize Git LFS.")
                else:
                    # Determine LFS track patterns based on file type selection
                    file_patterns_to_track = [search_pattern]
                    if not track_files(self.current_directory, file_patterns_to_track):
                        self.output_text.append("❌ Failed to track files with Git LFS.")
                    elif not add_gitattributes(self.current_directory):
                         self.output_text.append("❌ Failed to stage .gitattributes.")
            all_files_in_dir = glob.glob(os.path.join(self.current_directory, search_pattern))

            filtered_files = []
            for file_path in all_files_in_dir:
                if os.path.islink(file_path):
                    self.output_text.append(f"ℹ️ Skipping symlink: {os.path.basename(file_path)}")
                    continue
                if not os.path.isfile(file_path):
                    continue
                filtered_files.append(file_path)

            sort_key = os.path.getmtime if self.sort_by_dropdown.currentText() == "date" else lambda x: os.path.basename(x).lower()
            reverse_sort = self.sort_by_dropdown.currentText() == "date"

            sorted_files = sorted(filtered_files, key=sort_key, reverse=reverse_sort)

            base_names = [os.path.basename(f) for f in sorted_files]
            self.file_list.addItems(base_names)
            self.output_text.append(f"✨ Found {len(sorted_files)} files matching '{search_pattern}' in {self.current_directory}")
        except Exception as e:
            logger.error(f"File listing error: {e}\n{traceback.format_exc()}")
            self.output_text.append(f"❌ Error listing files: {str(e)}")

    def start_upload(self):
        if self._is_upload_active:
            QMessageBox.warning(self, "Upload In Progress", "An upload operation is already in progress.")
            return

        org_name = self.org_input.text().strip()
        repo_name = self.repo_input.text().strip()

        if not org_name or not repo_name:
            QMessageBox.warning(self, "Missing Info", "Please fill in both Owner (User/Org) and Repository Name.")
            self.output_text.append("❗ Owner and Repository Name are required.")
            return

        self.repo_id_for_upload = f"{org_name}/{repo_name}"

        selected_list_items = self.file_list.selectedItems()
        if not selected_list_items:
            QMessageBox.warning(self, "No Files Selected", "Please select files from the list to upload.")
            self.output_text.append("📝 Nothing selected for upload.")
            return

        selected_file_basenames = [item.text() for item in selected_list_items]
        self.upload_queue = [os.path.join(self.current_directory, basename) for basename in selected_file_basenames]
        self.total_files_to_upload = len(self.upload_queue)
        self.files_processed_count = 0
        self.files_succeeded_count = 0
        self._is_upload_active = True
        self._cancel_requested = False

        self.repo_type_for_upload = self.repo_type_dropdown.currentText()
        self.repo_folder_for_upload = self.repo_folder_input.text().strip('/')
        self.commit_msg_for_upload = self.commit_message_input.toPlainText()
        self.create_pr_for_upload = self.create_pr_checkbox.isChecked()

        self.api_token_for_upload = get_api_token()
        if not self.api_token_for_upload:
            self.output_text.append("❌ API token not configured. Please set it via Edit Config.")
            QMessageBox.critical(self, "API Token Missing", "API token is not configured.")
            self._is_upload_active = False
            return

        try:
            self.max_concurrent_jobs = int(get_max_concurrent_upload_jobs())
            if self.max_concurrent_jobs <= 0:
                self.max_concurrent_jobs = 1
        except ValueError:
            self.max_concurrent_jobs = 1
            self.output_text.append("⚠️ Invalid max concurrent upload jobs in config, defaulting to 1.")

        if self.check_repo_exists_checkbox.isChecked():
            exists = self.repo_exists_on_hub(self.repo_id_for_upload, self.repo_type_for_upload)
            if not exists:
                if self.create_repo_checkbox.isChecked():
                    self.output_text.append(f"ℹ️ Repository {self.repo_id_for_upload} not found. Attempting to create it...")
                    if not self.create_repo_on_hub(self.repo_id_for_upload, self.repo_type_for_upload):
                        self.output_text.append(f"❌ Failed to create repository {self.repo_id_for_upload}. Aborting upload.")
                        QMessageBox.critical(self, "Repo Creation Failed", f"Could not create repository {self.repo_id_for_upload}.")
                        self._is_upload_active = False
                        return
                    self.output_text.append(f"✅ Repository {self.repo_id_for_upload} created successfully.")
                else:
                    self.output_text.append(f"❗ Repository {self.repo_id_for_upload} does not exist and creation is not enabled. Aborting.")
                    QMessageBox.warning(self, "Repo Not Found", f"Repository {self.repo_id_for_upload} does not exist and 'Create Repo' is not checked.")
                    self._is_upload_active = False
                    return

        self.upload_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_percent_label.setText("0%")
        self.progress_label.setText("Status: Starting uploads...")

        use_lfs = self.use_lfs_checkbox.isChecked() # Get the LFS status
        self._launch_next_workers(use_lfs=use_lfs) # PASS THE LFS

    def _launch_next_workers(self, use_lfs: bool): # include use_lfs
        if self._cancel_requested:
            return

        while len(self.active_workers) < self.max_concurrent_jobs and self.upload_queue:
            file_to_upload = self.upload_queue.pop(0)

            worker = UploadWorker(
                api_token=self.api_token_for_upload,
                repo_owner=self.repo_id_for_upload.split('/')[0],
                repo_name=self.repo_id_for_upload.split('/')[1],
                file_path=file_to_upload,
                commit_message=self.commit_msg_for_upload,
                repo_type=self.repo_type_for_upload,
                repo_folder=self.repo_folder_for_upload,
                upload_type="File",
                create_repo=False,
                repo_exists=True,
                use_lfs=use_lfs,   # PASS IT HERE.
            )
            worker.output_signal.connect(self._handle_worker_output)
            worker.finished_signal.connect(lambda success, worker_instance=worker, fp=file_to_upload: self._handle_worker_finished(worker_instance, fp, success))

            self.active_workers.append(worker)
            self.worker_file_map[worker] = file_to_upload
            worker.start()
            self.output_text.append(f"⏳ Worker started for: {os.path.basename(file_to_upload)}")

        if not self.active_workers and not self.upload_queue and self._is_upload_active:
            self._finalize_upload_process()

    def _handle_worker_output(self, message):
        self.output_text.append(message)

    def _handle_worker_finished(self, worker, file_path, success):
        self.files_processed_count += 1
        if success:
            self.files_succeeded_count += 1

        if worker in self.active_workers:
            self.active_workers.remove(worker)
        if worker in self.worker_file_map:
            del self.worker_file_map[worker]

        self._update_overall_progress()

        if self._cancel_requested:
            if not self.active_workers:
                self._finalize_upload_process()
            return

        if self.upload_queue or self.active_workers:
            self._launch_next_workers()
        else:  # No more files in queue and no active workers
            self._finalize_upload_process()

    def _update_overall_progress(self):
        if self.total_files_to_upload > 0:
            progress_percent = int((self.files_processed_count / self.total_files_to_upload) * 100)
            self.progress_bar.setValue(progress_percent)
            self.progress_percent_label.setText(f"{progress_percent}%")
            self.progress_label.setText(f"Status: Processed {self.files_processed_count}/{self.total_files_to_upload}. Active: {len(self.active_workers)}")
        else:
            self.progress_bar.setValue(0)
            self.progress_percent_label.setText("0%")

    def _finalize_upload_process(self):
        self._is_upload_active = False
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        final_message = ""
        if self._cancel_requested:
            final_message = f"🛑 Upload cancelled. {self.files_succeeded_count}/{self.total_files_to_upload} files uploaded."
            self.output_text.append(final_message)
        elif self.files_succeeded_count == self.total_files_to_upload and self.total_files_to_upload > 0:
            final_message = f"🎉 All {self.total_files_to_upload} files uploaded successfully to {self.repo_id_for_upload}."
            self.progress_bar.setValue(100)
            self.progress_percent_label.setText("100%")
            self.output_text.append(final_message)
        elif self.total_files_to_upload > 0:
            final_message = f"⚠️ Upload complete with errors. {self.files_succeeded_count}/{self.total_files_to_upload} files uploaded to {self.repo_id_for_upload}."
            self.output_text.append(final_message)
        else:  # No files were selected or processed
            final_message = "No files processed."
            self.output_text.append(final_message)

        self.progress_label.setText(f"Status: {final_message}")
        logger.info(f"Upload task to {self.repo_id_for_upload} finished. Succeeded: {self.files_succeeded_count}/{self.total_files_to_upload}. Cancelled: {self._cancel_requested}")

        if self.clear_after_checkbox.isChecked() and self.files_succeeded_count == self.total_files_to_upload and not self._cancel_requested:
             QTimer.singleShot(2000, self.clear_output)

    def cancel_upload(self):
        if not self._is_upload_active:
            self.output_text.append("ℹ️ No active upload to cancel.")
            return

        self.output_text.append("🔄 Requesting cancellation of uploads...")
        self._cancel_requested = True

        # Terminate active QThreads. UploadWorker does not have a graceful stop.
        for worker in list(self.active_workers):  # Iterate over a copy
            if worker.isRunning():
                worker.terminate()  # Forcible stop
                # worker.wait() # Optionally wait, but terminate is usually immediate
                self.output_text.append(f"🛑 Worker for {os.path.basename(self.worker_file_map.get(worker, 'unknown file'))} termination signal sent.")

        self.active_workers.clear()
        self.upload_queue.clear()

        # If no workers were active or they terminated quickly, finalize.
        # Otherwise, _handle_worker_finished will eventually call _finalize_upload_process.
        if not self.active_workers:
             QTimer.singleShot(100, self._finalize_upload_process) # Use a short delay to allow UI to update

        self.cancel_button.setEnabled(False) # Disable cancel button once pressed

    def clear_output(self):
        self.output_text.clear()
        self.progress_bar.setValue(0)
        self.progress_label.setText("Status: Ready")
        self.progress_percent_label.setText("0%")