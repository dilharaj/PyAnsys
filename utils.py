import os


def remove_file(fname):  
    try:
        os.remove(fname)
    except FileNotFoundError:
        print(f"File: {fname} not found. Skipping deletion")
    except PermissionError:
        print(f"File: {fname} is in use and cannot be deleted.")