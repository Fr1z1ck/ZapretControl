import os
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    # 1. Check if running as a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Path to the temp folder where files are extracted
        base_path = sys._MEIPASS
        
        # Check if the resource exists in the temp folder
        packed_path = os.path.join(base_path, relative_path)
        if os.path.exists(packed_path):
            return packed_path
            
        # Fallback: Check if it's next to the executable
        exe_dir = os.path.dirname(sys.executable)
        external_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(external_path):
            return external_path
            
        return packed_path # Default to temp folder path
    else:
        # Development mode
        # Get the root directory of the project (one level up from utils/)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
