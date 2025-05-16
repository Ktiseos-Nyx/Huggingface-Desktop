import subprocess
import logging
import os

logger = logging.getLogger(__name__)

def is_git_lfs_installed():
    """Checks if git-lfs is installed."""
    try:
        subprocess.run(["git", "lfs", "version"], check=True, capture_output=True)
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git LFS is installed, but gave an error: {e}")
        return True

def init_git_lfs(project_path):
    """Initializes Git LFS in the specified project directory."""
    try:
        if not is_git_lfs_installed():
            logger.error("Git LFS is not installed. Please install it.")
            return False

        subprocess.run(["git", "lfs", "install"], cwd=project_path, check=True, capture_output=True)
        logger.info("Git LFS initialized successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error initializing Git LFS: {e.stderr.decode()}")
        return False

def track_files(project_path, file_patterns):
    """Tracks files with Git LFS using the specified patterns."""
    try:
        for pattern in file_patterns:
            subprocess.run(["git", "lfs", "track", pattern], cwd=project_path, check=True, capture_output=True)
            logger.info(f"Tracked pattern: {pattern}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error tracking files with Git LFS: {e.stderr.decode()}")
        return False

def add_gitattributes(project_path):
    """Adds the .gitattributes file to the staging area."""
    try:
        subprocess.run(["git", "add", ".gitattributes"], cwd=project_path, check=True, capture_output=True)
        logger.info("Added .gitattributes to staging area.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error adding .gitattributes: {e.stderr.decode()}")
        return False