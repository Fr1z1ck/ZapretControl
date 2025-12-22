import os
import ctypes
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QCheckBox, QFrame, QPlainTextEdit,
                             QSpacerItem, QSizePolicy, QComboBox, QMessageBox, QDialog,
                             QScrollArea, QGraphicsOpacityEffect, QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QEvent, QUrl, QSize
from PySide6.QtGui import QIcon, QColor, QPalette, QDesktopServices, QPixmap, QPainter
from core.config import config
from utils.paths import get_resource_path
from utils.autostart import set_autostart, is_autostart_enabled

# Set AppUserModelID to show icon in taskbar on Windows
try:
    myappid = 'fr1z1ck.zapretcontrol.manager.1.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Autostart Section
        autostart_card = QFrame()
        autostart_card.setObjectName("card")
        autostart_layout = QVBoxLayout(autostart_card)
        
        self.autostart_cb = QCheckBox("Запускать при старте Windows")
        # Load current state
        self.autostart_cb.setChecked(config.get("autostart", is_autostart_enabled()))
        
        autostart_layout.addWidget(self.autostart_cb)
        layout.addWidget(autostart_card)

        # Updates Section
        updates_card = QFrame()
        updates_card.setObjectName("card")
        updates_layout = QVBoxLayout(updates_card)
        
        updates_title = QLabel("ОБНОВЛЕНИЕ СТРАТЕГИЙ")
        updates_title.setStyleSheet("font-weight: bold; color: #888; font-size: 11px;")
        updates_layout.addWidget(updates_title)
        
        self.update_btn = QPushButton("Проверить обновления")
        self.update_btn.setObjectName("secondary_btn")
        self.update_btn.setIcon(QIcon(get_resource_path(os.path.join('assets', 'icons', 'activity.svg'))))
        self.update_btn.clicked.connect(self.on_check_update_clicked)
        updates_layout.addWidget(self.update_btn)
        
        self.update_status_label = QLabel("Последнее обновление: " + (config.get("last_update_hash")[:7] if config.get("last_update_hash") else "неизвестно"))
        self.update_status_label.setStyleSheet("color: #888; font-size: 11px;")
        updates_layout.addWidget(self.update_status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% (%v/%m)")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 4px;
                text-align: center;
                height: 15px;
                background-color: #1a1a1a;
                color: white;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #3d5afe;
                border-radius: 3px;
            }
        """)
        updates_layout.addWidget(self.progress_bar)
        
        layout.addWidget(updates_card)

        # Actions Section (Reset Icons)
        actions_card = QFrame()
        actions_card.setObjectName("card")
        actions_layout = QVBoxLayout(actions_card)
        
        actions_title = QLabel("ДЕЙСТВИЯ")
        actions_title.setStyleSheet("font-weight: bold; color: #888; font-size: 11px;")
        actions_layout.addWidget(actions_title)
        
        self.reset_btn = QPushButton("Сбросить иконки статуса")
        self.reset_btn.setObjectName("secondary_btn")
        self.reset_btn.setIcon(QIcon(get_resource_path(os.path.join('assets', 'icons', 'settings.svg'))))
        self.reset_btn.clicked.connect(self.on_reset_clicked)
        actions_layout.addWidget(self.reset_btn)
        layout.addWidget(actions_card)

        # About Section
        about_card = QFrame()
        about_card.setObjectName("card")
        about_layout = QVBoxLayout(about_card)
        
        about_title = QLabel("О ПРИЛОЖЕНИИ")
        about_title.setStyleSheet("font-weight: bold; color: #888; font-size: 11px;")
        about_layout.addWidget(about_title)
        
        info_label = QLabel("Zapret Control Manager\nВерсия 1.1.0")
        info_label.setStyleSheet("color: #DDD; font-size: 14px; margin-top: 5px;")
        about_layout.addWidget(info_label)

        author_label = QLabel("Создатель: Fr1z1ck")
        author_label.setStyleSheet("color: #AAA; font-size: 13px; margin-top: 10px;")
        about_layout.addWidget(author_label)

        links_layout = QHBoxLayout()
        
        github_btn = QPushButton("GitHub")
        github_btn.setObjectName("link_btn")
        github_btn.setCursor(Qt.PointingHandCursor)
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/Fr1z1ck")))
        
        telegram_btn = QPushButton("Telegram")
        telegram_btn.setObjectName("link_btn")
        telegram_btn.setCursor(Qt.PointingHandCursor)
        telegram_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://t.me/Fr1z1ck")))
        
        links_layout.addWidget(github_btn)
        links_layout.addWidget(telegram_btn)
        about_layout.addLayout(links_layout)
        
        layout.addWidget(about_card)
        
        layout.addStretch()
        
        # Bottom Buttons
        btns_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setObjectName("toggle_btn")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.on_save_clicked)
        
        close_btn = QPushButton("Отмена")
        close_btn.setObjectName("secondary_btn")
        close_btn.setMinimumHeight(40)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        
        btns_layout.addWidget(close_btn)
        btns_layout.addWidget(self.save_btn)
        layout.addLayout(btns_layout)

    def on_save_clicked(self):
        enabled = self.autostart_cb.isChecked()
        # 1. Update Windows Registry
        success = set_autostart(enabled)
        
        if success:
            # 2. Update config file
            config.set("autostart", enabled)
            QMessageBox.information(self, "Успех", "Настройки успешно сохранены.")
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось обновить настройки автозагрузки в реестре Windows.\nВозможно, требуются права администратора.")

    def on_reset_clicked(self):
        self.parent().controller.reset_health_results()
        self.parent().update_strategies_ui()
        self.parent().update_status()
        QMessageBox.information(self, "Готово", "Иконки статуса сброшены.")

    def on_check_update_clicked(self):
        self.update_btn.setEnabled(False)
        self.update_btn.setText("Проверка...")
        
        # Use WorkerThread to check for updates
        self.check_thread = WorkerThread(self.parent().controller.check_for_updates)
        self.check_thread.finished.connect(self.on_check_finished)
        self.check_thread.start()

    def on_check_finished(self, result, error):
        if error:
            QMessageBox.warning(self, "Ошибка", f"Не удалось проверить обновления: {error}")
            self.update_btn.setEnabled(True)
            self.update_btn.setText("Проверить обновления")
            return

        has_update, latest_hash = result
        if has_update:
            reply = QMessageBox.question(self, "Обновление доступно", 
                                       f"Доступны новые стратегии.\nХотите скачать их сейчас?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.update_btn.setText("Загрузка...")
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                
                self.download_thread = UpdateThread(self.parent().controller, latest_hash)
                self.download_thread.progress.connect(self.on_update_progress)
                self.download_thread.finished.connect(self.on_update_finished)
                self.download_thread.start()
            else:
                self.update_btn.setEnabled(True)
                self.update_btn.setText("Проверить обновления")
        else:
            QMessageBox.information(self, "Обновлений нет", "У вас установлены актуальные версии стратегий.")
            self.update_btn.setEnabled(True)
            self.update_btn.setText("Проверить обновления")

    def on_update_progress(self, current, total, filename):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.update_btn.setText(f"Загрузка: {filename}")

    def on_update_finished(self, success, error):
        self.update_btn.setEnabled(True)
        self.update_btn.setText("Проверить обновления")
        self.progress_bar.setVisible(False)
        if success:
            self.update_status_label.setText("Последнее обновление: " + config.get("last_update_hash")[:7])
            self.parent().update_strategies_ui()
            QMessageBox.information(self, "Успех", "Стратегии успешно обновлены!")
        else:
            QMessageBox.warning(self, "Ошибка", f"Не удалось обновить стратегии: {error}")

class UpdateThread(QThread):
    progress = Signal(int, int, str)
    finished = Signal(bool, str)

    def __init__(self, controller, latest_hash):
        super().__init__()
        self.controller = controller
        self.latest_hash = latest_hash

    def run(self):
        try:
            success = self.controller.update_strategies(self.latest_hash, self.on_progress)
            self.finished.emit(success, "")
        except Exception as e:
            self.finished.emit(False, str(e))

    def on_progress(self, current, total, filename):
        self.progress.emit(current, total, filename)

class WorkerThread(QThread):
    finished = Signal(object, str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result, "")
        except Exception as e:
            self.finished.emit(None, str(e))

class HealthCheckThread(QThread):
    progress = Signal(int, int, str)
    finished = Signal(str) # Change to string to avoid dict conversion issues

    def __init__(self, controller, strategy_index=None):
        super().__init__()
        self.controller = controller
        self.strategy_index = strategy_index

    def run(self):
        # We don't need to return results via signal, they are stored in controller
        self.controller.check_health(self.on_progress, self.strategy_index)
        self.finished.emit("done")

    def on_progress(self, current, total, strategy_name):
        self.progress.emit(current, total, strategy_name)

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Zapret Control")
        self.setWindowIcon(QIcon(get_resource_path(os.path.join('assets', 'app.ico'))))
        self.setMinimumSize(500, 650)
        
        self.init_ui()
        self.load_styles()
        
        # Timer to check status periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)
        
        self.first_hide = True

    def closeEvent(self, event):
        if self.isVisible():
            if self.first_hide:
                self.controller.tray.showMessage(
                    "Zapret Control",
                    "Приложение свернуто в трей и продолжает работать.",
                    QIcon(get_resource_path(os.path.join('assets', 'app.ico'))),
                    3000
                )
                self.first_hide = False
            self.hide()
            event.ignore()

    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Zapret Control Manager")
        self.setMinimumSize(450, 520) # Reduced minimum height from 600
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0) # Reduced margins
        header.setFixedHeight(50) # Reduced height from 60)
        
        title = QLabel("ZAPRET CONTROL")
        title.setObjectName("title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("settings_btn")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        
        icon_path = get_resource_path(os.path.join('assets', 'icons', 'settings.svg'))
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.settings_btn.setIcon(icon)
                self.settings_btn.setIconSize(QSize(20, 20))
            else:
                self.settings_btn.setText("⚙")
                self.settings_btn.setStyleSheet("font-size: 18px; color: white;")
        else:
            self.settings_btn.setText("⚙")
            self.settings_btn.setStyleSheet("font-size: 18px; color: white;")
            
        self.settings_btn.clicked.connect(self.show_settings)
        header_layout.addWidget(self.settings_btn)
        
        main_layout.addWidget(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setContentsMargins(10, 10, 10, 10) # Reduced margins from 15
        self.content_layout.setSpacing(10) # Reduced spacing from 12
        
        # 2. Strategy Card
        strategy_card = QFrame()
        strategy_card.setObjectName("strategy_card")
        strategy_layout = QVBoxLayout(strategy_card)
        strategy_layout.setContentsMargins(12, 12, 12, 12) # Reduced margins from 15
        strategy_layout.setSpacing(10)
        
        card_title = QLabel("ВЫБОР СТРАТЕГИИ")
        card_title.setObjectName("card_title")
        strategy_layout.addWidget(card_title)
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.currentIndexChanged.connect(self.on_strategy_changed)
        self.strategy_combo.setIconSize(QSize(40, 20)) # Space for two icons
        strategy_layout.addWidget(self.strategy_combo)
        
        # Action Buttons for Strategy
        btns_layout = QHBoxLayout()
        
        self.health_btn = QPushButton("Проверить всё")
        self.health_btn.setObjectName("secondary_btn")
        self.health_btn.setIcon(QIcon(get_resource_path(os.path.join('assets', 'icons', 'activity.svg'))))
        self.health_btn.setCursor(Qt.PointingHandCursor)
        self.health_btn.clicked.connect(lambda: self.on_health_check_clicked(True))
        
        self.check_one_btn = QPushButton("Проверить")
        self.check_one_btn.setObjectName("secondary_btn")
        self.check_one_btn.setIcon(QIcon(get_resource_path(os.path.join('assets', 'icons', 'check.svg'))))
        self.check_one_btn.setCursor(Qt.PointingHandCursor)
        self.check_one_btn.clicked.connect(lambda: self.on_health_check_clicked(False))
        
        btns_layout.addWidget(self.health_btn)
        btns_layout.addWidget(self.check_one_btn)
        strategy_layout.addLayout(btns_layout)
        
        self.content_layout.addWidget(strategy_card)

        # 3. Main Toggle Button
        self.toggle_btn = QPushButton("ВКЛЮЧИТЬ ОБХОД")
        self.toggle_btn.setObjectName("toggle_btn")
        self.toggle_btn.setMinimumHeight(45) # Reduced height from 50
        self.toggle_btn.setIcon(QIcon(get_resource_path(os.path.join('assets', 'icons', 'play.svg'))))
        self.toggle_btn.setIconSize(QSize(18, 18))
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.on_toggle_clicked)
        self.content_layout.addWidget(self.toggle_btn)

        # 4. Status Panel
        status_panel = QFrame()
        status_panel.setObjectName("status_panel")
        status_layout = QHBoxLayout(status_panel)
        status_layout.setContentsMargins(12, 8, 12, 8) # Reduced margins
        
        self.status_dot = QFrame()
        self.status_dot.setObjectName("status_dot")
        self.status_dot.setFixedSize(6, 6) # Smaller dot from 8
        status_layout.addWidget(self.status_dot)
        
        self.status_indicator = QLabel("СТАТУС: ВЫКЛЮЧЕНО")
        self.status_indicator.setStyleSheet("color: #8F95B2; font-weight: 700; font-size: 10px;") # Smaller font from 11
        status_layout.addWidget(self.status_indicator)
        
        status_layout.addStretch()
        
        self.content_layout.addWidget(status_panel)

        # 5. Log Area
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(70) # Reduced height from 80
        self.log_view.setPlaceholderText("Логи приложения появятся здесь...")
        self.log_view.setStyleSheet("font-size: 11px;")
        self.content_layout.addWidget(self.log_view)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        self.update_strategies_ui()
        self.update_status()

    def load_styles(self):
        style_path = get_resource_path(os.path.join('ui', 'styles.qss'))
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                style = f.read()
                # Update relative paths for SVG icons in QSS
                check_icon_path = get_resource_path(os.path.join('assets', 'icons', 'check.svg')).replace('\\', '/')
                style = style.replace('url(assets/icons/check.svg)', f'url({check_icon_path})')
                self.setStyleSheet(style)

    def log(self, message):
        self.log_view.appendPlainText(message)

    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def on_toggle_clicked(self):
        self.toggle_btn.setEnabled(False)
        if not self.controller.is_active:
            self.log("Запуск обхода...")
            self.worker = WorkerThread(self.controller.start)
        else:
            self.log("Остановка обхода...")
            self.worker = WorkerThread(self.controller.stop)
        
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.start()

    def on_operation_finished(self, success, error):
        self.toggle_btn.setEnabled(True)
        if not success and error:
            self.log(f"Ошибка: {error}")
        self.update_status()

    def update_strategies_ui(self):
        self.strategy_combo.blockSignals(True)
        current_idx = self.strategy_combo.currentIndex()
        self.strategy_combo.clear()
        
        # Load PNG icons
        yt_path = get_resource_path(os.path.join('assets', 'icons', 'Youtube.png'))
        dc_path = get_resource_path(os.path.join('assets', 'icons', 'Discord.png'))
        
        yt_pix = QPixmap(yt_path) if os.path.exists(yt_path) else None
        dc_pix = QPixmap(dc_path) if os.path.exists(dc_path) else None
        
        for i, strategy in enumerate(self.controller.strategies):
            text = strategy.name
            health = self.controller.health_results.get(strategy.name)
            
            # Use data to store original description
            self.strategy_combo.addItem(text, strategy.description)
            
            if health:
                is_yt = health.get("youtube")
                is_dc = health.get("discord")
                
                if (is_yt and yt_pix) or (is_dc and dc_pix):
                    # Create a composite icon for both YouTube and Discord status
                    composite = QPixmap(40, 18)
                    composite.fill(Qt.transparent)
                    painter = QPainter(composite)
                    
                    x = 0
                    if is_yt and yt_pix:
                        painter.drawPixmap(0, 0, 18, 18, yt_pix)
                        x += 20
                    if is_dc and dc_pix:
                        painter.drawPixmap(x, 0, 18, 18, dc_pix)
                    
                    painter.end()
                    self.strategy_combo.setItemIcon(i, QIcon(composite))
        
        # Restore last used strategy if possible
        if current_idx < 0:
            # Try to restore from config
            last_name = config.get("last_strategy")
            for idx, s in enumerate(self.controller.strategies):
                if s.name == last_name:
                    current_idx = idx
                    break
        
        if current_idx >= 0:
            self.strategy_combo.setCurrentIndex(current_idx)
        else:
            self.strategy_combo.setCurrentIndex(0)
            
        self.strategy_combo.blockSignals(False)
        self.update_strategy_tooltip()

    def on_health_check_clicked(self, check_all=True):
        self.health_btn.setEnabled(False)
        self.check_one_btn.setEnabled(False)
        self.toggle_btn.setEnabled(False)
        
        strategy_index = None if check_all else self.strategy_combo.currentIndex()
        if strategy_index is not None:
            strategy_name = self.controller.strategies[strategy_index].name
            self.log(f"Проверка выбранной стратегии: {strategy_name}...")
        else:
            self.log("Начало проверки всех стратегий...")
        
        self.health_thread = HealthCheckThread(self.controller, strategy_index)
        self.health_thread.progress.connect(self.on_health_progress)
        self.health_thread.finished.connect(self.on_health_finished)
        self.health_thread.start()

    def on_health_progress(self, current, total, strategy_name):
        self.log(f"[{current+1}/{total}] Проверка: {strategy_name}")

    def on_health_finished(self, status):
        self.health_btn.setEnabled(True)
        self.check_one_btn.setEnabled(True)
        self.toggle_btn.setEnabled(True)
        self.log("Проверка завершена.")
        
        self.update_strategies_ui()
        self.update_status()
        
        # Use simple string for message to prevent conversion errors
        QMessageBox.information(self, "Проверка завершена", 
                              "Проверка стратегий на YouTube и Discord окончена.")

    def on_strategy_changed(self, index):
        self.controller.set_strategy(index)
        strategy_name = self.controller.strategies[index].name
        self.log(f"Выбран метод: {strategy_name}")
        self.update_strategy_tooltip()

    def update_strategy_tooltip(self):
        index = self.strategy_combo.currentIndex()
        if index >= 0:
            description = self.strategy_combo.itemData(index)
            self.strategy_combo.setToolTip(description)

    def update_status(self):
        """Updates the UI based on current controller state."""
        active = self.controller.is_active
        
        # Update Toggle Button
        if active:
            self.toggle_btn.setText("ОСТАНОВИТЬ ОБХОД")
            self.toggle_btn.setProperty("active", "true")
            icon_path = get_resource_path(os.path.join('assets', 'icons', 'stop.svg'))
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.toggle_btn.setIcon(icon)
            else:
                self.toggle_btn.setText("■ ОСТАНОВИТЬ")
                
            self.status_indicator.setText("СТАТУС: ЗАПУЩЕНО")
            self.status_indicator.setStyleSheet("color: #00C853; font-weight: 700; font-size: 12px;")
            self.status_dot.setProperty("status", "active")
        else:
            self.toggle_btn.setText("ВКЛЮЧИТЬ ОБХОД")
            self.toggle_btn.setProperty("active", "false")
            icon_path = get_resource_path(os.path.join('assets', 'icons', 'play.svg'))
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.toggle_btn.setIcon(icon)
            else:
                self.toggle_btn.setText("▶ ВКЛЮЧИТЬ")
                
            self.status_indicator.setText("СТАТУС: ВЫКЛЮЧЕНО")
            self.status_indicator.setStyleSheet("color: #8F95B2; font-weight: 700; font-size: 12px;")
            self.status_dot.setProperty("status", "off")
            
        # Refresh styles to apply property changes
        self.toggle_btn.style().unpolish(self.toggle_btn)
        self.toggle_btn.style().polish(self.toggle_btn)
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)
