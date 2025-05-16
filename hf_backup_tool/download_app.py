import logging
import collections
import uuid
import os
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from download_worker import DownloadWorkerThread
from config_manager import get_max_concurrent_downloads, load_config
from config_dialog import ConfigDialog  # Import the ConfigDialog

logger = logging.getLogger(__name__)


class DownloadTask:
    def __init__(self, repo_url, download_directory):
        self.id = str(uuid.uuid4())
        self.repo_url = repo_url
        self.download_directory = download_directory
        self.status = "Pending"
        self.progress = 0

    def __repr__(self):
        return f"DownloadTask(id={self.id}, url='{self.repo_url}', status='{self.status}', progress={self.progress}%)"


class DownloadApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Download from Repository")
        self.download_queue = collections.deque()
        self.active_workers = {}
        self.task_map = {}

        # Load configuration here to ensure it's loaded before anything else
        try:
            load_config()  # Load the config at application startup
            self.max_concurrent_downloads = get_max_concurrent_downloads()
        except Exception as e:
            logger.error(
                f"Error loading max_concurrent_downloads from config: {e}. Defaulting to 1."
            )
            self.max_concurrent_downloads = 1
            QMessageBox.warning(
                self,
                "Config Warning",
                f"Could not load max concurrent downloads setting. Defaulting to 1. Error: {e}",
            )

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        input_layout = QVBoxLayout()
        self.repo_url_label = QLabel("Repository URL:")
        self.repo_url_input = QLineEdit()
        input_layout.addWidget(self.repo_url_label)
        input_layout.addWidget(self.repo_url_input)

        self.download_dir_label = QLabel("Download Directory:")
        self.download_dir_input = QLineEdit()
        self.download_dir_button = QPushButton("Select Directory")
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.download_dir_input)
        dir_layout.addWidget(self.download_dir_button)
        input_layout.addWidget(self.download_dir_label)
        input_layout.addLayout(dir_layout)

        self.add_to_queue_button = QPushButton("Add to Queue")
        input_layout.addWidget(self.add_to_queue_button)
        main_layout.addLayout(input_layout)

        # Settings Button
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_config_dialog)
        main_layout.addWidget(self.settings_button)

        queue_label = QLabel("Download Queue (Active & Pending):")
        main_layout.addWidget(queue_label)
        self.queue_list_widget = QListWidget()
        main_layout.addWidget(self.queue_list_widget)

        queue_controls_layout = QHBoxLayout()
        self.cancel_all_tasks_button = QPushButton("Cancel All Tasks")
        queue_controls_layout.addWidget(self.cancel_all_tasks_button)
        self.remove_selected_button = QPushButton("Remove Selected from Queue")
        queue_controls_layout.addWidget(self.remove_selected_button)
        self.clear_queue_button = QPushButton("Clear Entire Queue")
        queue_controls_layout.addWidget(self.clear_queue_button)
        main_layout.addLayout(queue_controls_layout)

        log_label = QLabel("Log:")
        main_layout.addWidget(log_label)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFixedHeight(100)
        main_layout.addWidget(self.output_text)
        self.setLayout(main_layout)

        self.download_dir_button.clicked.connect(self.select_download_directory)
        self.add_to_queue_button.clicked.connect(self.add_to_download_queue)
        self.cancel_all_tasks_button.clicked.connect(self.handle_cancel_all_tasks)
        self.remove_selected_button.clicked.connect(self.remove_selected_from_queue)
        self.clear_queue_button.clicked.connect(self.clear_download_queue)
        self.queue_list_widget.itemSelectionChanged.connect(self.update_button_states)
        self.update_queue_display()

    def open_config_dialog(self):
        dialog = ConfigDialog()
        if dialog.exec() == QDialog.Accepted:  # Use QDialog.Accepted for clarity
            # Optionally, refresh any settings that might affect the UI
            # You might reload the config here or just update relevant settings
            pass

    def update_button_states(self):
        can_cancel_anything = bool(self.active_workers or self.download_queue)
        self.cancel_all_tasks_button.setEnabled(can_cancel_anything)

        selected_items = self.queue_list_widget.selectedItems()
        can_remove_selected = False
        if selected_items:
            selected_text = selected_items[0].text()
            try:
                task_id_to_check = selected_text.split(" - ID: ")[-1]
                if '%)' in task_id_to_check:
                    task_id_to_check = task_id_to_check.split("%)")[0].strip()

                task = self.task_map.get(task_id_to_check)
                if task:
                    if task_id_to_check not in self.active_workers:
                        can_remove_selected = True
            except Exception as e:
                logger.error(
                    f"Exception in update_button_states (for remove button logic for item '{selected_text}'): {e}",
                    exc_info=True,
                )
        self.remove_selected_button.setEnabled(can_remove_selected)

    def select_download_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.download_dir_input.setText(directory)

    def add_to_download_queue(self):
        repo_url = self.repo_url_input.text()
        download_directory = self.download_dir_input.text()
        if not repo_url or not download_directory:
            self.output_text.append("Please provide both repository URL and download directory.")
            return
        task = DownloadTask(repo_url, download_directory)
        self.download_queue.append(task)
        self.task_map[task.id] = task
        self.output_text.append(f"Added to queue: {task.repo_url} (ID: {task.id})")
        logger.info(f"Task {task.id} added to download queue: {task.repo_url}")
        self.update_queue_display()
        self._process_queue()

    def _process_queue(self):
        while (
            len(self.active_workers) < self.max_concurrent_downloads and self.download_queue
        ):
            task_to_start = self.download_queue.popleft()
            task_to_start.status = "Downloading"
            self.task_map[task_to_start.id] = task_to_start

            self.output_text.append(
                f"Starting download: {task_to_start.repo_url} (ID: {task_to_start.id})"
            )
            logger.info(f"Processing download task: {task_to_start}")

            worker = DownloadWorkerThread(task_to_start)
            worker.progress.connect(self.on_download_progress)
            worker.status_update.connect(self.on_download_status_update)
            worker.finished.connect(self.on_download_finished)

            self.active_workers[task_to_start.id] = worker
            worker.start()
        self.update_queue_display()

    def on_download_progress(self, task_id, percentage):
        task = self.task_map.get(task_id)
        if task:
            task.progress = percentage
            self.update_queue_display()
        logger.debug(f"Task {task_id} progress: {percentage}%")

    def on_download_status_update(self, task_id, message):
        self.output_text.append(f"Status ({task_id}): {message}")
        self.update_queue_display()

    def on_download_finished(self, task_id, success, message):
        logger.info(
            f"Download task {task_id} finished. Success: {success}. Message: {message}"
        )
        self.output_text.append(f"Download finished for {task_id}: {message}")

        task = self.task_map.get(task_id)
        if task:
            task.status = "Completed" if success else "Failed"
            task.progress = 100

        if task_id in self.active_workers:
            del self.active_workers[task_id]

        self.update_queue_display()
        self._process_queue()

    def handle_cancel_all_tasks(self):
        logger.info("User initiated 'Cancel All Tasks'.")
        self.output_text.append("Attempting to cancel all active and pending downloads...")

        active_tasks_cancelled_count = 0
        if not self.active_workers and not self.download_queue:
            self.output_text.append("No tasks to cancel.")
            return

        for task_id, worker in list(self.active_workers.items()):
            task = self.task_map.get(task_id)
            if worker.isRunning():
                logger.info(f"Cancelling active task: {task_id}")
                worker.cancel_download()
                if task:
                    task.status = "Cancelling"
                active_tasks_cancelled_count += 1
            elif task:
                task.status = "Cancelled"

        if active_tasks_cancelled_count > 0:
            self.output_text.append(
                f"Cancellation requested for {active_tasks_cancelled_count} active download(s)."
            )

        pending_tasks_cleared_count = 0
        pending_ids_to_remove = []
        for task in list(self.download_queue):
            task.status = "Cancelled"
            pending_ids_to_remove.append(task.id)
            pending_tasks_cleared_count += 1

        self.download_queue.clear()

        for task_id in pending_ids_to_remove:
            if task_id in self.task_map:
                del self.task_map[task_id]
                logger.info(f"Removed cancelled pending task {task_id} from task_map.")

        if pending_tasks_cleared_count > 0:
            self.output_text.append(
                f"Cleared {pending_tasks_cleared_count} pending download(s)."
            )

        self.update_queue_display()

    def remove_selected_from_queue(self):
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            self.output_text.append("No task selected from the queue to remove.")
            return

        selected_text = selected_items[0].text()
        try:
            task_id_to_remove = selected_text.split(" - ID: ")[-1]
            if '%)' in task_id_to_remove:
                task_id_to_remove = task_id_to_remove.split("%)")[0].strip()

            task = self.task_map.get(task_id_to_remove)

            if task:
                if task_id_to_remove in self.active_workers:
                    self.output_text.append(
                        f"Cannot remove active task {task_id_to_remove}. Cancel it first."
                    )
                    return

                if task in self.download_queue:
                    self.download_queue.remove(task)

                del self.task_map[task_id_to_remove]

                self.output_text.append(f"Removed task {task_id_to_remove} ({task.repo_url}) from records.")
                logger.info(f"Task {task_id_to_remove} removed by user.")
                self.update_queue_display()
            else:
                self.output_text.append(f"Task with ID {task_id_to_remove} not found for removal.")
        except Exception as e:
            logger.error(f"Error parsing selected item text for removal: {e}")
            self.output_text.append("Could not identify selected task for removal.")

    def clear_download_queue(self):
        if not self.download_queue and not self.active_workers:
            self.output_text.append("Download queue and active tasks are already empty.")
            return

        reply = QMessageBox.question(
            self,
            "Clear Downloads",
            "This will clear all pending downloads. Do you also want to attempt to cancel active downloads?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return

        if reply == QMessageBox.StandardButton.Yes:
            for task_id, worker in list(self.active_workers.items()):
                if worker.isRunning():
                    self.output_text.append(f"Attempting to cancel active task {task_id} as part of clear.")
                    worker.cancel_download()
                    if self.task_map.get(task_id):
                        self.task_map[task_id].status = "Cancelling"

        num_pending_cleared = len(self.download_queue)
        pending_ids_to_remove = [task.id for task in self.download_queue]
        self.download_queue.clear()
        for task_id in pending_ids_to_remove:
            if task_id in self.task_map:
                del self.task_map[task_id]

        self.output_text.append(f"Cleared {num_pending_cleared} tasks from the pending download queue.")
        logger.info(f"Pending download queue cleared by user ({num_pending_cleared} tasks). Active tasks cancellation attempted if chosen.")
        self.update_queue_display()

    def update_queue_display(self):
        self.queue_list_widget.clear()

        for task_id, worker in self.active_workers.items():
            task = self.task_map.get(task_id)
            if task:
                item_text = f"[{task.status}] {task.repo_url} ({task.progress}%) - ID: {task.id}"
                self.queue_list_widget.addItem(QListWidgetItem(item_text))

        for task in self.download_queue:
            item_text = f"[{task.status}] {task.repo_url} - ID: {task.id}"
            self.queue_list_widget.addItem(QListWidgetItem(item_text))

        self.update_button_states()