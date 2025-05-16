import os
import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal
from huggingface_hub import HfApi  # Use HfApi
from huggingface_hub.utils import HfHubHTTPError
from config_manager import get_api_token  # Make sure this is imported correctly

logger = logging.getLogger(__name__)

class HFUploaderThread(QThread):
    signal_status = pyqtSignal(str, str)
    signal_progress = pyqtSignal(str, int)
    signal_output = pyqtSignal(str, str)
    signal_finished = pyqtSignal(str, bool, str)

    def __init__(self, repo_id, selected_files, repo_type, repo_folder, current_directory, commit_msg, create_pr, rate_limit_delay, task_id=None):
        super().__init__()
        self.task_id = task_id
        self.repo_id = repo_id
        self.selected_files = selected_files
        self.repo_type = repo_type
        self.repo_folder = repo_folder.strip('/')
        self.current_directory = current_directory
        self.commit_msg = commit_msg
        self.create_pr = create_pr
        self.rate_limit_delay = rate_limit_delay
        self._is_running = True
        self.api = HfApi() # Initialise HfApi

    def run(self):
        overall_success = True
        final_message = "Upload process completed."
        api_token = get_api_token()
        if not api_token:
            msg = "❌ Hugging Face API token not found. Please configure it."
            self.signal_output.emit(self.task_id, msg)
            self.signal_finished.emit(self.task_id, False, msg)
            return

        try:
            self.signal_output.emit(self.task_id, "Starting upload...")
            total_files = len(self.selected_files)
            if total_files == 0:
                msg = "ℹ️ No files selected for upload in this task."
                self.signal_output.emit(self.task_id, msg)
                self.signal_finished.emit(self.task_id, True, msg)
                return
            files_uploaded_successfully = 0
            for i, file_path in enumerate(self.selected_files):
                if not self._is_running:
                    final_message = "ℹ️ Upload cancelled by user."
                    self.signal_output.emit(self.task_id, final_message)
                    overall_success = False
                    break
                file_name = os.path.basename(file_path)
                path_in_repo = file_name
                if self.repo_folder:
                    path_in_repo = f"{self.repo_folder}/{file_name}"
                self.signal_status.emit(self.task_id, f"Uploading {file_name}...")
                self.signal_output.emit(self.task_id, f"⏳ Starting upload of {file_name} to {self.repo_id}/{path_in_repo}")
                try:
                    self.api.upload_file(  # Use self.api
                        path_or_fileobj=file_path,
                        path_in_repo=path_in_repo,
                        repo_id=self.repo_id,
                        token=api_token,
                        repo_type=self.repo_type,
                        commit_message=self.commit_msg,
                        create_pr=self.create_pr,
                    )
                    self.signal_output.emit(self.task_id, f"✅ Successfully uploaded {file_name}")
                    files_uploaded_successfully += 1
                except HfHubHTTPError as e:
                    self.signal_output.emit(self.task_id, f"❌ HTTP Error uploading {file_name}: {e}")
                    logger.error(f"Task {self.task_id}: HTTP Error uploading {file_name} to {self.repo_id}: {e}", exc_info=True)
                    overall_success = False
                except FileNotFoundError:
                    self.signal_output.emit(self.task_id, f"❌ File not found: {file_path}")
                    logger.error(f"Task {self.task_id}: File not found for upload: {file_path}", exc_info=True)
                    overall_success = False
                except Exception as e:
                    self.signal_output.emit(self.task_id, f"❌ An unexpected error occurred uploading {file_name}: {e}")
                    logger.error(f"Task {self.task_id}: Unexpected error uploading {file_name}: {e}", exc_info=True)
                    overall_success = False
                progress = int(((i + 1) / total_files) * 100)
                self.signal_progress.emit(self.task_id, progress)
                if self.rate_limit_delay > 0 and (i + 1) < total_files:
                    if not self._is_running:
                        break
                    time.sleep(self.rate_limit_delay)
            if not self._is_running:
                self.signal_status.emit(self.task_id, "Upload cancelled.")
                final_message = "Upload task cancelled by user."
                overall_success = False
            elif overall_success:
                self.signal_status.emit(self.task_id, "Upload complete.")
                final_message = f"🎉 All {total_files} files processed. {files_uploaded_successfully} succeeded."
            else:
                self.signal_status.emit(self.task_id, "Upload completed with errors.")
                final_message = f"⚠️ Task completed with errors. {files_uploaded_successfully}/{total_files} files uploaded successfully."
        except Exception as e:
            final_message = f"❌ A critical error occurred in the upload thread: {e}"
            self.signal_output.emit(self.task_id, final_message)
            logger.error(f"Task {self.task_id}: Critical error in HFUploaderThread: {e}", exc_info=True)
            overall_success = False
        finally:
            self.signal_finished.emit(self.task_id, overall_success, final_message)

    def stop(self):
        self.signal_output.emit(self.task_id, "ℹ️ Cancellation requested. Upload will stop after the current file completes or before the next one starts.")
        self._is_running = False