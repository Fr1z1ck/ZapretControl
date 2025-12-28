import ctypes
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if is_admin():
        return True
    
    # Try to re-run with admin rights
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    
    # If the process was successfully started (or at least the attempt was made), 
    # we MUST exit the current non-elevated process.
    if ret > 32:
        sys.exit(0)
    
    return False
