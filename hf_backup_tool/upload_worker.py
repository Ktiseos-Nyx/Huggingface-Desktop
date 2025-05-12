from PyQt6.QtCore import QThread, pyqtSignal
from huggingface_hub import HfApi, create_repo, upload_file, upload_folder
import os
from custom_exceptions import UploadError, APIKeyError

class UploadWorker(QThread):
    progress_signal = pyqtSignal(int)
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

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

    def run(self):
        try:
            if not self.api_token:
                raise APIKeyError("API token not found in configuration.")
            api = HfApi(token=self.api_token)
            repo_id = f"{self.repo_owner}/{self.repo_name}"
            if self.repo_exists:
                try:
                    api.repo_info(repo_id)
                    self.output_signal.emit(f"✅ Repository '{repo_id}' found.")
                except Exception as e:
                    self.output_signal.emit(
                        f"❌ Repository '{repo_id}' not found. Error: {str(e)}"
                    )
                    self.finished_signal.emit(False)
                    return
            if self.create_repo:
                try:
                    create_repo(
                        repo_id,
                        repo_type=self.repo_type,
                        token=self.api_token,
                        private=False,
                    )
                    self.output_signal.emit(
                        f"✅ Repository '{repo_id}' created successfully."
                    )
                except Exception as e:
                    self.output_signal.emit(
                        f"❌ Failed to create repository '{repo_id}'. Error: {str(e)}"
                    )
                    self.finished_signal.emit(False)
                    return
            if self.upload_type == "File":
                if not self.file_path:
                    raise UploadError("No file selected for upload.")
                try:
                    filename = os.path.basename(self.file_path)
                    if self.repo_folder:
                        upload_path = os.path.join(self.repo_folder, filename)
                    else:
                        upload_path = filename
                    upload_file(
                        path_or_fileobj=self.file_path,
                        path_in_repo=upload_path,
                        repo_id=repo_id,
                        repo_type=self.repo_type,
                        commit_message=self.commit_message,
                        token=self.api_token,
                        create_pr=False,
                    )
                    self.output_signal.emit(
                        f"✅ File '{filename}' uploaded to '{repo_id}' successfully."
                    )
                except Exception as e:
                    self.output_signal.emit(f"❌ File upload failed. Error: {str(e)}")
                    self.finished_signal.emit(False)
                    return
            elif self.upload_type == "Folder":
                if not self.folder_path:
                    raise UploadError("No folder selected for upload.")
                try:
                    upload_folder(
                        folder_path=self.folder_path,
                        repo_id=repo_id,
                        repo_type=self.repo_type,
                        commit_message=self.commit_message,
                        token=self.api_token,
                    )
                    self.output_signal.emit(
                        f"✅ Folder '{self.folder_path}' uploaded to '{repo_id}' successfully."
                    )
                except Exception as e:
                    self.output_signal.emit(f"❌ Folder upload failed. Error: {str(e)}")
                    self.finished_signal.emit(False)
                    return
            self.finished_signal.emit(True)
        except APIKeyError as e:
            self.output_signal.emit(f"❌ API Key Error: {str(e)}")
            self.finished_signal.emit(False)
        except UploadError as e:
            self.output_signal.emit(f"❌ Upload Error: {str(e)}")
            self.finished_signal.emit(False)
        except Exception as e:
            self.output_signal.emit(f"❌ An unexpected error occurred: {str(e)}")
            self.finished_signal.emit(False)
