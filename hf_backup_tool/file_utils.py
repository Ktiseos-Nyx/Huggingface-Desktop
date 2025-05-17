import os

def get_files_by_extension(directory, extension):
    files = []
    for filename in os.listdir(directory):
        if filename.endswith(f".{extension}"):
            files.append(os.path.join(directory, filename))
    return files

def sort_files_by_date(files):
    return sorted(files, key=os.path.getmtime, reverse=True)

def sort_files_by_name(files):
    return sorted(files)
