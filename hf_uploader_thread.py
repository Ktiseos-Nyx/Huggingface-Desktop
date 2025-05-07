import glob
import logging
import os
import time
import traceback
from pathlib import Path

# from config_dialog import ConfigDialog  # Not needed here - but good for ref.
# hf_uploader_thread.py
# import huggingface_hub
# from huggingface_hub.utils import get_hf_home_dir # OLD
from huggingface_hub import (  # Import the library
    HfApi,
    upload_folder,
)
from PyQt6.QtCore import QThread, pyqtSignal  # Import QThread and pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)  # Import QApplication

logger = logging.getLogger(__name__)


def format_size(size):
    """Formats the file size into a human-readable string."""
    for unit in ["bytes", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.2f} {unit}"


class HFUploaderThread(QThread):
    """Thread for uploading files to Hugging Face Hub."""

    signal_status = pyqtSignal(str)
    signal_progress = pyqtSignal(int)
    signal_output = pyqtSignal(str)
    signal_finished = pyqtSignal()

    def __init__(
        self,
        repo_id,
        selected_files,
        repo_type,
        repo_folder,
        current_directory,
        commit_msg,
        create_pr,
        rate_limit_delay,
    ):
        """
        Initializes the HFUploaderThread.

        Args:
            repo_id (str): The ID of the Hugging Face repository (e.g., "username/repo_name").
            selected_files (list): A list of file paths to upload.
            repo_type (str): The type of the repository (e.g., "model", "dataset").
            repo_folder (str): The subfolder within the repository (optional).
            current_directory (str): The current working directory.
            commit_msg (str): The commit message for the upload.
            create_pr (bool): Whether to create a pull request.
            rate_limit_delay (float): The delay in seconds between uploads.
        """
        super().__init__()
        self.repo_id = repo_id
        self.selected_files = selected_files
        self.repo_type = repo_type
        self.repo_folder = repo_folder
        self.current_directory = current_directory
        self.commit_msg = commit_msg
        self.create_pr = create_pr
        self.rate_limit_delay = rate_limit_delay
        self.stop_flag = False
        self.is_stopped = False  # Add this line
        self.api = HfApi()  # Initialize the API

    def stop(self):
        """Sets the stop flag to request the thread to stop."""
        self.stop_flag = True
        self.is_stopped = True  # Add this line

    def run(self):
        """
        Executes the upload process in a separate thread.
        """
        try:
            logger.info("HFUploaderThread: run() called")
            total_files = len(self.selected_files)
            self.signal_status.emit("Starting upload...")
            self.signal_progress.emit(0)

            try:  # Wrap the get_api_token call
                api_token = get_api_token()  # Use the function from config_manager
            except APIKeyError as e:
                self.signal_output.emit(f"❌ API Key Error: {e}")
                self.signal_finished.emit()
                return

            if not api_token:
                self.signal_output.emit("❌ API token not found. Please configure it.")
                self.signal_finished.emit()
                return

            # Initialize the API with the token
            self.api = HfApi(
                token=api_token
            )  # Initialize here, after the token is retrieved

            logger.info("Api Token Found")
            try:
                for idx, ckpt in enumerate(self.selected_files, 1):
                    if self.stop_flag:
                        self.signal_status.emit("Upload cancelled.")
                        break  # Exit the loop if the stop flag is set

                    self.signal_status.emit(f"Uploading: {ckpt}")
                    file_size = os.path.getsize(ckpt)
                    self.signal_output.emit(
                        f"📦 File {idx}/{total_files}: {ckpt} ({format_size(file_size)})"
                    )

                    start_time = time.time()
                    path_in_repo = os.path.basename(ckpt)

                    path_parts = Path(ckpt).parts
                    if len(path_parts) > 1:
                        folder_path_parts = path_parts[
                            len(Path(self.current_directory).parts) : -1
                        ]
                        if folder_path_parts:
                            path_in_repo = os.path.join(
                                *folder_path_parts, os.path.basename(ckpt)
                            )

                    if self.repo_folder:
                        path_in_repo = os.path.join(self.repo_folder, path_in_repo)

                    percentage = int((idx / total_files) * 100)
                    self.signal_progress.emit(percentage)

                    try:
                        logger.info("TRYING TO UPLOAD")
                        response = self.api.upload_file(
                            path_or_fileobj=ckpt,
                            path_in_repo=path_in_repo,
                            repo_id=self.repo_id,
                            repo_type=self.repo_type,
                            create_pr=self.create_pr,  # Use the create_pr attribute
                            commit_message=self.commit_msg,
                            # token=api_token, #Remove the token argument
                        )
                        logger.info("FINISHED TO UPLOAD")

                        duration = time.time() - start_time
                        self.signal_output.emit(
                            f"✅ Upload completed in {duration:.1f} seconds"
                        )
                        self.signal_output.emit(str(response))

                    except Exception as e:
                        logger.error(
                            f"Upload error: {e}", exc_info=True
                        )  # Log the full exception
                        self.signal_output.emit(
                            f"❌ Error uploading {ckpt}: {type(e).__name__} - {str(e)}"
                        )
                        self.signal_output.emit(traceback.format_exc())
                        # Re-raise the exception as an UploadError
                        raise UploadError(f"Failed to upload {ckpt}: {e}") from e

                    # Rate limiting
                    time.sleep(float(self.rate_limit_delay))  # Delay between API calls

            except UploadError as e:  # Catch the upload error
                logger.exception("An unexpected error occurred during upload.")
                self.signal_output.emit(
                    f"❌ An unexpected error occurred: {type(e).__name__} - {str(e)}"
                )
                self.signal_output.emit(traceback.format_exc())

            except Exception as e:
                logger.exception("An unexpected error occurred during upload.")
                self.signal_output.emit(
                    f"❌ An unexpected error occurred: {type(e).__name__} - {str(e)}"
                )
                self.signal_output.emit(traceback.format_exc())

        finally:
            self.signal_progress.emit(100)
            self.signal_finished.emit()
            logger.info("HFUploaderThread: finished")
