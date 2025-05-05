import logging
import os
import subprocess

from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


def create_download(repo_url, download_directory, output_text_widget):
    """Downloads files using aria2c or wget."""
    if is_aria2_available():
        download_with_aria2(repo_url, download_directory, output_text_widget)
    else:
        download_with_wget(repo_url, download_directory, output_text_widget)


def is_aria2_available():
    """Checks if aria2c is installed and available in the system."""
    try:
        subprocess.run(["aria2c", "--version"], check=False, capture_output=True)
        return True
    except FileNotFoundError:
        return False


def download_with_aria2(repo_url, download_directory, output_text_widget):
    """Downloads files using aria2c."""
    try:
        command = ["aria2c", repo_url, "-d", download_directory]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output_text_widget.append(output.strip())
                QApplication.processEvents()  # Keep UI responsive

        return_code = process.returncode
        if return_code == 0:
            output_text_widget.append("Download completed successfully with aria2c.")
        else:
            output_text_widget.append(f"Download failed with aria2c. Return code: {return_code}")

    except Exception as e:
        logger.error(f"Aria2 download error: {e}", exc_info=True)
        output_text_widget.append(f"Error during aria2c download: {e}")


def download_with_wget(repo_url, download_directory, output_text_widget):
    """Downloads files using wget."""
    try:
        command = ["wget", "-r", "-np", "-nH", "--cut-dirs=1", "-P", download_directory, repo_url]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output_text_widget.append(output.strip())
                QApplication.processEvents()  # Keep UI responsive

            return_code = process.returncode
            if return_code == 0:
                output_text_widget.append("Download completed successfully with wget.")
            else:
                output_text_widget.append(f"Download failed with wget. Return code: {return_code}")

        except Exception as e:
            logger.error(f"Wget download error: {e}", exc_info=True)
            output_text_widget.append(f"Error during wget download: {e}")
