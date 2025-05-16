import logging
import os
import time
import threading
from urllib.parse import urlparse
from PyQt6.QtCore import QThread, pyqtSignal
from huggingface_hub import (
    HfApi,
    hf_hub_url,
    hf_hub_download
)
from huggingface_hub.utils import (
    HfHubHTTPError,
    RepositoryNotFoundError,
    RevisionNotFoundError,
)
from config_manager import get_api_token


logger = logging.getLogger(__name__)


class DownloadWorkerThread(QThread):
    progress = pyqtSignal(str, int)
    status_update = pyqtSignal(str, str)
    finished = pyqtSignal(str, bool, str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.is_cancelled = False
        logger.info(
            "DownloadWorkerThread initialized for task: "
            f"{self.task.id} - URL: {self.task.repo_url}"
        )

    def _parse_hf_url(self, hf_url):
        parsed_url = urlparse(hf_url)
        path_parts = [
            part for part in parsed_url.path.strip('/').split('/') if part
        ]

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

        logger.debug(
            f"Parsed URL: repo_id='{repo_id}', repo_type='{repo_type}', "
            f"revision='{revision}', folder_path='{folder_path_in_repo}'"
        )
        return repo_id, repo_type, revision, folder_path_in_repo

    def _perform_download_operations(
        self, repo_id, repo_type, revision, folder_path_in_repo, token
    ):
        self.status_update.emit(self.task.id, "Fetching file list...")
        api = HfApi(token=token)
        try:
            repo_info_obj = api.repo_info(
                repo_id=repo_id,
                revision=revision,
                repo_type=repo_type
            )

            files_to_download = []
            if repo_info_obj.siblings:
                for f_info in repo_info_obj.siblings:
                    if folder_path_in_repo:
                        normalized_folder_path = folder_path_in_repo.strip("/")
                        if (
                            f_info.rfilename.startswith(
                                normalized_folder_path + "/")
                            or f_info.rfilename == normalized_folder_path
                        ):
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
            msg = (
                f"Repository or revision not found: {repo_id}@{revision}. "
                f"Error: {e}"
            )
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
            self.status_update.emit(
                self.task.id, "Download cancelled after fetching file list."
            )
            self.finished.emit(
                self.task.id, False, "Download was cancelled by user."
            )
            return

        grand_total_size = sum(
            f.size for f in files_to_download if f.size is not None
        )
        total_bytes_downloaded_overall = 0
        num_files = len(files_to_download)

        self.status_update.emit(
            self.task.id,
            f"Found {num_files} file(s) to download, total size: "
            f"{grand_total_size / (1024*1024):.2f} MB.",
        )

        for i, file_info in enumerate(files_to_download):
            if self.is_cancelled:
                self.task.status = "Cancelled"
                self.status_update.emit(
                    self.task.id,
                    "Download cancelled before processing file: "
                    f"{file_info.rfilename}",
                )
                self.finished.emit(
                    self.task.id, False, "Download was cancelled by user."
                )
                return

            # Note: We use a threaded approach with hf_hub_download.
            # Cancellation is detected but actual download termination requires
            # force termination via QThread.terminate() which is handled in
            # download_app.py

            file_path_in_repo = file_info.rfilename
            file_size = file_info.size if file_info.size is not None else 0

            local_file_path = os.path.join(
                self.task.download_directory, file_path_in_repo)
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            self.status_update.emit(
                self.task.id,
                f"Downloading file {i+1}/{num_files}: {file_path_in_repo} "
                f"({file_size / (1024*1024):.2f} MB)...",
            )

            bytes_downloaded_for_file = 0
            try:
                # We use hf_hub_download with progress tracking approach
                # 1. Get the URL using hf_hub_url which handles LFS properly
                hf_hub_url(
                    repo_id=repo_id,
                    filename=file_path_in_repo,
                    repo_type=repo_type,
                    revision=revision,
                )

                # 2. Start an async download with hf_hub_download
                download_thread = None
                is_complete = False
                local_file_dir = os.path.dirname(local_file_path)
                os.makedirs(local_file_dir, exist_ok=True)

                def download_file_async():
                    nonlocal is_complete
                    # Use the hub library for download which handles auth
                    # and LFS properly
                    hf_hub_download(
                        repo_id=repo_id,
                        filename=file_path_in_repo,
                        repo_type=repo_type,
                        revision=revision,
                        local_dir=self.task.download_directory,
                        token=token,
                        force_download=True,
                    )
                    is_complete = True

                # Start the download in a separate thread
                download_thread = threading.Thread(target=download_file_async)
                # Allow the thread to be killed if main thread exits
                download_thread.daemon = True
                download_thread.start()

                # 3. Monitor the file size while download is in progress
                check_interval = 0.1  # seconds
                last_size = 0
                while not is_complete:
                    if self.is_cancelled:
                        # Note: This won't actually stop the download thread
                        # We need to rely on the terminate() method from
                        # the parent
                        self.task.status = "Cancelled"
                        self.status_update.emit(
                            self.task.id,
                            "Download cancellation requested for: "
                            f"{file_path_in_repo}",
                        )
                        self.finished.emit(
                            self.task.id,
                            False,
                            "Download was cancelled by user.",
                        )
                        return

                    # Check if the file exists yet
                    if os.path.exists(local_file_path):
                        current_size = os.path.getsize(local_file_path)
                        if current_size > last_size:
                            # Update the progress
                            bytes_downloaded_for_file = current_size
                            total_bytes_downloaded_overall += (
                                current_size - last_size
                            )
                            last_size = current_size

                            file_progress_percent = 0
                            if file_size > 0:
                                file_progress_percent = (
                                    bytes_downloaded_for_file / file_size
                                ) * 100

                            overall_progress_percent = 0
                            if grand_total_size > 0:
                                overall_progress_percent = (
                                    total_bytes_downloaded_overall
                                    / grand_total_size
                                ) * 100

                            self.progress.emit(
                                self.task.id, int(overall_progress_percent)
                            )
                            self.status_update.emit(
                                self.task.id,
                                (
                                    "File {}/{}: {}\n"
                                    "({:.2f}/{:.2f} MB, {:.1f}%) - "
                                    "Overall: {:.1f}%".format(
                                        i + 1,
                                        num_files,
                                        file_path_in_repo,
                                        bytes_downloaded_for_file
                                        / (1024 * 1024),
                                        file_size / (1024 * 1024),
                                        file_progress_percent,
                                        overall_progress_percent,
                                    )
                                ),
                            )

                    time.sleep(check_interval)

                # Download is complete
                if os.path.exists(local_file_path):
                    bytes_downloaded_for_file = os.path.getsize(
                        local_file_path)

                # File is complete - calculate overall progress
                file_progress_percent = 100
                total_bytes_downloaded_overall = sum(
                    os.path.getsize(
                        os.path.join(self.task.download_directory, f.rfilename)
                    )
                    for f in files_to_download[: i + 1]
                    if os.path.exists(
                        os.path.join(self.task.download_directory, f.rfilename)
                    )
                )

                overall_progress_percent = 0
                if grand_total_size > 0:
                    overall_progress_percent = (
                        total_bytes_downloaded_overall / grand_total_size
                    ) * 100

                self.progress.emit(self.task.id, int(overall_progress_percent))
                self.status_update.emit(
                    self.task.id,
                    (
                        f"File {i+1}/{num_files}: {file_path_in_repo} "
                        f"("
                        f"{bytes_downloaded_for_file / (1024*1024):.2f} MB, "
                        f"100%) - "
                        f"Overall: {overall_progress_percent:.1f}%"
                    )
                )

                self.status_update.emit(
                    self.task.id, f"Completed download of {file_path_in_repo}."
                )

            except HfHubHTTPError as e:
                self.task.status = "Failed"
                error_message = (
                    "Hugging Face Hub error downloading "
                    f"{file_path_in_repo}: {e}"
                )
                logger.error(
                    f"Task {self.task.id}: {error_message}", exc_info=True
                )
                self.status_update.emit(self.task.id, error_message)
                self.finished.emit(self.task.id, False, error_message)
                return
            except Exception as e:
                self.task.status = "Failed"
                error_message = (
                    "Unexpected error during download of "
                    f"{file_path_in_repo}: {e}"
                )
                logger.error(
                    f"Task {self.task.id}: {error_message}", exc_info=True
                )
                self.status_update.emit(self.task.id, error_message)
                self.finished.emit(self.task.id, False, error_message)
                return

        self.progress.emit(self.task.id, 100)
        self.task.status = "Completed"
        msg = (
            f"All {num_files} files downloaded successfully for {repo_id} "
            f"into {self.task.download_directory}."
        )
        self.status_update.emit(self.task.id, msg)
        self.finished.emit(self.task.id, True, msg)
        logger.info(f"Task {self.task.id}: {msg}")

    def run(self):
        logger.info(
            "Starting download for task: "
            f"{self.task.id} - URL: {self.task.repo_url}"
        )
        self.task.status = "Downloading"
        self.status_update.emit(self.task.id, "Download started...")
        self.progress.emit(self.task.id, 0)

        if self.is_cancelled:
            self.task.status = "Cancelled"
            self.status_update.emit(
                self.task.id, "Download cancelled before start."
            )
            self.finished.emit(
                self.task.id, False, "Download was cancelled by user."
            )
            logger.info(
                f"Download task {self.task.id} cancelled before start."
            )
            return

        repo_id, repo_type, revision, folder_path_in_repo = self._parse_hf_url(
            self.task.repo_url
        )

        if not repo_id:
            msg = f"Invalid Hugging Face URL: {self.task.repo_url}"
            self.status_update.emit(self.task.id, msg)
            self.finished.emit(self.task.id, False, msg)
            logger.error(f"Task {self.task.id}: {msg}")
            return

        self.status_update.emit(
            self.task.id,
            f"Parsed: Repo ID: {repo_id}, Type: {repo_type}, "
            f"Revision: {revision}, Folder: '{folder_path_in_repo or './'}'",
        )

        token = get_api_token()

        # Log the token retrieval process (without logging the token itself)
        if token:
            logger.debug(
                f"Token retrieved successfully for task {self.task.id}"
            )
        else:
            logger.warning(
                "No token found for task "
                f"{self.task.id}, proceeding with anonymous access"
            )

        try:
            self._perform_download_operations(
                repo_id, repo_type, revision, folder_path_in_repo, token
            )
        except Exception as e:
            self.task.status = "Failed"
            error_message = f"A critical unexpected error occurred: {e}"
            logger.error(
                f"Task {self.task.id}: {error_message}", exc_info=True
            )
            self.status_update.emit(self.task.id, error_message)
            self.finished.emit(self.task.id, False, error_message)

    def cancel_download(self):
        logger.info(
            f"Cancellation requested for download task: {self.task.id}"
        )
        self.is_cancelled = True
        self.status_update.emit(
            self.task.id,
            "Cancellation request received. Note: The internal download "
            "thread may still be running until force terminated.",
        )
