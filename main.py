import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from ui.tray import TrayIcon
from core.controller import AppController
from utils.admin import is_admin, run_as_admin
from utils.logger import logger
import socket

# Global socket to prevent multiple instances
_instance_lock = None

def is_already_running():
    global _instance_lock
    try:
        _instance_lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind to a specific port that we'll use as a "lock"
        _instance_lock.bind(('127.0.0.1', 47231))
        return False
    except socket.error:
        return True

def main():
    # 1. Admin Check
    if not is_admin():
        logger.info("Requesting admin privileges...")
        # This function will call sys.exit(0) if it succeeds in starting the elevated process
        if not run_as_admin():
            logger.warning("Admin privileges denied by user.")
            # We continue anyway, but winws will likely fail later
            pass

    # 2. Single Instance Check (After Admin elevation)
    if is_already_running():
        # Just exit quietly if another instance is running
        sys.exit(0)

    # 2. Initialize App
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Keep running in tray

    # 3. Setup Controller
    base_path = os.path.dirname(os.path.abspath(__file__))
    controller = AppController(base_path)

    # 4. Create UI
    window = MainWindow(controller)
    tray = TrayIcon(window, controller)
    controller.tray = tray # Store tray reference in controller
    
    # 5. Show Window
    window.show()
    tray.show()

    # 6. Run Event Loop
    logger.info("Application started.")
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        # Show error message box if possible
        try:
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Произошла критическая ошибка")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Ошибка")
            msg.exec()
        except:
            pass
        sys.exit(1)
