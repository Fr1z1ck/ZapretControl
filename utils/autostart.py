import winreg
import os
import sys

def set_autostart(enabled=True):
    """Adds/Removes the application from Windows autostart (Registry)."""
    app_name = "ZapretControl"
    # Get the path to the executable or the python script
    if getattr(sys, 'frozen', False):
        # If running as a compiled exe
        app_path = sys.executable
    else:
        # If running as a script (for development)
        app_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass # Already deleted
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error setting autostart: {e}")
        return False

def is_autostart_enabled():
    """Checks if the application is in Windows autostart."""
    app_name = "ZapretControl"
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False
