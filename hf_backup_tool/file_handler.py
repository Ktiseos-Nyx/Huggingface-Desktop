# hf_backup_tool/utils/file_handler.py
# Provides utility functions for file operations.
import os
import shutil
import logging

logger = logging.getLogger(__name__)


def create_directory(path):
    """Creates a directory if it doesn't exist."""
    try:
        os.makedirs(path, exist_ok=True)
        logger.info(f"Directory created/already exists: {path}")
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}", exc_info=True)
        return False  # Indicate failure
    return True  # Indicate success


def remove_directory(path):
    """Removes a directory and its contents."""
    try:
        shutil.rmtree(path, ignore_errors=True)
        logger.info(f"Directory removed (if it existed): {path}")
    except Exception as e:
        logger.error(f"Error removing directory {path}: {e}", exc_info=True)
