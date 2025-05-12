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
    QProgressBar,
    QScrollArea,
    QSizePolicy,
)
from hf_uploader_thread import HFUploaderThread
from config_manager import config, get_api_token, save_config
from config_dialog import ConfigDialog

logger = logging.getLogger(__name__)

class HuggingFaceUploader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hugging Face Uploader")
        self.current_directory = os.getcwd()
        self.uploader_thread = None
        self.config_dialog = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
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
        
        repo_layout.setColumnStretch(1, 1)
        repo_layout.setColumnStretch(3, 1)
        main_layout.addLayout(repo_layout)

        header_dir = QLabel("Directory Selection")
        header_dir.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_dir)
        dir_layout = QHBoxLayout()
        self.directory_label = QLabel(f"Current Directory: {self.current_directory}")
        self.directory_label.setWordWrap(True)
        self.directory_input = QLineEdit(self.current_directory)
        self.select_dir_button = QPushButton("Select Directory")
        self.update_dir_button = QPushButton("Set Directory from Input")
        dir_layout.addWidget(self.directory_label)
        dir_layout.addWidget(self.directory_input, 1)
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
            ("SafeTensors", "safetensors"), ("PyTorch Models", "pt"),
            ("PyTorch Legacy", "pth"), ("ONNX Models", "onnx"),
            ("TensorFlow Models", "pb"), ("Keras Models", "h5"),
            ("Checkpoints", "ckpt"), ("Binary Files", "bin"),
            ("JSON Files", "json"), ("YAML Files", "yaml"),
            ("YAML Alt", "yml"), ("Text Files", "txt"),
            ("CSV Files", "csv"), ("Pickle Files", "pkl"),
            ("PNG Images", "png"), ("JPEG Images", "jpg"),
            ("JPEG Alt", "jpeg"), ("WebP Images", "webp"),
            ("GIF Images", "gif"), ("ZIP Archives", "zip"),
            ("TAR Files", "tar"), ("GZ Archives", "gz"),
            ("All Files", "*")
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
        self.check_repo_exists_checkbox = QCheckBox("Check if Repo Exists Before Upload")
        self.create_repo_checkbox = QCheckBox("Create Repo if it doesn't exist (requires token with write access)")
        self.create_repo_checkbox.setEnabled(False)
        self.clear_after_checkbox = QCheckBox("Clear output after upload")
        self.clear_after_checkbox.setChecked(True)
        options_layout.addWidget(self.create_pr_checkbox)
        options_layout.addWidget(self.check_repo_exists_checkbox)
        options_layout.addWidget(self.create_repo_checkbox)
        options_layout.addWidget(self.clear_after_checkbox)
        main_layout.addLayout(options_layout)

        header_files_list = QLabel("Files to Upload (Select files from the list)")
        header_files_list.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_files_list)
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list.setMinimumHeight(150)
        main_layout.addWidget(self.file_list, 1)

        header_output = QLabel("Output & Progress")
        header_output.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_output)
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFixedHeight(100)
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

        button_layout = QHBoxLayout()
        self.update_files_button = QPushButton("Refresh File List")
        self.upload_button = QPushButton("Upload Selected Files")
        self.cancel_button = QPushButton("Cancel Upload")
        self.cancel_button.setEnabled(False)
        self.clear_output_button = QPushButton("Clear Output Log")
        button_layout.addWidget(self.update_files_button)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.clear_output_button)
        main_layout.addLayout(button_layout)

        scroll_content_widget = QWidget()
        scroll_content_widget.setLayout(main_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content_widget)
        
        scroll_content_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)


        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0,0,0,0)
        page_layout.addWidget(scroll_area)
        self.setLayout(page_layout)

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
        directory = QFileDialog.getExistingDirectory(self, "Select a Directory", self.current_directory)
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
            QMessageBox.warning(self, "Invalid Directory", f"The specified directory does not exist: {new_dir}")


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
        org_name = self.org_input.text().strip()
        repo_name = self.repo_input.text().strip()

        if not org_name or not repo_name:
            QMessageBox.warning(self, "Missing Info", "Please fill in both Owner (User/Org) and Repository Name.")
            self.output_text.append("❗ Owner and Repository Name are required.")
            return

        repo_id = f"{org_name}/{repo_name}"
        
        selected_list_items = self.file_list.selectedItems()
        if not selected_list_items:
            QMessageBox.warning(self, "No Files Selected", "Please select files from the list to upload.")
            self.output_text.append("📝 Nothing selected for upload.")
            return

        selected_file_basenames = [item.text() for item in selected_list_items]
        selected_full_paths = [os.path.join(self.current_directory, basename) for basename in selected_file_basenames]

        repo_type = self.repo_type_dropdown.currentText()
        repo_folder = self.repo_folder_input.text().strip('/')
        commit_msg = self.commit_message_input.toPlainText()
        
        try:
            rate_limit_delay = float(config.get("HuggingFace", "rate_limit_delay", fallback="1.0"))
        except ValueError:
            rate_limit_delay = 1.0
            self.output_text.append("⚠️ Invalid rate limit delay in config, defaulting to 1.0s.")

        if self.check_repo_exists_checkbox.isChecked():
            exists = self.repo_exists_on_hub(repo_id, repo_type)
            if not exists:
                if self.create_repo_checkbox.isChecked():
                    self.output_text.append(f"ℹ️ Repository {repo_id} not found. Attempting to create it...")
                    if not self.create_repo_on_hub(repo_id, repo_type):
                        self.output_text.append(f"❌ Failed to create repository {repo_id}. Aborting upload.")
                        QMessageBox.critical(self, "Repo Creation Failed", f"Could not create repository {repo_id}.")
                        return
                    self.output_text.append(f"✅ Repository {repo_id} created successfully.")
                else:
                    self.output_text.append(f"❗ Repository {repo_id} does not exist and creation is not enabled. Aborting.")
                    QMessageBox.warning(self, "Repo Not Found", f"Repository {repo_id} does not exist and 'Create Repo' is not checked.")
                    return
        
        self.upload_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_percent_label.setText("0%")

        self.uploader_thread = HFUploaderThread(
            repo_id=repo_id,
            selected_files=selected_full_paths,
            repo_type=repo_type,
            repo_folder=repo_folder,
            current_directory=self.current_directory,
            commit_msg=commit_msg,
            create_pr=self.create_pr_checkbox.isChecked(),
            rate_limit_delay=rate_limit_delay,
            task_id=repo_id
        )
        self.uploader_thread.signal_status.connect(self.update_status)
        self.uploader_thread.signal_progress.connect(self.update_progress)
        self.uploader_thread.signal_output.connect(self.update_output)
        self.uploader_thread.signal_finished.connect(self.upload_finished)
        self.uploader_thread.start()
        self.output_text.append(f"🚀 Starting upload of {len(selected_full_paths)} files to {repo_id}...")

    def cancel_upload(self):
        if self.uploader_thread and self.uploader_thread.isRunning():
            self.output_text.append("🔄 Attempting to forcibly terminate upload...")
            self.uploader_thread.terminate()
            self.output_text.append("🛑 Upload termination signal sent.")
        else:
            self.output_text.append("ℹ️ No active upload to cancel.")
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)


    def update_status(self, task_id, message):
        self.progress_label.setText(f"Status: {message}")

    def update_progress(self, task_id, value):
        self.progress_bar.setValue(value)
        self.progress_percent_label.setText(f"{value}%")

    def update_output(self, task_id, message):
        self.output_text.append(message)

    def upload_finished(self, task_id, success, final_message):
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_label.setText(f"Status: {final_message}")
        if success:
            self.progress_bar.setValue(100)
            self.progress_percent_label.setText("100%")
        if self.clear_after_checkbox.isChecked() and success:
            self.output_text.append("Clearing log as per setting...")
        logger.info(f"Upload task {task_id} finished. Success: {success}. Message: {final_message}")


    def clear_output(self):
        self.output_text.clear()
        self.progress_bar.setValue(0)
        self.progress_label.setText("Status: Ready")
        self.progress_percent_label.setText("0%")

    def repo_exists_on_hub(self, repo_id, repo_type):
        api_token = get_api_token() # This now returns a clear token
        if not api_token:
            self.output_text.append("❌ API token not configured. Cannot check repository status.")
            QMessageBox.warning(self, "API Token Missing", "API token is not configured. Please set it in the configuration.")
            return False

        try:
            from huggingface_hub import HfApi
            hf_api = HfApi(token=api_token)
            hf_api.repo_info(repo_id=repo_id, repo_type=repo_type)
            self.output_text.append(f"✅ Repository {repo_id} exists.")
            return True
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                self.output_text.append(f"ℹ️ Repository {repo_id} does not exist or is private.")
                return False
            else:
                self.output_text.append(f"⚠️ Error checking repository {repo_id}: {str(e)}")
                logger.error(f"Error checking repo {repo_id}: {e}", exc_info=True)
                return False

    def create_repo_on_hub(self, repo_id, repo_type):
        api_token = get_api_token()
        if not api_token:
            self.output_text.append("❌ API token not configured. Cannot create repository.")
            QMessageBox.warning(self, "API Token Missing", "API token is not configured. Please set it in the configuration.")
            return False
            
        try:
            from huggingface_hub import create_repo
            
            create_repo(repo_id, token=api_token, repo_type=repo_type, exist_ok=True)
            self.output_text.append(f"✅ Successfully created or confirmed repository: {repo_id}")
            return True
        except Exception as e:
            self.output_text.append(f"❌ Failed to create repository {repo_id}: {str(e)}")
            logger.error(f"Error creating repo {repo_id}: {e}", exc_info=True)
            return False

    def closeEvent(self, event):
        if self.uploader_thread and self.uploader_thread.isRunning():
            reply = QMessageBox.question(self, 'Confirm Exit',
                                         "An upload is in progress. Are you sure you want to exit? This will cancel the upload.",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.cancel_upload()
                self.uploader_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            if self.config_dialog:
                self.config_dialog.close()
            event.accept()
