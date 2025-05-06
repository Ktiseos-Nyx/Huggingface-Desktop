import logging
import os
import shutil
import zipfile

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QTextEdit,
)

from config_manager import config

logger = logging.getLogger(__name__)


class ZipApp(QWidget):
    """Widget for zipping folders."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folder Zipper")
        self.folder_path = ""

        # Widgets
        self.folder_label = QLabel("Folder:")
        self.folder_input = QLineEdit()
        self.folder_button = QPushButton("Select Folder")
        self.zip_name_label = QLabel("Zip Name:")
        self.zip_name_input = QLineEdit(
            config["Zip"]["default_zip_name"]
        )  # From config
        self.zip_button = QPushButton("Zip and Save")
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        # Layout
        hbox = QHBoxLayout()
        hbox.addWidget(self.folder_input)
        hbox.addWidget(self.folder_button)

        vbox = QVBoxLayout()
        vbox.addWidget(self.folder_label)
        vbox.addLayout(hbox)
        vbox.addWidget(self.zip_name_label)
        vbox.addWidget(self.zip_name_input)
        vbox.addWidget(self.zip_button)
        vbox.addWidget(self.output_text)

        self.setLayout(vbox)

        # Connections
        self.folder_button.clicked.connect(self.select_folder)
        self.zip_button.clicked.connect(self.zip_and_save)

    def select_folder(self):
        """Opens a dialog to select a folder."""
        self.folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        self.folder_input.setText(self.folder_path)

    def zip_and_save(self):
        """Zips the selected folder and saves it to a location chosen by the user."""
        folder_path = self.folder_input.text()
        zip_file_name = self.zip_name_input.text().strip()

        if not folder_path:
            self.output_text.append("Please select a folder.")
            return
        if not zip_file_name:
            self.output_text.append("Please enter a zip file name.")
            return
        if not os.path.isdir(folder_path):
            self.output_text.append(
                "Invalid folder path. Please provide a valid directory"
            )
            return

        zip_file_path = zip_file_name + ".zip"

        try:
            temp_dir = "temp_zip_dir"
            os.makedirs(temp_dir, exist_ok=True)
            temp_zip_path = os.path.join(temp_dir, zip_file_path)

            with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, relative_path)

            # Get the directory to save the zip file to
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save Zip File", zip_file_path, "Zip files (*.zip)"
            )

            if save_path:
                shutil.copy2(temp_zip_path, save_path)
                self.output_text.append(
                    f"Successfully created and saved {zip_file_path} to {save_path}"
                )
            else:
                self.output_text.append("Zip file creation cancelled.")

        except Exception as e:
            logger.error(f"Zip error: {e}", exc_info=True)  # Log the exception
            self.output_text.append(f"Error creating zip file: {e}")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
