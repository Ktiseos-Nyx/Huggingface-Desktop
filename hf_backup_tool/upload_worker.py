import os
import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal
from huggingface_hub import HfApi, create_repo, upload_file, upload_folder
from custom_exceptions import UploadError, APIKeyError

logger = logging.getLogger(__name__)

class UploadWorker(QThread):
    signal_status = pyqtSignal(str, str)
    signal_progress = pyqtSignal(str, int)  # Add the signal for progress
    signal_output = pyqtSignal(str, str)
    signal_finished = pyqtSignal(bool, str)  # Signal now takes string for a final message

    def __init__(
        self,
        api_token,
        repo_owner,
        repo_name,
        file_path=None,
        folder_path=None,
        commit_message=None,
        repo_type="model",
        repo_folder=None,
        upload_type="File",
        create_repo=False,
        repo_exists=False,
        use_lfs=False,
    ):
        super().__init__()
        self.api_token = api_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.file_path = file_path
        self.folder_path = folder_path
        self.commit_message = commit_message
        self.repo_type = repo_type
        self.repo_folder = repo_folder
        self.upload_type = upload_type
        self.create_repo = create_repo
        self.repo_exists = repo_exists
        self.use_lfs = use_lfs # NEW LFS

    def run(self):
        try:
            if not self.api_token:
                raise APIKeyError("API token not found in configuration.")
            api = HfApi()
            repo_id = f"{self.repo_owner}/{self.repo_name}"
            if self.repo_exists:
                try:
                    api.repo_info(repo_id, repo_type=self.repo_type)
                    self.signal_output.emit(self.task_id, f"✅ Repository '{repo_id}' found.")
                except Exception as e:
                    msg = f"❌ Repository '{repo_id}' not found. Error: {str(e)}"
                    self.signal_output.emit(self.task_id, msg)
                    self.signal_finished.emit(False, msg)
                    return
            if self.create_repo:
                try:
                    create_repo(
                        repo_id,
                        repo_type=self.repo_type,
                        token=self.api_token,
                        private=False,
                    )
                    self.signal_output.emit(self.task_id, f"✅ Repository '{repo_id}' created successfully.")
                except Exception as e:
                    msg = f"❌ Failed to create repository '{repo_id}'. Error: {str(e)}"
                    self.signal_output.emit(self.task_id, msg)
                    self.signal_finished.emit(False, msg)
                    return
            if self.upload_type == "File":
                if not self.file_path:
                    raise UploadError("No file selected for upload.")
                try:
                    file_name = os.path.basename(self.file_path)
                    if self.repo_folder:
                        path_in_repo = f"{self.repo_folder}/{file_name}"
                    else:
                        path_in_repo = file_name

                    self.signal_output.emit(self.task_id, f"⏳ Uploading {file_name}...")  # START MESSAGE
                    # Get file size to use for progress bar.
                    file_size = os.path.getsize(self.file_path)
                    bytes_uploaded = 0

                    def progress_callback(progress):
                         self.signal_progress.emit(self.task_id, progress)
                    # Use the new upload function
                    if self.use_lfs:
                         # In the future, you'd use a different API method, but the `upload_file` call below works
                         # with Git LFS if the file is correctly tracked.  The important thing is that
                         # the user has Git LFS configured.
                         api.upload_file(
                             path_or_fileobj=self.file_path,
                             path_in_repo=path_in_repo,
                             repo_id=repo_id,
                             repo_type=self.repo_type,
                             token=self.api_token,
                             commit_message=self.commit_msg,
                             create_pr=self.create_pr,
                         )
                    else:
                         api.upload_file(
                             path_or_fileobj=self.file_path,
                             path_in_repo=path_in_repo,
                             repo_id=repo_id,
                             repo_type=self.repo_type,
                             token=self.api_token,
                             commit_message=self.commit_msg,
                             create_pr=self.create_pr,
                         )
                    self.signal_output.emit(self.task_id, f"✅ File '{file_name}' uploaded to '{repo_id}' successfully.")
                except Exception as e:
                    msg = f"❌ File upload failed. Error: {str(e)}"
                    self.signal_output.emit(self.task_id, msg)
                    self.signal_finished.emit(False, msg)
                    return
            elif self.upload_type == "Folder":
                if not self.folder_path:
                    raise UploadError("No folder selected for upload.")
                try:
                    self.signal_output.emit(self.task_id, f"⏳ Uploading {self.folder_path}...")  # START MESSAGE
                    upload_folder(
                        folder_path=self.folder_path,
                        repo_id=repo_id,
                        repo_type=self.repo_type,
                        commit_message=self.commit_message,
                        token=self.api_token,
                    )
                    self.signal_output.emit(self.task_id, f"✅ Folder '{self.folder_path}' uploaded to '{repo_id}' successfully.")
                except Exception as e:
                    msg = f"❌ Folder upload failed. Error: {str(e)}"
                    self.signal_output.emit(self.task_id, msg)
                    self.signal_finished.emit(False, msg)
                    return

            self.signal_finished.emit(True, "Upload completed successfully.")
        except APIKeyError as e:
            msg = f"❌ API Key Error: {str(e)}"
            self.signal_output.emit(self.task_id, msg)
            self.signal_finished.emit(False, msg)
        except UploadError as e:
            msg = f"❌ Upload Error: {str(e)}"
            self.signal_output.emit(self.task_id, msg)
            self.signal_finished.emit(False, msg)
        except Exception as e:
            msg = f"❌ An unexpected error occurred: {e}"
            self.signal_output.emit(self.task_id, msg)
            self.signal_finished.emit(False, msg)