# hf_backup_tool/ui/download_app.py
import logging
import os
import subprocess

from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFileDialog, QTextEdit, QApplication)

#from ..downloads.download_manager import create_download  # Import the download function  <- REMOVE THIS

logger = logging.getLogger(__name__)


class DownloadApp(QWidget):
    """Widget for downloading files from a repository."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Download from Repository")

        # Widgets
        self.repo_url_label = QLabel("Repository URL:")
        self.repo_url_input = QLineEdit()
        self.download_dir_label = QLabel("Download Directory:")
        self.download_dir_input = QLineEdit()
        self.download_dir_button = QPushButton("Select Directory")
        self.download_button = QPushButton("Start Download")
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        # Layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.repo_url_label)
        vbox.addWidget(self.repo_url_input)

        hbox = QHBoxLayout()
        hbox.addWidget(self.download_dir_input)
        hbox.addWidget(self.download_dir_button)

        vbox.addWidget(self.download_dir_label)
        vbox.addLayout(hbox)
        vbox.addWidget(self.download_button)
        vbox.addWidget(self.output_text)

        self.setLayout(vbox)

        # Connections
        self.download_dir_button.clicked.connect(self.select_download_directory)
        self.download_button.clicked.connect(self.start_download)

    def select_download_directory(self):
        """Opens a dialog to select the download directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.download_dir_input.setText(directory)

    def start_download(self):
        """Starts the download process using aria2c or wget."""
        repo_url = self.repo_url_input.text()
        download_directory = self.download_dir_input.text()

        if not repo_url or not download_directory:
            self.output_text.append("Please provide both repository URL and download directory.")
            return

        #create_download(repo_url, download_directory, self.output_text) <-REMOVED

        downloader = download_manager(repo_url, download_directory, self.output_text) #Instantiate class
        downloader.start_download()



class download_manager(): #Corrected!
    def __init__(self, repo_url, download_directory, output_text): #Corrected!
        self.repo_url = repo_url
        self.download_directory = download_directory
        self.output_text = output_text
    def start_download(self):
      self.download_with_aria2c()

    def download_with_aria2c(self):
        """Downloads files using aria2c."""
        repo_url = self.repo_url
        download_directory = self.download_directory
        output_text = self.output_text
        try:
            command = ["aria2c", repo_url, "-d", download_directory]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output_text.append(output.strip())
                    QApplication.processEvents()  # Keep UI responsive

            return_code = process.returncode
            if return_code == 0:
                output_text.append("Download completed successfully with aria2c.")
            else:
                output_text.append(f"Download failed with aria2c. Return code: {return_code}")

        except Exception as e:
            logger.error(f"Aria2 download error: {e}", exc_info=True)
            output_text.append(f"Error during aria2c download: {e}")
            self.download_with_wget()

    def download_with_wget(self): #Corrected
        """Downloads files using wget."""
        repo_url = self.repo_url
        download_directory = self.download_directory
        output_text = self.output_text

        try:
            command = ["wget", "-r", "-np", "-nH", "--cut-dirs=1", "-P", download_directory, repo_url]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output_text.append(output.strip())
                    QApplication.processEvents()  # Keep UI responsive

            return_code = process.returncode
            if return_code == 0:
                output_text.append("Download completed successfully with wget.")
            else:
                output_text.append(f"Download failed with wget. Return code: {return_code}")

        except Exception as e:
            logger.error(f"Wget download error: {e}", exc_info=True)
            output_text.append(f"Error during wget download: {e}")