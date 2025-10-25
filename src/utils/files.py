import os
import shutil

def clear_temp_folder():
    """Deletes all contents of the 'temp' folder located in CURRENT_DIR\src\temp."""
    current_dir = os.getcwd()  # Get the current working directory
    temp_folder_path = os.path.join(current_dir, "src", "temp")  # Path to the temp folder

    os.makedirs(temp_folder_path, exist_ok=True)
    
    if not os.path.exists(temp_folder_path):
        raise FileNotFoundError(f"The 'temp' folder does not exist at {temp_folder_path}.")
    if not os.path.isdir(temp_folder_path):
        raise NotADirectoryError(f"'{temp_folder_path}' is not a directory.")
    
    # Iterate over the contents of the temp folder and delete them
    for item in os.listdir(temp_folder_path):
        item_path = os.path.join(temp_folder_path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)  # Delete files and symlinks
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Delete subdirectories and their contents
        except Exception as e:
            print(f"Error deleting {item_path}: {e}")