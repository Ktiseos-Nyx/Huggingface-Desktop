import os
from datetime import datetime


def get_files_by_extension(directory, extension):
    """Returns a list of files in a directory with a specific extension."""
    files = []
    for filename in os.listdir(directory):
        if filename.endswith(f".{extension}"):
            files.append(os.path.join(directory, filename))
    return files


def sort_files_by_date(files):
    """Sorts a list of files by last modified date (most recent first)."""
    return sorted(files, key=os.path.getmtime, reverse=True)


def sort_files_by_name(files):
    """Sorts a list of files by name alphabetically."""
    return sorted(files)
