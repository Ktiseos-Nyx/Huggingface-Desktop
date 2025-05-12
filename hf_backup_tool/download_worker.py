import logging
import os
import requests
from urllib.parse import urlparse
from PyQt6.QtCore import QThread, pyqtSignal
from huggingface_hub import (
    HfApi,
    hf_hub_url,
)
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError, RevisionNotFoundError
from config_manager import get_api_token
from token_utils import deobfuscate_token


logger = logging.getLogger(__name__)

class DownloadWorkerThread(QThread):
    progress = pyqtSignal(str, int)
    status_update = pyqtSignal(str, str)
    finished = pyqtSignal(str, bool, str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.is_cancelled = False
        logger.info(f"DownloadWorkerThread initialized for task: {self.task.id} - URL: {self.task.repo_url}")

    def _parse_hf_url(self, hf_url):
        parsed_url = urlparse(hf_url)
        path_parts = [part for part in parsed_url.path.strip('/').split('/') if part]

        if not path_parts:
            return None, None, None, None

        repo_type = "model"
        if path_parts[0] == "datasets":
            repo_type = "dataset"
            path_parts.pop(0)
        elif path_parts[0] == "spaces":
            repo_type = "space"
            path_parts.pop(0)
        
        if len(path_parts) < 2:
            return None, None, None, None

        repo_id = f"{path_parts[0]}/{path_parts[1]}"
        revision = "main"
        folder_path_in_repo = ""

        if len(path_parts) > 2 and path_parts[2] == "tree":
            if len(path_parts) > 3:
                revision = path_parts[3]
                if len(path_parts) > 4:
                    folder_path_in_repo = "/".join(path_parts[4:])

        logger.debug(f"Parsed URL: repo_id='{repo_id}', repo_type='{repo_type}', revision='{revision}', folder_path='{folder_path_in_repo}'")
        return repo_id, repo_type, revision, folder_path_in_repo


    def _perform_download_operations(self, repo_id, repo_type, revision, folder_path_in_repo, token):
        self.status_update.emit(self.task.id, "Fetching file list...")
        api = HfApi()
        try:
            repo_info_obj = api.repo_info(
                repo_id=repo_id,
                revision=revision,
                repo_type=repo_type,
                token=token
            )
            
            files_to_download = []
            if repo_info_obj.siblings:
                for f_info in repo_info_obj.siblings:
                    if folder_path_in_repo:
                        normalized_folder_path = folder_path_in_repo.strip("/")
                        if f_info.rfilename.startswith(normalized_folder_path + "/") or f_info.rfilename == normalized_folder_path:
                            files_to_download.append(f_info)
                    else:
                        files_to_download.append(f_info)
            
            if not files_to_download:
                msg = f"No files found in '{repo_id}'"
                if folder_path_in_repo:
                    msg += f" at path '{folder_path_in_repo}'"
                msg += f" (revision: {revision})."
                self.status_update.emit(self.task.id, msg)
                self.finished.emit(self.task.id, True, msg)
                logger.info(f"Task {self.task.id}: {msg}")
                return

        except (RepositoryNotFoundError, RevisionNotFoundError) as e:
            msg = f"Repository or revision not found: {repo_id}@{revision}. Error: {e}"
            self.status_update.emit(self.task.id, msg)
            self.finished.emit(self.task.id, False, msg)
            logger.error(f"Task {self.task.id}: {msg}")
            return
        except HfHubHTTPError as e:
            msg = f"HTTP error fetching file list for {repo_id}: {e}"
            self.status_update.emit(self.task.id, msg)
            self.finished.emit(self.task.id, False, msg)
            logger.error(f"Task {self.task.id}: {msg}")
            return
        except Exception as e:
            msg = f"Error fetching file list for {repo_id}: {e}"
            self.status_update.emit(self.task.id, msg)
            self.finished.emit(self.task.id, False, msg)
            logger.error(f"Task {self.task.id}: {msg}", exc_info=True)
            return

        if self.is_cancelled:
            self.task.status = "Cancelled"
            self.status_update.emit(self.task.id, "Download cancelled after fetching file list.")
            self.finished.emit(self.task.id, False, "Download was cancelled by user.")
            return

        grand_total_size = sum(f.size for f in files_to_download if f.size is not None)
        total_bytes_downloaded_overall = 0
        num_files = len(files_to_download)

        self.status_update.emit(self.task.id, f"Found {num_files} file(s) to download, total size: {grand_total_size / (1024*1024):.2f} MB.")

        for i, file_info in enumerate(files_to_download):
            if self.is_cancelled:
                self.task.status = "Cancelled"
                self.status_update.emit(self.task.id, f"Download cancelled before processing file: {file_info.rfilename}")
                self.finished.emit(self.task.id, False, "Download was cancelled by user.")
                return

            file_path_in_repo = file_info.rfilename
            file_size = file_info.size if file_info.size is not None else 0

            local_file_path = os.path.join(self.task.download_directory, file_path_in_repo)
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            self.status_update.emit(self.task.id, f"Downloading file {i+1}/{num_files}: {file_path_in_repo} ({file_size / (1024*1024):.2f} MB)...")
            
            download_url = hf_hub_url(
                repo_id=repo_id,
                filename=file_path_in_repo,
                repo_type=repo_type,
                revision=revision
            )

            bytes_downloaded_for_file = 0
            try:
                headers = {}
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                
                with requests.get(download_url, stream=True, headers=headers, timeout=30) as r:
                    r.raise_for_status()
                    actual_file_size = int(r.headers.get('content-length', file_size))
                    if file_size == 0 and actual_file_size > 0 :
                        if grand_total_size == 0 and num_files == 1:
                             grand_total_size = actual_file_size
                        file_size = actual_file_size


                    with open(local_file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if self.is_cancelled:
                                f.close()
                                if os.path.exists(local_file_path):
                                    os.remove(local_file_path)
                                self.task.status = "Cancelled"
                                self.status_update.emit(self.task.id, f"Download of {file_path_in_repo} cancelled during transfer.")
                                self.finished.emit(self.task.id, False, "Download was cancelled by user.")
                                return
                            
                            if chunk:
                                f.write(chunk)
                                bytes_downloaded_for_file += len(chunk)
                                total_bytes_downloaded_overall += len(chunk)
                                
                                file_progress_percent = 0
                                if file_size > 0:
                                    file_progress_percent = (bytes_downloaded_for_file / file_size) * 100
                                
                                overall_progress_percent = 0
                                if grand_total_size > 0:
                                    overall_progress_percent = (total_bytes_downloaded_overall / grand_total_size) * 100
                                
                                self.progress.emit(self.task.id, int(overall_progress_percent))
                                self.status_update.emit(self.task.id, f"File {i+1}/{num_files}: {file_path_in_repo} ({bytes_downloaded_for_file / (1024*1024):.2f}/{file_size / (1024*1024):.2f} MB, {file_progress_percent:.1f}%) - Overall: {overall_progress_percent:.1f}%")
                
                self.status_update.emit(self.task.id, f"Completed download of {file_path_in_repo}.")

            except requests.exceptions.RequestException as e:
                self.task.status = "Failed"
                error_message = f"Error downloading {file_path_in_repo}: {e}"
                logger.error(f"Task {self.task.id}: {error_message}", exc_info=True)
                self.status_update.emit(self.task.id, error_message)
                self.finished.emit(self.task.id, False, error_message)
                return
            except Exception as e:
                self.task.status = "Failed"
                error_message = f"Unexpected error during download of {file_path_in_repo}: {e}"
                logger.error(f"Task {self.task.id}: {error_message}", exc_info=True)
                self.status_update.emit(self.task.id, error_message)
                self.finished.emit(self.task.id, False, error_message)
                return

        self.progress.emit(self.task.id, 100)
        self.task.status = "Completed"
        msg = f"All {num_files} files downloaded successfully for {repo_id} into {self.task.download_directory}."
        self.status_update.emit(self.task.id, msg)
        self.finished.emit(self.task.id, True, msg)
        logger.info(f"Task {self.task.id}: {msg}")


    def run(self):
        logger.info(f"Starting download for task: {self.task.id} - URL: {self.task.repo_url}")
        self.task.status = "Downloading"
        self.status_update.emit(self.task.id, "Download started...")
        self.progress.emit(self.task.id, 0)

        if self.is_cancelled:
            self.task.status = "Cancelled"
            self.status_update.emit(self.task.id, "Download cancelled before start.")
            self.finished.emit(self.task.id, False, "Download was cancelled by user.")
            logger.info(f"Download task {self.task.id} cancelled before start.")
            return

        repo_id, repo_type, revision, folder_path_in_repo = self._parse_hf_url(self.task.repo_url)

        if not repo_id:
            msg = f"Invalid Hugging Face URL: {self.task.repo_url}"
            self.status_update.emit(self.task.id, msg)
            self.finished.emit(self.task.id, False, msg)
            logger.error(f"Task {self.task.id}: {msg}")
            return

        self.status_update.emit(self.task.id, f"Parsed: Repo ID: {repo_id}, Type: {repo_type}, Revision: {revision}, Folder: '{folder_path_in_repo or './'}'")

        token = get_api_token()
        deobfuscated_token = None
        if token:
            deobfuscated_token = deobfuscate_token(token)
            if not deobfuscated_token:
                self.status_update.emit(self.task.id, "Warning: Failed to deobfuscate API token. Private repos may fail.")
        
        try:
            self._perform_download_operations(repo_id, repo_type, revision, folder_path_in_repo, deobfuscated_token)
        except Exception as e:
            self.task.status = "Failed"
            error_message = f"A critical unexpected error occurred: {e}"
            logger.error(f"Task {self.task.id}: {error_message}", exc_info=True)
            self.status_update.emit(self.task.id, error_message)
            self.finished.emit(self.task.id, False, error_message)


    def cancel_download(self):
        logger.info(f"Cancellation requested for download task: {self.task.id}")
        self.is_cancelled = True
        self.status_update.emit(self.task.id, "Cancellation request received. Download will stop at the next check.")
