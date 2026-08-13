import os

# Default working directory (can be changed at runtime)
WORKING_DIR = os.getcwd()

# Folder you want as default
folder_path = r"C:\Users\rasan\Desktop\work"

# Try to set it at startup
if os.path.isdir(folder_path):
    WORKING_DIR = folder_path

def set_working_dir(new_path: str):
    global WORKING_DIR
    if os.path.isdir(new_path):
        WORKING_DIR = new_path
        return True
    else:
        return False

def get_working_dir() -> str:
    return WORKING_DIR
