from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from utils.paths import get_resource_path
import os

class TrayIcon(QSystemTrayIcon):
    def __init__(self, window, controller):
        super().__init__(window)
        self.window = window
        self.controller = controller
        
        # Load icon (using a placeholder if not found)
        icon_path = get_resource_path(os.path.join('assets', 'app.ico'))
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            # Fallback to a standard icon if our custom one isn't ready
            self.setIcon(window.style().standardIcon(window.style().SP_ComputerIcon))

        self.setToolTip("Zapret Control")
        self.init_menu()
        self.activated.connect(self.on_activated)

    def init_menu(self):
        menu = QMenu()
        
        self.toggle_action = QAction("Включить", self)
        self.toggle_action.triggered.connect(self.on_toggle_triggered)
        menu.addAction(self.toggle_action)
        
        menu.addSeparator()
        
        show_action = QAction("Показать окно", self)
        show_action.triggered.connect(self.window.showNormal)
        menu.addAction(show_action)
        
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.on_quit)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)

    def on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.window.isVisible():
                self.window.hide()
            else:
                self.window.showNormal()
                self.window.activateWindow()

    def on_toggle_triggered(self):
        if self.controller.is_active:
            self.controller.stop()
        else:
            self.controller.start()
        self.update_menu()

    def update_menu(self):
        if self.controller.is_active:
            self.toggle_action.setText("Остановить")
        else:
            self.toggle_action.setText("Включить")

    def on_quit(self):
        self.controller.stop()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
