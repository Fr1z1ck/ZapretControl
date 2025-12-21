import customtkinter as ctk
import subprocess
import os
import sys
import threading
import re
from pathlib import Path
from tkinter import messagebox, scrolledtext
import json
import tempfile
import urllib.request
import urllib.error
import socket
from datetime import datetime

# Настройка темы - современный дизайн
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Кастомные цвета для современного дизайна
COLORS = {
    'primary': '#1a73e8',
    'primary_hover': '#1557b0',
    'success': '#34a853',
    'success_hover': '#2d8f47',
    'warning': '#fbbc04',
    'warning_hover': '#d9a003',
    'danger': '#ea4335',
    'danger_hover': '#c5221f',
    'info': '#4285f4',
    'info_hover': '#3367d6',
    'bg_card': '#1e1e1e',
    'bg_secondary': '#2d2d2d',
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0b0',
    'border': '#3d3d3d'
}

class ModernCard(ctk.CTkFrame):
    """Современная карточка с тенью и скругленными углами"""
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            corner_radius=12,
            border_width=1,
            border_color=COLORS['border'],
            fg_color=COLORS['bg_card'],
            **kwargs
        )

class ZapretGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Zapret - DPI Bypass Control Panel")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Получаем путь к директории скрипта (работает и в exe, и в скрипте)
        if getattr(sys, 'frozen', False):
            # Если запущено как exe (PyInstaller)
            if hasattr(sys, '_MEIPASS'):
                # Временная директория PyInstaller
                self.temp_dir = Path(sys._MEIPASS)
            else:
                self.temp_dir = Path(sys.executable).parent
            # Директория где находится exe
            self.script_dir = Path(sys.executable).parent.absolute()
        else:
            # Если запущено как скрипт
            self.script_dir = Path(__file__).parent.absolute()
            self.temp_dir = self.script_dir
        
        # Инициализируем пути к данным
        self.bin_path = self.script_dir / "bin"
        self.lists_path = self.script_dir / "lists"
        self.service_bat = self.script_dir / "service.bat"
        
        # Если запущено как exe, распаковываем данные при первом запуске
        if getattr(sys, 'frozen', False):
            self.extract_embedded_data()
        
        # Переменные состояния
        self.game_filter_enabled = False
        self.ipset_status = "any"
        self.service_running = False
        
        # Проверка работоспособности YouTube
        self.youtube_status = None
        self.last_youtube_check = None
        
        # Процессы для отслеживания
        self.current_winws_process = None
        
        # Автоматическая проверка
        self.auto_check_enabled = False
        self.auto_check_thread = None
        self.auto_check_interval_seconds = 60
        
        # Файл настроек
        self.settings_file = self.script_dir / "zapret_settings.json"
        
        # Статистика трафика
        self.traffic_stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'connections': 0,
            'start_time': None
        }
        self.traffic_monitor_thread = None
        self.traffic_monitor_enabled = False
        
        # Проверка прав администратора
        self.is_admin = self.check_admin()
        if not self.is_admin:
            self.root.after(0, self.request_admin_restart)
        
        self.create_widgets()
        self.setup_hotkeys()
        self.update_admin_status()
        self.update_status()
        self.load_settings()
        # Запускаем проверку работоспособности при старте
        self.check_youtube_now()
        # Запускаем мониторинг трафика
        self.start_traffic_monitor()
        # Автозапуск последнего bypass если включен
        self.auto_start_last_bypass()
        
    def create_widgets(self):
        """Создает полностью переработанный современный интерфейс"""
        # Главный контейнер
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Современный заголовок
        self.create_modern_header(main_container)
        
        # Основной контент с боковой панелью
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(15, 0))
        
        # Боковая панель навигации
        self.create_sidebar(content_frame)
        
        # Область контента
        self.content_area = ctk.CTkFrame(content_frame, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True, padx=(15, 0))
        
        # Создаем страницы
        self.pages = {}
        self.create_dashboard_page()
        self.create_control_page()
        self.create_status_page()
        self.create_settings_page()
        self.create_traffic_page()
        self.create_console_page()
        
        # Показываем главную страницу
        self.show_page('dashboard')
        
        # Нижняя панель статуса
        self.create_status_bar(main_container)
    
    def create_modern_header(self, parent):
        """Создает современный заголовок"""
        header = ModernCard(parent)
        header.pack(fill="x", pady=(0, 15))
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=20, pady=15)
        
        # Левая часть - логотип и название
        left_header = ctk.CTkFrame(header_content, fg_color="transparent")
        left_header.pack(side="left")
        
        logo_label = ctk.CTkLabel(
            left_header,
            text="🔒",
            font=ctk.CTkFont(size=40)
        )
        logo_label.pack(side="left", padx=(0, 15))
        
        title_frame = ctk.CTkFrame(left_header, fg_color="transparent")
        title_frame.pack(side="left")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Zapret DPI Bypass",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS['primary']
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Control Panel v2.0",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        subtitle_label.pack(anchor="w")
        
        # Правая часть - статус и кнопки
        right_header = ctk.CTkFrame(header_content, fg_color="transparent")
        right_header.pack(side="right")
        
        self.admin_status_label = ctk.CTkLabel(
            right_header,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['success']
        )
        self.admin_status_label.pack(side="right", padx=(0, 15))
        
        help_btn = ctk.CTkButton(
            right_header,
            text="⌨️ Горячие клавиши",
            command=self.show_hotkeys_help,
            width=140,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_secondary'],
            hover_color=COLORS['border'],
            corner_radius=8
        )
        help_btn.pack(side="right", padx=(0, 10))
    
    def create_sidebar(self, parent):
        """Создает современную боковую панель навигации"""
        sidebar = ModernCard(parent, width=220)
        sidebar.pack(side="left", fill="y", padx=(0, 15))
        
        nav_content = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_content.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Заголовок навигации
        nav_title = ctk.CTkLabel(
            nav_content,
            text="Навигация",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_secondary']
        )
        nav_title.pack(pady=(0, 15))
        
        # Кнопки навигации
        self.nav_buttons = {}
        nav_items = [
            ('dashboard', '📊', 'Главная', 'Обзор системы'),
            ('control', '⚙️', 'Управление', 'Конфигурации и службы'),
            ('status', '📈', 'Статус', 'Мониторинг работы'),
            ('settings', '🔧', 'Настройки', 'Параметры приложения'),
            ('traffic', '📡', 'Трафик', 'Статистика сети'),
            ('console', '💻', 'Консоль', 'Логи и вывод')
        ]
        
        for page_id, icon, title, desc in nav_items:
            btn_frame = ctk.CTkFrame(nav_content, fg_color="transparent")
            btn_frame.pack(fill="x", pady=3)
            
            btn = ctk.CTkButton(
                btn_frame,
                text=f"{icon} {title}",
                command=lambda p=page_id: self.show_page(p),
                height=50,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=COLORS['bg_secondary'],
                hover_color=COLORS['border'],
                corner_radius=10,
                anchor="w",
                text_color=COLORS['text_primary']
            )
            btn.pack(fill="x")
            
            desc_label = ctk.CTkLabel(
                btn_frame,
                text=desc,
                font=ctk.CTkFont(size=10),
                text_color=COLORS['text_secondary']
            )
            desc_label.pack(anchor="w", padx=(15, 0), pady=(2, 0))
            
            self.nav_buttons[page_id] = btn
    
    def show_page(self, page_id):
        """Показывает выбранную страницу"""
        # Скрываем все страницы
        for page in self.pages.values():
            page.pack_forget()
        
        # Показываем выбранную
        if page_id in self.pages:
            self.pages[page_id].pack(fill="both", expand=True)
        
        # Обновляем активную кнопку навигации
        for nav_id, btn in self.nav_buttons.items():
            if nav_id == page_id:
                btn.configure(fg_color=COLORS['primary'], hover_color=COLORS['primary_hover'])
            else:
                btn.configure(fg_color=COLORS['bg_secondary'], hover_color=COLORS['border'])
    
    def create_status_bar(self, parent):
        """Создает нижнюю панель статуса"""
        status_bar = ModernCard(parent, height=40)
        status_bar.pack(fill="x", pady=(15, 0))
        
        status_content = ctk.CTkFrame(status_bar, fg_color="transparent")
        status_content.pack(fill="x", padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(
            status_content,
            text="Готов",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left")
    
    def create_dashboard_page(self):
        """Создает главную страницу с обзором"""
        page = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.pages['dashboard'] = page
        
        # Заголовок страницы
        page_header = ctk.CTkLabel(
            page,
            text="📊 Обзор системы",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        page_header.pack(anchor="w", pady=(0, 20))
        
        # Карточки статуса
        status_cards_frame = ctk.CTkFrame(page, fg_color="transparent")
        status_cards_frame.pack(fill="x", pady=(0, 20))
        
        # Карточка службы
        service_card = ModernCard(status_cards_frame)
        service_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.create_status_card(service_card, "Служба Zapret", "Проверка...", "service")
        
        # Карточка Bypass
        bypass_card = ModernCard(status_cards_frame)
        bypass_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.create_status_card(bypass_card, "Bypass (winws.exe)", "Проверка...", "bypass")
        
        # Карточка YouTube/Discord
        services_card = ModernCard(status_cards_frame)
        services_card.pack(side="left", fill="both", expand=True)
        self.create_status_card(services_card, "Доступность сервисов", "Проверка...", "services")
        
        # Быстрые действия
        quick_actions_frame = ModernCard(page)
        quick_actions_frame.pack(fill="x", pady=(0, 20))
        
        quick_header = ctk.CTkLabel(
            quick_actions_frame,
            text="⚡ Быстрые действия",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        quick_header.pack(anchor="w", padx=20, pady=(20, 15))
        
        actions_grid = ctk.CTkFrame(quick_actions_frame, fg_color="transparent")
        actions_grid.pack(fill="x", padx=20, pady=(0, 20))
        
        # Кнопки быстрых действий
        quick_actions = [
            ("▶️ Запустить", self.run_selected_config, COLORS['success']),
            ("⏸️ Остановить", self.stop_winws, COLORS['warning']),
            ("🔄 Проверить", self.check_youtube_now, COLORS['info']),
            ("🔍 Найти рабочий", self.find_working_bypass, COLORS['primary'])
        ]
        
        for i, (text, command, color) in enumerate(quick_actions):
            btn = ctk.CTkButton(
                actions_grid,
                text=text,
                command=command,
                height=45,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=color,
                hover_color=color,
                corner_radius=10
            )
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
            actions_grid.grid_columnconfigure(i%2, weight=1)
        
        # Последняя конфигурация
        last_config_frame = ModernCard(page)
        last_config_frame.pack(fill="x")
        
        config_header = ctk.CTkLabel(
            last_config_frame,
            text="📋 Последняя конфигурация",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        config_header.pack(anchor="w", padx=20, pady=(20, 15))
        
        self.last_config_label = ctk.CTkLabel(
            last_config_frame,
            text="Не выбрана",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_secondary']
        )
        self.last_config_label.pack(anchor="w", padx=20, pady=(0, 20))
    
    def create_status_card(self, parent, title, status_text, card_type):
        """Создает карточку статуса"""
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            content,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 10))
        
        status_label = ctk.CTkLabel(
            content,
            text=status_text,
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_secondary']
        )
        status_label.pack(anchor="w")
        
        # Сохраняем ссылки на метки
        if card_type == "service":
            self.service_status_label = status_label
        elif card_type == "bypass":
            self.winws_status_label = status_label
        elif card_type == "services":
            self.youtube_status_label = status_label
    
    def create_control_page(self):
        """Создает страницу управления - переименованная версия create_service_tab"""
        page = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.pages['control'] = page
        
        # Заголовок
        page_header = ctk.CTkLabel(
            page,
            text="⚙️ Управление конфигурациями",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        page_header.pack(anchor="w", pady=(0, 20))
        
        # Две колонки
        columns_frame = ctk.CTkFrame(page, fg_color="transparent")
        columns_frame.pack(fill="both", expand=True)
        
        # Левая колонка - управление службой
        left_col = ModernCard(columns_frame, width=300)
        left_col.pack(side="left", fill="y", padx=(0, 15))
        
        service_header = ctk.CTkLabel(
            left_col,
            text="🔧 Управление службой",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        service_header.pack(pady=(20, 15), padx=20)
        
        service_buttons = ctk.CTkFrame(left_col, fg_color="transparent")
        service_buttons.pack(fill="x", padx=20, pady=(0, 20))
        
        self.install_btn = self.create_action_button(
            service_buttons, "📥 Установить службу", self.install_service, COLORS['info']
        )
        self.remove_btn = self.create_action_button(
            service_buttons, "🗑️ Удалить службу", self.remove_service, COLORS['danger']
        )
        self.start_btn = self.create_action_button(
            service_buttons, "▶️ Запустить", self.start_service, COLORS['success']
        )
        self.stop_btn = self.create_action_button(
            service_buttons, "⏸️ Остановить", self.stop_service, COLORS['warning']
        )
        self.refresh_btn = self.create_action_button(
            service_buttons, "🔄 Обновить", self.update_status, COLORS['bg_secondary']
        )
        
        # Правая колонка - конфигурации
        right_col = ModernCard(columns_frame)
        right_col.pack(side="right", fill="both", expand=True)
        
        config_header = ctk.CTkLabel(
            right_col,
            text="📋 Выбор конфигурации",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        config_header.pack(pady=(20, 15), padx=20)
        
        # Список конфигураций
        self.config_scroll_frame = ctk.CTkScrollableFrame(right_col, height=400)
        self.config_scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        self.config_var = ctk.StringVar(value="")
        self.config_radio_buttons = []
        self.config_status_labels = {}
        
        self.load_configurations(self.config_scroll_frame)
        
        # Кнопки управления конфигурациями
        config_actions = ctk.CTkFrame(right_col, fg_color="transparent")
        config_actions.pack(fill="x", padx=20, pady=(0, 20))
        
        self.run_config_btn = ctk.CTkButton(
            config_actions,
            text="▶️ Запустить выбранную",
            command=self.run_selected_config,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['success_hover'],
            corner_radius=10
        )
        self.run_config_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.find_working_btn = ctk.CTkButton(
            config_actions,
            text="🔍 Найти рабочий",
            command=self.find_working_bypass,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            corner_radius=10
        )
        self.find_working_btn.pack(side="left", fill="x", expand=True)
        
        self.find_progress_label = ctk.CTkLabel(
            right_col,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        self.find_progress_label.pack(pady=(0, 20))
    
    def create_status_page(self):
        """Создает страницу статуса"""
        page = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.pages['status'] = page
        
        page_header = ctk.CTkLabel(
            page,
            text="📈 Статус и мониторинг",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        page_header.pack(anchor="w", pady=(0, 20))
        
        # Карточки статуса
        status_grid = ctk.CTkFrame(page, fg_color="transparent")
        status_grid.pack(fill="both", expand=True)
        
        # Карточка службы
        service_card = ModernCard(status_grid)
        service_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.create_detailed_status_card(service_card, "Служба Zapret", "service")
        
        # Карточка Bypass
        bypass_card = ModernCard(status_grid)
        bypass_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.create_detailed_status_card(bypass_card, "Bypass (winws.exe)", "bypass")
        
        # Карточка сервисов
        services_card = ModernCard(status_grid)
        services_card.pack(side="left", fill="both", expand=True)
        self.create_detailed_status_card(services_card, "Доступность сервисов", "services")
        
        # Информация
        info_card = ModernCard(page)
        info_card.pack(fill="x", pady=(20, 0))
        
        info_header = ctk.CTkLabel(
            info_card,
            text="ℹ️ Информация",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        info_header.pack(anchor="w", padx=20, pady=(20, 15))
        
        self.info_text = ctk.CTkTextbox(info_card, height=150, corner_radius=10)
        self.info_text.pack(fill="x", padx=20, pady=(0, 20))
        
        # Кнопка проверки и индикаторы
        check_btn_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        check_btn_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.youtube_check_btn = ctk.CTkButton(
            check_btn_frame,
            text="🔄 Проверить работоспособность",
            command=self.check_youtube_now,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['info'],
            hover_color=COLORS['info_hover'],
            corner_radius=10
        )
        self.youtube_check_btn.pack(side="left")
        
        # Индикатор и время последней проверки
        status_info_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        status_info_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.youtube_status_indicator = ctk.CTkLabel(
            status_info_frame,
            text="●",
            font=ctk.CTkFont(size=24),
            text_color="gray"
        )
        self.youtube_status_indicator.pack(side="left", padx=(0, 10))
        
        self.youtube_last_check_label = ctk.CTkLabel(
            status_info_frame,
            text="Проверка работоспособности выполняется при запуске приложения",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        self.youtube_last_check_label.pack(side="left")
    
    def create_detailed_status_card(self, parent, title, card_type):
        """Создает детальную карточку статуса"""
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            content,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 15))
        
        status_label = ctk.CTkLabel(
            content,
            text="Проверка...",
            font=ctk.CTkFont(size=16),
            text_color=COLORS['text_secondary']
        )
        status_label.pack(anchor="w")
        
        if card_type == "service":
            self.service_status_label = status_label
        elif card_type == "bypass":
            self.winws_status_label = status_label
        elif card_type == "services":
            self.youtube_status_label = status_label
    
    def create_settings_page(self):
        """Создает страницу настроек с автозапуском"""
        page = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.pages['settings'] = page
        
        page_header = ctk.CTkLabel(
            page,
            text="🔧 Настройки приложения",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        page_header.pack(anchor="w", pady=(0, 20))
        
        # Автозапуск - главная карточка
        autostart_card = ModernCard(page)
        autostart_card.pack(fill="x", pady=(0, 15))
        
        autostart_header = ctk.CTkLabel(
            autostart_card,
            text="🚀 Автозапуск",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        autostart_header.pack(anchor="w", padx=20, pady=(20, 15))
        
        autostart_content = ctk.CTkFrame(autostart_card, fg_color="transparent")
        autostart_content.pack(fill="x", padx=20, pady=(0, 20))
        
        # Приложение при старте Windows
        app_autostart_frame = ctk.CTkFrame(autostart_content, fg_color="transparent")
        app_autostart_frame.pack(fill="x", pady=10)
        
        self.autostart_var = ctk.BooleanVar(value=False)
        autostart_switch = ctk.CTkSwitch(
            app_autostart_frame,
            text="Запускать приложение при старте Windows",
            variable=self.autostart_var,
            command=self.toggle_autostart,
            font=ctk.CTkFont(size=14, weight="bold"),
            onvalue=True,
            offvalue=False
        )
        autostart_switch.pack(side="left")
        
        autostart_desc = ctk.CTkLabel(
            app_autostart_frame,
            text="Приложение будет автоматически запускаться при входе в Windows",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        autostart_desc.pack(side="left", padx=(15, 0))
        
        # Разделитель
        separator = ctk.CTkFrame(autostart_content, height=1, fg_color=COLORS['border'])
        separator.pack(fill="x", pady=15)
        
        # Автозапуск bypass
        bypass_autostart_frame = ctk.CTkFrame(autostart_content, fg_color="transparent")
        bypass_autostart_frame.pack(fill="x", pady=10)
        
        self.auto_start_bypass_var = ctk.BooleanVar(value=False)
        auto_start_bypass_switch = ctk.CTkSwitch(
            bypass_autostart_frame,
            text="Автоматически запускать последний использованный bypass при старте",
            variable=self.auto_start_bypass_var,
            command=self.toggle_auto_start_bypass,
            font=ctk.CTkFont(size=14, weight="bold"),
            onvalue=True,
            offvalue=False
        )
        auto_start_bypass_switch.pack(side="left")
        
        bypass_desc = ctk.CTkLabel(
            bypass_autostart_frame,
            text="Последняя использованная конфигурация будет запущена автоматически",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        bypass_desc.pack(side="left", padx=(15, 0))
        
        # Game Filter
        game_filter_card = ModernCard(page)
        game_filter_card.pack(fill="x", pady=(0, 15))
        
        game_header = ctk.CTkLabel(
            game_filter_card,
            text="🎮 Game Filter",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        game_header.pack(anchor="w", padx=20, pady=(20, 15))
        
        self.game_filter_var = ctk.StringVar(value="disabled")
        game_switch = ctk.CTkSwitch(
            game_filter_card,
            text="Включить Game Filter",
            variable=self.game_filter_var,
            onvalue="enabled",
            offvalue="disabled",
            command=self.toggle_game_filter,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        game_switch.pack(anchor="w", padx=20, pady=(0, 20))
        
        # IPSet
        ipset_card = ModernCard(page)
        ipset_card.pack(fill="x", pady=(0, 15))
        
        ipset_header = ctk.CTkLabel(
            ipset_card,
            text="🌐 IPSet режим",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        ipset_header.pack(anchor="w", padx=20, pady=(20, 15))
        
        self.ipset_var = ctk.StringVar(value="any")
        ipset_menu = ctk.CTkOptionMenu(
            ipset_card,
            values=["any", "none", "loaded"],
            variable=self.ipset_var,
            command=self.change_ipset_mode,
            font=ctk.CTkFont(size=14),
            corner_radius=10
        )
        ipset_menu.pack(anchor="w", padx=20, pady=(0, 10))
        
        update_ipset_btn = ctk.CTkButton(
            ipset_card,
            text="🔄 Обновить IPSet список",
            command=self.update_ipset,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['info'],
            hover_color=COLORS['info_hover'],
            corner_radius=10
        )
        update_ipset_btn.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Автоматическая проверка
        auto_check_card = ModernCard(page)
        auto_check_card.pack(fill="x", pady=(0, 15))
        
        auto_check_header = ctk.CTkLabel(
            auto_check_card,
            text="🔄 Автоматическая проверка",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        auto_check_header.pack(anchor="w", padx=20, pady=(20, 15))
        
        self.auto_check_var = ctk.BooleanVar(value=False)
        self.auto_check_switch = ctk.CTkSwitch(
            auto_check_card,
            text="Включить автоматическую проверку работоспособности",
            variable=self.auto_check_var,
            command=self.toggle_auto_check,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.auto_check_switch.pack(anchor="w", padx=20, pady=(0, 10))
        
        interval_frame = ctk.CTkFrame(auto_check_card, fg_color="transparent")
        interval_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            interval_frame,
            text="Интервал проверки (секунд):",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 10))
        
        self.auto_check_interval_var = ctk.StringVar(value="60")
        self.auto_check_interval = ctk.CTkEntry(
            interval_frame,
            textvariable=self.auto_check_interval_var,
            width=100,
            font=ctk.CTkFont(size=12),
            corner_radius=8
        )
        self.auto_check_interval.pack(side="left")
        
        # Тема оформления
        theme_card = ModernCard(page)
        theme_card.pack(fill="x", pady=(0, 15))
        
        theme_header = ctk.CTkLabel(
            theme_card,
            text="🎨 Тема оформления",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        theme_header.pack(anchor="w", padx=20, pady=(20, 15))
        
        self.theme_var = ctk.StringVar(value="dark")
        theme_menu = ctk.CTkOptionMenu(
            theme_card,
            values=["dark", "light", "system"],
            variable=self.theme_var,
            command=self.change_theme,
            font=ctk.CTkFont(size=14),
            corner_radius=10
        )
        theme_menu.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Экспорт/Импорт
        export_card = ModernCard(page)
        export_card.pack(fill="x")
        
        export_header = ctk.CTkLabel(
            export_card,
            text="💾 Настройки",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        export_header.pack(anchor="w", padx=20, pady=(20, 15))
        
        export_buttons = ctk.CTkFrame(export_card, fg_color="transparent")
        export_buttons.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            export_buttons,
            text="💾 Экспорт настроек",
            command=self.export_settings,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['info'],
            hover_color=COLORS['info_hover'],
            corner_radius=10
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(
            export_buttons,
            text="📥 Импорт настроек",
            command=self.import_settings,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            corner_radius=10
        ).pack(side="left", fill="x", expand=True)
    
    def create_traffic_page(self):
        """Создает страницу мониторинга трафика"""
        page = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.pages['traffic'] = page
        
        page_header = ctk.CTkLabel(
            page,
            text="📡 Мониторинг трафика",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        page_header.pack(anchor="w", pady=(0, 20))
        
        # Управление
        control_card = ModernCard(page)
        control_card.pack(fill="x", pady=(0, 15))
        
        control_content = ctk.CTkFrame(control_card, fg_color="transparent")
        control_content.pack(fill="x", padx=20, pady=20)
        
        self.traffic_monitor_btn = ctk.CTkButton(
            control_content,
            text="▶️ Запустить мониторинг",
            command=self.toggle_traffic_monitor,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['success_hover'],
            corner_radius=10
        )
        self.traffic_monitor_btn.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            control_content,
            text="🔄 Сбросить",
            command=self.reset_traffic_stats,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['bg_secondary'],
            hover_color=COLORS['border'],
            corner_radius=10
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            control_content,
            text="💾 Экспорт",
            command=self.export_traffic_stats,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['info'],
            hover_color=COLORS['info_hover'],
            corner_radius=10
        ).pack(side="left")
        
        # Статистика
        stats_grid = ctk.CTkFrame(page, fg_color="transparent")
        stats_grid.pack(fill="both", expand=True)
        
        # Исходящий трафик
        sent_card = ModernCard(stats_grid)
        sent_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.create_traffic_stat_card(sent_card, "📤 Исходящий трафик", "sent")
        
        # Входящий трафик
        received_card = ModernCard(stats_grid)
        received_card.pack(side="left", fill="both", expand=True)
        self.create_traffic_stat_card(received_card, "📥 Входящий трафик", "received")
        
        # Общая статистика
        total_card = ModernCard(page)
        total_card.pack(fill="x", pady=(15, 0))
        
        total_header = ctk.CTkLabel(
            total_card,
            text="📊 Общая статистика",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        total_header.pack(anchor="w", padx=20, pady=(20, 15))
        
        total_stats = ctk.CTkFrame(total_card, fg_color="transparent")
        total_stats.pack(fill="x", padx=20, pady=(0, 20))
        
        self.total_packets_label = ctk.CTkLabel(
            total_stats,
            text="Всего пакетов: 0",
            font=ctk.CTkFont(size=14)
        )
        self.total_packets_label.pack(side="left", padx=10)
        
        self.total_bytes_label = ctk.CTkLabel(
            total_stats,
            text="Всего байт: 0",
            font=ctk.CTkFont(size=14)
        )
        self.total_bytes_label.pack(side="left", padx=10)
        
        self.connections_label = ctk.CTkLabel(
            total_stats,
            text="Соединений: 0",
            font=ctk.CTkFont(size=14)
        )
        self.connections_label.pack(side="left", padx=10)
        
        self.uptime_label = ctk.CTkLabel(
            total_stats,
            text="Время работы: 00:00:00",
            font=ctk.CTkFont(size=14)
        )
        self.uptime_label.pack(side="left", padx=10)
    
    def create_traffic_stat_card(self, parent, title, stat_type):
        """Создает карточку статистики трафика"""
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            content,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 15))
        
        if stat_type == "sent":
            self.packets_sent_label = ctk.CTkLabel(
                content,
                text="Пакетов отправлено: 0",
                font=ctk.CTkFont(size=14)
            )
            self.packets_sent_label.pack(anchor="w", pady=5)
            
            self.bytes_sent_label = ctk.CTkLabel(
                content,
                text="Байт отправлено: 0",
                font=ctk.CTkFont(size=14)
            )
            self.bytes_sent_label.pack(anchor="w")
        else:
            self.packets_received_label = ctk.CTkLabel(
                content,
                text="Пакетов получено: 0",
                font=ctk.CTkFont(size=14)
            )
            self.packets_received_label.pack(anchor="w", pady=5)
            
            self.bytes_received_label = ctk.CTkLabel(
                content,
                text="Байт получено: 0",
                font=ctk.CTkFont(size=14)
            )
            self.bytes_received_label.pack(anchor="w")
    
    def create_console_page(self):
        """Создает страницу консоли"""
        page = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.pages['console'] = page
        
        page_header = ctk.CTkLabel(
            page,
            text="💻 Консоль и логи",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        page_header.pack(anchor="w", pady=(0, 15))
        
        # Консоль
        console_card = ModernCard(page)
        console_card.pack(fill="both", expand=True)
        
        console_controls = ctk.CTkFrame(console_card, fg_color="transparent")
        console_controls.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkButton(
            console_controls,
            text="🔄 Очистить",
            command=lambda: self.console_text.delete(1.0, "end"),
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_secondary'],
            hover_color=COLORS['border'],
            corner_radius=8
        ).pack(side="left", padx=(0, 10))
        
        self.console_auto_scroll = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            console_controls,
            text="Автопрокрутка",
            variable=self.console_auto_scroll,
            font=ctk.CTkFont(size=12)
        ).pack(side="left")
        
        self.console_text = scrolledtext.ScrolledText(
            console_card,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Consolas", 11),
            wrap="word",
            relief="flat",
            borderwidth=0
        )
        self.console_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.log_to_console("=== Zapret DPI Bypass Control Panel ===\n")
        self.log_to_console("Консоль готова. Логи будут отображаться здесь.\n\n")
    
    def create_action_button(self, parent, text, command, color):
        """Создает кнопку действия"""
        btn = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=color,
            hover_color=color,
            corner_radius=10
        )
        btn.pack(fill="x", pady=5)
        return btn
    
    def create_status_tab(self):
        """Старый метод - больше не используется, заменен на create_status_page"""
        pass
    
    def create_diagnostics_tab(self):
        """Старый метод - больше не используется"""
        pass
    
    def create_old_settings_tab(self):
        """Старый метод - больше не используется, заменен на create_settings_page"""
        pass
    
    def create_settings_tab(self):
        # Game Filter
        game_frame = ctk.CTkFrame(self.settings_tab)
        game_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            game_frame,
            text="Game Filter",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        self.game_filter_var = ctk.StringVar(value="disabled")
        self.game_filter_switch = ctk.CTkSwitch(
            game_frame,
            text="Включить Game Filter",
            variable=self.game_filter_var,
            onvalue="enabled",
            offvalue="disabled",
            command=self.toggle_game_filter,
            font=ctk.CTkFont(size=14)
        )
        self.game_filter_switch.pack(pady=10)
        
        # IPSet
        ipset_frame = ctk.CTkFrame(self.settings_tab)
        ipset_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            ipset_frame,
            text="IPSet режим",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        self.ipset_var = ctk.StringVar(value="any")
        ipset_menu = ctk.CTkOptionMenu(
            ipset_frame,
            values=["any", "none", "loaded"],
            variable=self.ipset_var,
            command=self.change_ipset_mode,
            font=ctk.CTkFont(size=14)
        )
        ipset_menu.pack(pady=10)
        
        ctk.CTkButton(
            ipset_frame,
            text="🔄 Обновить IPSet список",
            command=self.update_ipset,
            height=40,
            font=ctk.CTkFont(size=14)
        ).pack(pady=10)
        
        # Автоматическая проверка
        auto_check_frame = ctk.CTkFrame(self.settings_tab)
        auto_check_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            auto_check_frame,
            text="Автоматическая проверка",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        auto_check_switch_frame = ctk.CTkFrame(auto_check_frame, fg_color="transparent")
        auto_check_switch_frame.pack(fill="x", padx=10, pady=5)
        
        self.auto_check_var = ctk.BooleanVar(value=False)
        self.auto_check_switch = ctk.CTkSwitch(
            auto_check_switch_frame,
            text="Включить автоматическую проверку работоспособности",
            variable=self.auto_check_var,
            command=self.toggle_auto_check,
            font=ctk.CTkFont(size=14)
        )
        self.auto_check_switch.pack(side="left")
        
        self.auto_check_interval_var = ctk.StringVar(value="60")
        interval_frame = ctk.CTkFrame(auto_check_frame, fg_color="transparent")
        interval_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            interval_frame,
            text="Интервал проверки (секунд):",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 10))
        
        self.auto_check_interval = ctk.CTkEntry(
            interval_frame,
            textvariable=self.auto_check_interval_var,
            width=80,
            font=ctk.CTkFont(size=12)
        )
        self.auto_check_interval.pack(side="left")
        
        # Тема оформления
        theme_frame = ctk.CTkFrame(self.settings_tab)
        theme_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            theme_frame,
            text="Тема оформления",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        self.theme_var = ctk.StringVar(value="dark")
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["dark", "light", "system"],
            variable=self.theme_var,
            command=self.change_theme,
            font=ctk.CTkFont(size=14)
        )
        theme_menu.pack(pady=10)
        
        # Автозапуск
        autostart_frame = ctk.CTkFrame(self.settings_tab)
        autostart_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            autostart_frame,
            text="Автозапуск",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        self.autostart_var = ctk.BooleanVar(value=False)
        autostart_switch = ctk.CTkSwitch(
            autostart_frame,
            text="Запускать приложение при старте Windows",
            variable=self.autostart_var,
            command=self.toggle_autostart,
            font=ctk.CTkFont(size=14)
        )
        autostart_switch.pack(pady=5)
        
        self.auto_start_bypass_var = ctk.BooleanVar(value=False)
        auto_start_bypass_switch = ctk.CTkSwitch(
            autostart_frame,
            text="Автоматически запускать последний использованный bypass при старте",
            variable=self.auto_start_bypass_var,
            command=self.toggle_auto_start_bypass,
            font=ctk.CTkFont(size=14)
        )
        auto_start_bypass_switch.pack(pady=5)
        
        # Обновления
        update_frame = ctk.CTkFrame(self.settings_tab)
        update_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            update_frame,
            text="Обновления",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        ctk.CTkButton(
            update_frame,
            text="🔍 Проверить обновления",
            command=self.check_updates,
            height=40,
            font=ctk.CTkFont(size=14)
        ).pack(pady=10)
        
        # Экспорт/Импорт настроек
        export_frame = ctk.CTkFrame(self.settings_tab)
        export_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            export_frame,
            text="Настройки",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        export_buttons_frame = ctk.CTkFrame(export_frame, fg_color="transparent")
        export_buttons_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            export_buttons_frame,
            text="💾 Экспорт настроек",
            command=self.export_settings,
            height=35,
            font=ctk.CTkFont(size=13),
            width=150
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            export_buttons_frame,
            text="📥 Импорт настроек",
            command=self.import_settings,
            height=35,
            font=ctk.CTkFont(size=13),
            width=150
        ).pack(side="left")
        
    def load_configurations(self, parent_frame=None):
        """Загружает список доступных .bat конфигураций"""
        # Исключаем служебные файлы
        excluded_files = {
            "service.bat",
            "build.bat", 
            "run_gui.bat",
            "install_dependencies.bat"
        }
        
        configs = []
        for file in self.script_dir.glob("*.bat"):
            # Исключаем файлы начинающиеся с "service" и служебные файлы
            if not file.name.startswith("service") and file.name not in excluded_files:
                # Проверяем что файл действительно содержит winws.exe (является конфигурацией bypass)
                try:
                    content = file.read_text(encoding='utf-8', errors='ignore')
                    if 'winws.exe' in content or '%BIN%winws.exe' in content:
                        configs.append(file.name)
                except:
                    # Если не удалось прочитать - пропускаем
                    pass
        
        self.configurations = configs
        
        # Если передан parent_frame, создаем радиокнопки
        if parent_frame:
            # Очищаем старые виджеты
            for widget in parent_frame.winfo_children():
                widget.destroy()
            
            self.config_radio_buttons.clear()
            self.config_status_labels.clear()
            if configs:
                self.config_var.set(configs[0])
                for config in configs:
                    # Фрейм для каждой конфигурации
                    config_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
                    config_frame.pack(fill="x", pady=3, padx=5)
                    
                    # Радиокнопка
                    radio = ctk.CTkRadioButton(
                        config_frame,
                        text=config,
                        variable=self.config_var,
                        value=config,
                        font=ctk.CTkFont(size=11)
                    )
                    radio.pack(side="left", anchor="w")
                    
                    # Метка статуса (YouTube/Discord)
                    status_label = ctk.CTkLabel(
                        config_frame,
                        text="",
                        font=ctk.CTkFont(size=14),
                        width=60
                    )
                    status_label.pack(side="right", padx=(10, 0))
                    self.config_status_labels[config] = status_label
                    
                    self.config_radio_buttons.append(radio)
            else:
                no_config_label = ctk.CTkLabel(
                    parent_frame,
                    text="Конфигурации не найдены",
                    font=ctk.CTkFont(size=12),
                    text_color="gray"
                )
                no_config_label.pack(pady=20)
    
    def update_config_status(self, config_name, youtube_works, discord_works):
        """Обновляет статус конфигурации с иконками"""
        if config_name in self.config_status_labels:
            status_text = ""
            if youtube_works and discord_works:
                status_text = "📺💬"
            elif youtube_works:
                status_text = "📺"
            elif discord_works:
                status_text = "💬"
            else:
                status_text = "❌"
            
            self.config_status_labels[config_name].configure(text=status_text)
        
    def run_selected_config(self):
        """Запускает выбранную конфигурацию"""
        config_file = self.config_var.get()
        if not config_file or config_file not in self.configurations:
            messagebox.showwarning("Предупреждение", "Выберите конфигурацию из списка")
            return
        
        self.run_bat_file(config_file)
    
    def log_to_console(self, message):
        """Выводит сообщение в консоль"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_text.insert("end", f"[{timestamp}] {message}")
        if self.console_auto_scroll.get():
            self.console_text.see("end")
        self.root.update_idletasks()
    
    def run_bat_file(self, bat_file):
        """Запускает .bat файл в фоне без отдельного окна"""
        bat_path = self.script_dir / bat_file
        if not bat_path.exists():
            messagebox.showerror("Ошибка", f"Файл {bat_file} не найден")
            return
        
        try:
            # Останавливаем предыдущий процесс если есть
            if self.current_winws_process:
                try:
                    self.current_winws_process.terminate()
                except:
                    pass
            
            # Запускаем без отдельного окна консоли
            self.current_winws_process = subprocess.Popen(
                [str(bat_path)],
                cwd=str(self.script_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                shell=False
            )
            
            # Сохраняем последнюю использованную конфигурацию
            self.save_last_config(bat_file)
            
            self.log_to_console(f"Запущена конфигурация: {bat_file}\n")
            self.update_status_label(f"Запущена конфигурация: {bat_file}")
        except Exception as e:
            error_msg = f"Ошибка запуска {bat_file}: {str(e)}\n"
            self.log_to_console(error_msg)
            messagebox.showerror("Ошибка", f"Не удалось запустить: {str(e)}")
    
    def stop_winws(self):
        """Останавливает процесс winws.exe"""
        try:
            # Останавливаем отслеживаемый процесс
            if self.current_winws_process:
                try:
                    self.current_winws_process.terminate()
                    self.current_winws_process.wait(timeout=5)
                except:
                    try:
                        self.current_winws_process.kill()
                    except:
                        pass
                self.current_winws_process = None
            
            # Также останавливаем через taskkill для надежности
            subprocess.run(
                ["taskkill", "/IM", "winws.exe", "/F"],
                capture_output=True,
                shell=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            # Даем время процессу завершиться
            threading.Event().wait(2)
            self.log_to_console("Процесс winws.exe остановлен\n")
        except Exception as e:
            self.log_to_console(f"Ошибка остановки winws.exe: {str(e)}\n")
    
    def find_working_bypass(self):
        """Автоматически находит рабочую конфигурацию путем проверки каждой"""
        if not self.configurations:
            messagebox.showwarning("Предупреждение", "Конфигурации не найдены")
            return
        
        # Подтверждение
        result = messagebox.askyesno(
            "Поиск рабочего Bypass",
            f"Будет проверено {len(self.configurations)} конфигураций.\n\n"
            "Это может занять некоторое время. Продолжить?",
            icon="question"
        )
        if not result:
            return
        
        # Блокируем кнопку во время поиска
        self.find_working_btn.configure(state="disabled", text="🔍 Поиск...")
        
        def search():
            try:
                working_configs = []  # Список всех рабочих конфигураций
                total = len(self.configurations)
                
                # Останавливаем текущий процесс если запущен
                self.root.after(0, lambda: self.find_progress_label.configure(
                    text="Останавливаю текущий процесс...",
                    text_color="orange"
                ))
                self.stop_winws()
                
                for i, config in enumerate(self.configurations, 1):
                    # Обновляем прогресс
                    self.root.after(0, lambda c=config, idx=i, tot=total: self.find_progress_label.configure(
                        text=f"Проверяю {idx}/{tot}: {c}...",
                        text_color="gray"
                    ))
                    self.root.after(0, lambda idx=i, tot=total, cfg=config: self.update_status_label(
                        f"Проверка конфигурации {idx}/{tot}: {cfg}"
                    ))
                    
                    # Останавливаем предыдущий процесс
                    self.stop_winws()
                    
                    # Проверяем что это реальный файл конфигурации (не служебный)
                    excluded_files = {"service.bat", "build.bat", "run_gui.bat", "install_dependencies.bat"}
                    if config in excluded_files:
                        self.root.after(0, lambda cfg=config: self.log_to_console(f"Пропускаю служебный файл: {cfg}\n"))
                        continue
                    
                    # Запускаем новую конфигурацию
                    bat_path = self.script_dir / config
                    if not bat_path.exists():
                        self.root.after(0, lambda cfg=config: self.log_to_console(f"Файл не найден: {cfg}\n"))
                        continue
                    
                    try:
                        # Останавливаем предыдущий процесс
                        if self.current_winws_process:
                            try:
                                self.current_winws_process.terminate()
                            except:
                                pass
                        
                        self.current_winws_process = subprocess.Popen(
                            [str(bat_path)],
                            cwd=str(self.script_dir),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                        )
                        self.root.after(0, lambda cfg=config: self.log_to_console(f"Тестирую конфигурацию: {cfg}\n"))
                    except Exception as e:
                        self.root.after(0, lambda err=str(e), cfg=config: self.find_progress_label.configure(
                            text=f"Ошибка запуска {cfg}: {err}",
                            text_color="red"
                        ))
                        continue
                    
                    # Ждем инициализацию bypass (нужно больше времени для запуска winws.exe)
                    youtube_works = False
                    discord_works = False
                    
                    # Ждем 12 секунд для полной инициализации bypass
                    for wait in range(12):
                        threading.Event().wait(1)
                        if wait >= 10:  # Через 10 секунд начинаем проверку
                            # Проверяем доступность YouTube и Discord (делаем несколько попыток для надежности)
                            for attempt in range(2):
                                youtube_available = self.check_youtube_availability()
                                discord_available = self.check_discord_availability()
                                
                                youtube_works = youtube_available is True
                                discord_works = discord_available is True
                                
                                # Обновляем статус конфигурации
                                self.root.after(0, lambda c=config, yt=youtube_works, dc=discord_works: 
                                              self.update_config_status(c, yt, dc))
                                
                                # Если хотя бы один работает - выходим из попыток
                                if youtube_works or discord_works:
                                    break
                                
                                # Небольшая задержка между попытками
                                if attempt < 1:
                                    threading.Event().wait(2)
                            
                            # Если хотя бы один работает - добавляем в список рабочих
                            if youtube_works or discord_works:
                                working_configs.append({
                                    'name': config,
                                    'youtube': youtube_works,
                                    'discord': discord_works
                                })
                                self.root.after(0, lambda cfg=config, yt=youtube_works, dc=discord_works: 
                                              self.log_to_console(f"✅ Найдена рабочая конфигурация: {cfg} (YouTube: {yt}, Discord: {dc})\n"))
                    
                    # Продолжаем проверку всех конфигураций (не останавливаемся)
                
                # Результат
                if working_configs:
                    # Формируем список всех найденных рабочих конфигураций
                    configs_list = []
                    for cfg_info in working_configs:
                        services = []
                        if cfg_info['youtube']:
                            services.append("📺 YouTube")
                        if cfg_info['discord']:
                            services.append("💬 Discord")
                        services_str = " + ".join(services) if services else "неизвестно"
                        configs_list.append(f"  • {cfg_info['name']} ({services_str})")
                    
                    configs_text = "\n".join(configs_list)
                    total_found = len(working_configs)
                    
                    # Выбираем первую рабочую конфигурацию
                    first_working = working_configs[0]['name']
                    
                    self.root.after(0, lambda found=total_found: self.find_progress_label.configure(
                        text=f"✅ Найдено рабочих конфигураций: {found}",
                        text_color="green"
                    ))
                    self.root.after(0, lambda found=total_found: self.update_status_label(
                        f"✅ Проверка завершена. Найдено рабочих конфигураций: {found}"
                    ))
                    
                    # Выделяем первую найденную конфигурацию
                    self.root.after(0, lambda cfg=first_working: self.config_var.set(cfg))
                    
                    # Показываем сообщение со всеми найденными конфигурациями
                    self.root.after(0, lambda found=total_found, text=configs_text: messagebox.showinfo(
                        "Успех!",
                        f"✅ Найдено рабочих конфигураций: {found}\n\n"
                        f"Рабочие конфигурации:\n{text}\n\n"
                        "Первая найденная конфигурация была автоматически выбрана в списке."
                    ))
                else:
                    self.root.after(0, lambda: self.find_progress_label.configure(
                        text="❌ Рабочая конфигурация не найдена",
                        text_color="red"
                    ))
                    self.root.after(0, lambda: self.update_status_label(
                        "❌ Рабочая конфигурация не найдена среди проверенных"
                    ))
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Не найдено",
                        "Рабочая конфигурация не найдена среди проверенных.\n\n"
                        "Возможно, требуется дополнительная настройка или проблема с сетью."
                    ))
                
            except Exception as e:
                self.root.after(0, lambda err=str(e): messagebox.showerror(
                    "Ошибка",
                    f"Произошла ошибка при поиске: {err}"
                ))
            finally:
                # Восстанавливаем кнопку
                self.root.after(0, lambda: self.find_working_btn.configure(
                    state="normal",
                    text="🔍 Найти рабочий Bypass"
                ))
        
        threading.Thread(target=search, daemon=True).start()
    
    def install_service(self):
        """Устанавливает службу"""
        if not self.service_bat.exists():
            messagebox.showerror("Ошибка", "Файл service.bat не найден")
            return
        
        # Получаем список конфигураций для выбора
        configs = [f.name for f in self.script_dir.glob("*.bat") if not f.name.startswith("service")]
        
        if not configs:
            messagebox.showerror("Ошибка", "Не найдено конфигураций для установки")
            return
        
        # Создаем окно выбора конфигурации
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Выбор конфигурации для установки")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(
            dialog,
            text="Выберите конфигурацию для установки:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=20)
        
        # Список конфигураций с радиокнопками
        selected_config = ctk.StringVar(value=configs[0] if configs else "")
        
        scroll_frame = ctk.CTkScrollableFrame(dialog)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        for config in configs:
            ctk.CTkRadioButton(
                scroll_frame,
                text=config,
                variable=selected_config,
                value=config,
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=5)
        
        def install():
            config_name = selected_config.get()
            if config_name:
                dialog.destroy()
                self.run_service_install_interactive(config_name)
        
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="Установить",
            command=install,
            font=ctk.CTkFont(size=14),
            fg_color="green",
            hover_color="darkgreen"
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame,
            text="Отмена",
            command=dialog.destroy,
            font=ctk.CTkFont(size=14)
        ).pack(side="left")
    
    def run_service_install_interactive(self, config_name):
        """Запускает установку службы через упрощенный скрипт"""
        # Используем упрощенный подход - создаем скрипт, который вызывает оригинальный service.bat
        # но с предварительно подготовленными параметрами
        def run():
            try:
                if not (self.script_dir / config_name).exists():
                    self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Файл {config_name} не найден"))
                    return
                
                # Создаем упрощенный скрипт установки
                # Этот скрипт будет использовать логику из service.bat
                install_script = f'''@echo off
chcp 65001 > nul
cd /d "{self.script_dir}"

echo Установка службы zapret с конфигурацией: {config_name}
echo.
echo ВАЖНО: Этот процесс использует оригинальный service.bat
echo Для автоматической установки запустите service.bat вручную и выберите конфигурацию {config_name}
echo.
echo Открываю service.bat...
echo.

:: Запускаем service.bat от имени администратора
powershell -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c \"cd /d {self.script_dir} && call service.bat admin\"' -Verb RunAs"

pause
'''
                
                temp_bat = tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False, encoding='utf-8')
                temp_bat.write(install_script)
                temp_bat.close()
                
                # Показываем сообщение пользователю
                result = messagebox.askyesno(
                    "Установка службы",
                    f"Установка службы с конфигурацией '{config_name}'\n\n"
                    "Для установки будет открыто окно service.bat.\n"
                    "Выберите в меню пункт '1. Install Service' и введите номер конфигурации '{config_name}'.\n\n"
                    "Продолжить?",
                    icon="question"
                )
                
                if result:
                    # Запускаем напрямую (уже с правами администратора)
                    run_result = subprocess.run(
                        [str(temp_bat)],
                        cwd=str(self.script_dir),
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="ignore",
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                    self.root.after(0, lambda: self.log_to_console(run_result.stdout + run_result.stderr + "\n"))
                    
                    self.root.after(0, lambda: self.update_status_label(
                        f"Открыто окно установки. Выберите конфигурацию: {config_name}"
                    ))
                    self.root.after(10000, self.update_status)  # Обновляем статус через 10 секунд
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось запустить установку: {str(e)}"))
        
        threading.Thread(target=run, daemon=True).start()
    
    def remove_service(self):
        """Удаляет службу"""
        if messagebox.askyesno("Подтверждение", "Удалить службу zapret?"):
            self.run_service_command_direct(["net", "stop", "zapret"])
            self.run_service_command_direct(["sc", "delete", "zapret"])
            
            # Также останавливаем winws.exe и WinDivert
            subprocess.run(["taskkill", "/IM", "winws.exe", "/F"], 
                         capture_output=True, shell=True)
            subprocess.run(["net", "stop", "WinDivert"], 
                         capture_output=True, shell=True)
            subprocess.run(["sc", "delete", "WinDivert"], 
                         capture_output=True, shell=True)
            
            self.update_status()
            self.update_status_label("Служба удалена")
    
    def start_service(self):
        """Запускает службу"""
        self.run_service_command_direct(["net", "start", "zapret"])
        self.update_status()
        self.update_status_label("Запуск службы...")
    
    def stop_service(self):
        """Останавливает службу"""
        self.run_service_command_direct(["net", "stop", "zapret"])
        self.update_status()
        self.update_status_label("Остановка службы...")
    
    def run_service_command_direct(self, cmd):
        """Выполняет команду напрямую (требует прав администратора)"""
        def run():
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    shell=True
                )
                if result.returncode != 0:
                    # Пытаемся запустить с правами администратора
                    subprocess.Popen(
                        ["powershell", "-Command", 
                         f"Start-Process -FilePath '{cmd[0]}' -ArgumentList '{' '.join(cmd[1:])}' -Verb RunAs"],
                        shell=True
                    )
            except Exception as e:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Предупреждение", 
                    f"Не удалось выполнить команду напрямую: {str(e)}\n"
                    "Попробуйте запустить приложение от имени администратора."
                ))
        
        threading.Thread(target=run, daemon=True).start()
    
    def update_status(self):
        """Обновляет статус службы"""
        def check():
            try:
                # Проверка службы zapret
                result = subprocess.run(
                    ["sc", "query", "zapret"],
                    capture_output=True,
                    text=True
                )
                
                is_running = "RUNNING" in result.stdout
                
                # Проверка winws.exe
                winws_result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq winws.exe"],
                    capture_output=True,
                    text=True
                )
                winws_running = "winws.exe" in winws_result.stdout
                
                self.root.after(0, lambda: self.update_status_display(is_running, winws_running))
                
            except Exception as e:
                self.root.after(0, lambda: self.update_status_label(f"Ошибка проверки: {str(e)}"))
        
        threading.Thread(target=check, daemon=True).start()
    
    def update_status_display(self, service_running, winws_running):
        """Обновляет отображение статуса"""
        self.service_running = service_running
        
        if service_running:
            self.service_status_label.configure(
                text="✅ Служба zapret: ЗАПУЩЕНА",
                text_color="green"
            )
        else:
            self.service_status_label.configure(
                text="❌ Служба zapret: ОСТАНОВЛЕНА",
                text_color="red"
            )
        
        if winws_running:
            self.winws_status_label.configure(
                text="✅ Bypass (winws.exe): АКТИВЕН",
                text_color="green"
            )
        else:
            self.winws_status_label.configure(
                text="❌ Bypass (winws.exe): НЕ АКТИВЕН",
                text_color="red"
            )
        
        # Получаем информацию о текущей конфигурации
        try:
            result = subprocess.run(
                ["reg", "query", "HKLM\\System\\CurrentControlSet\\Services\\zapret", "/v", "zapret-discord-youtube"],
                capture_output=True,
                text=True
            )
            if "zapret-discord-youtube" in result.stdout:
                match = re.search(r'zapret-discord-youtube\s+REG_SZ\s+(.+)', result.stdout)
                if match:
                    config_name = match.group(1).strip()
                    self.info_text.delete(1.0, "end")
                    self.info_text.insert("end", f"Текущая конфигурация: {config_name}\n")
        except:
            pass
    
    def run_diagnostics(self):
        """Запускает диагностику"""
        self.diagnostics_text.delete(1.0, "end")
        self.diagnostics_text.insert("end", "Запуск диагностики...\n\n")
        
        def run():
            try:
                result = subprocess.run(
                    [str(self.service_bat), "diagnostics"],
                    cwd=str(self.script_dir),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore"
                )
                
                output = result.stdout + result.stderr
                self.root.after(0, lambda: self.diagnostics_text.insert("end", output))
            except Exception as e:
                self.root.after(0, lambda: self.diagnostics_text.insert("end", f"Ошибка: {str(e)}\n"))
        
        threading.Thread(target=run, daemon=True).start()
    
    def toggle_game_filter(self):
        """Переключает Game Filter"""
        enabled = self.game_filter_var.get() == "enabled"
        flag_file = self.bin_path / "game_filter.enabled"
        
        try:
            if enabled:
                flag_file.write_text("ENABLED")
            else:
                if flag_file.exists():
                    flag_file.unlink()
            
            self.save_settings()
            self.update_status_label("Game Filter переключен. Перезапустите службу для применения изменений.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось переключить Game Filter: {str(e)}")
    
    def change_ipset_mode(self, value):
        """Изменяет режим IPSet"""
        list_file = self.lists_path / "ipset-all.txt"
        backup_file = self.lists_path / "ipset-all.txt.backup"
        
        try:
            if value == "none":
                if not backup_file.exists() and list_file.exists():
                    list_file.rename(backup_file)
                list_file.write_text("203.0.113.113/32\n")
            elif value == "any":
                if list_file.exists():
                    list_file.write_text("")
            elif value == "loaded":
                if backup_file.exists():
                    if list_file.exists():
                        list_file.unlink()
                    backup_file.rename(list_file)
                else:
                    messagebox.showwarning("Предупреждение", "Нет резервной копии для восстановления")
            
            self.save_settings()
            self.update_status_label(f"IPSet режим изменен на: {value}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось изменить режим IPSet: {str(e)}")
    
    def toggle_auto_check(self):
        """Переключает автоматическую проверку"""
        self.auto_check_enabled = self.auto_check_var.get()
        self.auto_check_interval_seconds = int(self.auto_check_interval_var.get())
        self.save_settings()
        
        if self.auto_check_enabled:
            self.start_auto_check()
        else:
            self.stop_auto_check()
    
    def start_auto_check(self):
        """Запускает автоматическую проверку"""
        if self.auto_check_thread and self.auto_check_thread.is_alive():
            return
        
        def auto_check_loop():
            while self.auto_check_enabled:
                threading.Event().wait(self.auto_check_interval_seconds)
                if self.auto_check_enabled:
                    self.root.after(0, self.check_youtube_now)
        
        self.auto_check_thread = threading.Thread(target=auto_check_loop, daemon=True)
        self.auto_check_thread.start()
        self.log_to_console(f"Автоматическая проверка включена (интервал: {self.auto_check_interval_seconds} сек)\n")
    
    def stop_auto_check(self):
        """Останавливает автоматическую проверку"""
        self.auto_check_enabled = False
        self.log_to_console("Автоматическая проверка отключена\n")
    
    def change_theme(self, theme):
        """Изменяет тему оформления"""
        if theme == "system":
            try:
                import darkdetect
                theme = "dark" if darkdetect.isDark() else "light"
            except ImportError:
                theme = "dark"  # По умолчанию темная тема
        ctk.set_appearance_mode(theme)
        self.save_settings()
    
    def toggle_autostart(self):
        """Переключает автозапуск"""
        enabled = self.autostart_var.get()
        self.set_autostart(enabled)
        self.save_settings()
    
    def set_autostart(self, enabled):
        """Устанавливает автозапуск в реестре Windows"""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "ZapretGUI"
            # Используем правильный путь к exe
            if getattr(sys, 'frozen', False):
                exe_path = str(sys.executable)
            else:
                exe_path = str(sys.executable)
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
                self.log_to_console("Автозапуск включен\n")
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    self.log_to_console("Автозапуск отключен\n")
                except FileNotFoundError:
                    pass
            
            winreg.CloseKey(key)
        except Exception as e:
            self.log_to_console(f"Ошибка настройки автозапуска: {str(e)}\n")
            if not self.is_admin:
                messagebox.showwarning(
                    "Предупреждение",
                    "Для настройки автозапуска могут потребоваться права администратора."
                )
    
    def export_settings(self):
        """Экспортирует настройки в файл"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Экспорт настроек"
        )
        if filename:
            try:
                settings = {
                    'game_filter': self.game_filter_var.get(),
                    'ipset_mode': self.ipset_var.get(),
                    'auto_check': self.auto_check_var.get(),
                    'auto_check_interval': int(self.auto_check_interval_var.get()),
                    'theme': self.theme_var.get(),
                    'autostart': self.autostart_var.get()
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Успех", f"Настройки экспортированы в:\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать настройки: {str(e)}")
    
    def import_settings(self):
        """Импортирует настройки из файла"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Импорт настроек"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Применяем настройки
                if 'game_filter' in settings:
                    self.game_filter_var.set(settings['game_filter'])
                    self.toggle_game_filter()
                
                if 'ipset_mode' in settings:
                    self.ipset_var.set(settings['ipset_mode'])
                    self.change_ipset_mode(settings['ipset_mode'])
                
                if 'auto_check' in settings:
                    self.auto_check_var.set(settings['auto_check'])
                    self.auto_check_enabled = settings['auto_check']
                    if settings['auto_check']:
                        self.start_auto_check()
                    else:
                        self.stop_auto_check()
                
                if 'auto_check_interval' in settings:
                    self.auto_check_interval_var.set(str(settings['auto_check_interval']))
                    self.auto_check_interval_seconds = settings['auto_check_interval']
                
                if 'theme' in settings:
                    self.theme_var.set(settings['theme'])
                    self.change_theme(settings['theme'])
                
                if 'autostart' in settings:
                    self.autostart_var.set(settings['autostart'])
                    self.set_autostart(settings['autostart'])
                
                self.save_settings()
                messagebox.showinfo("Успех", "Настройки успешно импортированы")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось импортировать настройки: {str(e)}")
    
    def update_ipset(self):
        """Обновляет IPSet список"""
        list_file = self.lists_path / "ipset-all.txt"
        url = "https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/refs/heads/main/.service/ipset-service.txt"
        
        def run():
            try:
                import urllib.request
                self.update_status_label("Обновление IPSet списка...")
                urllib.request.urlretrieve(url, str(list_file))
                self.root.after(0, lambda: self.update_status_label("IPSet список успешно обновлен"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось обновить список: {str(e)}"))
        
        threading.Thread(target=run, daemon=True).start()
    
    def check_updates(self):
        """Проверяет обновления"""
        def run():
            try:
                result = subprocess.run(
                    [str(self.service_bat), "check_updates"],
                    cwd=str(self.script_dir),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore"
                )
                output = result.stdout
                self.root.after(0, lambda: messagebox.showinfo("Обновления", output))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось проверить обновления: {str(e)}"))
        
        threading.Thread(target=run, daemon=True).start()
        self.update_status_label("Проверка обновлений...")
    
    def check_service_availability(self, host):
        """Проверяет доступность сервиса через HTTPS запрос (точная проверка)"""
        try:
            # Используем HTTPS запрос для более точной проверки
            # TCP соединение может быть установлено даже если сайт заблокирован DPI
            req = urllib.request.Request(
                f"https://{host}",
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            try:
                with urllib.request.urlopen(req, timeout=8) as response:
                    # Проверяем статус код
                    if response.status == 200:
                        # Проверяем размер ответа - заблокированные сайты обычно возвращают маленькие страницы-заглушки
                        # Читаем первые несколько байт для проверки
                        data = response.read(2000)  # Читаем первые 2KB
                        
                        # Проверяем что это не страница блокировки
                        data_str = data.decode('utf-8', errors='ignore').lower()
                        
                        # Если это реальная страница (содержит характерные элементы)
                        if len(data) > 500:  # Реальный сайт обычно больше 500 байт
                            # Проверяем что это не страница блокировки по ключевым словам
                            block_keywords = ['blocked', 'заблокирован', 'access denied', 'ркн', 'roskomnadzor', 'доступ ограничен', 'roscomnadzor']
                            if not any(keyword in data_str for keyword in block_keywords):
                                return True
                        
                        return False
                    return False
                    
            except urllib.error.HTTPError as e:
                # HTTP ошибки (403, 404 и т.д.) означают что сайт доступен (сервер ответил)
                if e.code in [403, 404, 429, 503]:
                    return True
                return False
                
            except urllib.error.URLError as e:
                # URL ошибки обычно означают что сайт недоступен или заблокирован
                error_str = str(e.reason).lower()
                if 'timed out' in error_str or 'timeout' in error_str:
                    return False
                if 'refused' in error_str or 'unreachable' in error_str:
                    return False
                # Другие ошибки - считаем недоступным
                return False
                
            except socket.timeout:
                return False
                
        except Exception as e:
            # Любая другая ошибка - считаем недоступным
            return False
    
    def check_youtube_availability(self):
        """Проверяет доступность youtube.com"""
        return self.check_service_availability("www.youtube.com")
    
    def check_discord_availability(self):
        """Проверяет доступность discord.com"""
        return self.check_service_availability("discord.com")
    
    def check_youtube_now(self):
        """Выполняет проверку работоспособности YouTube и Discord"""
        def check():
            self.root.after(0, lambda: self.youtube_status_label.configure(
                text="Проверка работоспособности...",
                text_color="gray"
            ))
            self.root.after(0, lambda: self.youtube_status_indicator.configure(
                text="●",
                text_color="gray"
            ))
            self.update_status_label("Выполняется проверка работоспособности...")
            
            youtube_result = self.check_youtube_availability()
            discord_result = self.check_discord_availability()
            
            self.root.after(0, lambda: self.update_youtube_status(youtube_result, discord_result))
        
        threading.Thread(target=check, daemon=True).start()
    
    def update_youtube_status(self, youtube_available, discord_available=None):
        """Обновляет статус YouTube и Discord в интерфейсе"""
        self.last_youtube_check = datetime.now()
        self.youtube_status = youtube_available
        
        # Если discord_available не передан, проверяем его
        if discord_available is None:
            discord_available = self.check_discord_availability()
        
        youtube_ok = youtube_available is True
        discord_ok = discord_available is True
        
        # Формируем статусное сообщение
        status_parts = []
        if youtube_ok:
            status_parts.append("📺 YouTube")
        if discord_ok:
            status_parts.append("💬 Discord")
        
        if status_parts:
            status_text = f"✅ {' + '.join(status_parts)} доступны - Bypass работает!"
            status_color = "green"
            status_indicator = "●"
            indicator_color = "green"
            status_msg = f"Проверка: ✅ Работает ({' + '.join(status_parts)})"
        elif youtube_available is False and discord_available is False:
            status_text = "❌ YouTube и Discord недоступны - Bypass не работает"
            status_color = "red"
            status_indicator = "●"
            indicator_color = "red"
            status_msg = "Проверка: ❌ Оба сервиса недоступны"
        else:
            status_text = "⚠️ Ошибка проверки работоспособности"
            status_color = "orange"
            status_indicator = "●"
            indicator_color = "orange"
            status_msg = "Проверка: ⚠️ Ошибка"
        
        self.youtube_status_label.configure(
            text=status_text,
            text_color=status_color
        )
        self.youtube_status_indicator.configure(
            text=status_indicator,
            text_color=indicator_color
        )
        
        # Обновляем время последней проверки
        if self.last_youtube_check:
            time_str = self.last_youtube_check.strftime("%H:%M:%S")
            self.youtube_last_check_label.configure(
                text=f"Последняя проверка: {time_str}"
            )
        
        self.update_status_label(status_msg)
    
    def create_console_tab(self):
        """Создает вкладку консоли для вывода логов"""
        # Текстовое поле для консоли
        self.console_text = scrolledtext.ScrolledText(
            self.console_tab,
            bg="#1e1e1e",
            fg="#00ff00",
            font=("Consolas", 10),
            wrap="word"
        )
        self.console_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Кнопки управления консолью
        button_frame = ctk.CTkFrame(self.console_tab, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(
            button_frame,
            text="🔄 Очистить консоль",
            command=lambda: self.console_text.delete(1.0, "end"),
            height=35,
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 10))
        
        self.console_auto_scroll = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            button_frame,
            text="Автопрокрутка",
            variable=self.console_auto_scroll,
            font=ctk.CTkFont(size=12)
        ).pack(side="left")
        
        # Приветственное сообщение
        self.log_to_console("=== Zapret DPI Bypass Control Panel ===\n")
        self.log_to_console("Консоль готова. Логи будут отображаться здесь.\n\n")
    
    def create_traffic_tab(self):
        """Создает вкладку мониторинга трафика"""
        # Верхняя панель с кнопками управления
        control_frame = ctk.CTkFrame(self.traffic_tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            control_frame,
            text="Мониторинг трафика",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        buttons_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.traffic_monitor_btn = ctk.CTkButton(
            buttons_frame,
            text="▶️ Запустить мониторинг",
            command=self.toggle_traffic_monitor,
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.traffic_monitor_btn.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            buttons_frame,
            text="🔄 Сбросить статистику",
            command=self.reset_traffic_stats,
            height=35,
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            buttons_frame,
            text="💾 Экспорт статистики",
            command=self.export_traffic_stats,
            height=35,
            font=ctk.CTkFont(size=13)
        ).pack(side="left")
        
        # Статистика трафика
        stats_frame = ctk.CTkFrame(self.traffic_tab)
        stats_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Сетка для статистики
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Левая колонка
        left_col = ctk.CTkFrame(stats_grid)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(
            left_col,
            text="📤 Исходящий трафик",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))
        
        self.packets_sent_label = ctk.CTkLabel(
            left_col,
            text="Пакетов отправлено: 0",
            font=ctk.CTkFont(size=14)
        )
        self.packets_sent_label.pack(pady=5)
        
        self.bytes_sent_label = ctk.CTkLabel(
            left_col,
            text="Байт отправлено: 0",
            font=ctk.CTkFont(size=14)
        )
        self.bytes_sent_label.pack(pady=5)
        
        # Правая колонка
        right_col = ctk.CTkFrame(stats_grid)
        right_col.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(
            right_col,
            text="📥 Входящий трафик",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))
        
        self.packets_received_label = ctk.CTkLabel(
            right_col,
            text="Пакетов получено: 0",
            font=ctk.CTkFont(size=14)
        )
        self.packets_received_label.pack(pady=5)
        
        self.bytes_received_label = ctk.CTkLabel(
            right_col,
            text="Байт получено: 0",
            font=ctk.CTkFont(size=14)
        )
        self.bytes_received_label.pack(pady=5)
        
        # Общая статистика
        total_frame = ctk.CTkFrame(stats_frame)
        total_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(
            total_frame,
            text="📊 Общая статистика",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        total_stats_frame = ctk.CTkFrame(total_frame, fg_color="transparent")
        total_stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.total_packets_label = ctk.CTkLabel(
            total_stats_frame,
            text="Всего пакетов: 0",
            font=ctk.CTkFont(size=14)
        )
        self.total_packets_label.pack(side="left", padx=10)
        
        self.total_bytes_label = ctk.CTkLabel(
            total_stats_frame,
            text="Всего байт: 0",
            font=ctk.CTkFont(size=14)
        )
        self.total_bytes_label.pack(side="left", padx=10)
        
        self.connections_label = ctk.CTkLabel(
            total_stats_frame,
            text="Соединений: 0",
            font=ctk.CTkFont(size=14)
        )
        self.connections_label.pack(side="left", padx=10)
        
        self.uptime_label = ctk.CTkLabel(
            total_stats_frame,
            text="Время работы: 00:00:00",
            font=ctk.CTkFont(size=14)
        )
        self.uptime_label.pack(side="left", padx=10)
        
        # Обновляем отображение статистики
        self.update_traffic_display()
    
    def setup_hotkeys(self):
        """Настраивает горячие клавиши"""
        # Биндим горячие клавиши на главное окно
        self.root.bind('<Control-r>', lambda e: self.run_selected_config())
        self.root.bind('<Control-s>', lambda e: self.start_service())
        self.root.bind('<Control-t>', lambda e: self.stop_service())
        self.root.bind('<Control-f>', lambda e: self.find_working_bypass())
        self.root.bind('<Control-y>', lambda e: self.check_youtube_now())
        self.root.bind('<Control-q>', lambda e: self.stop_winws())
        self.root.bind('<F5>', lambda e: self.update_status())
        self.root.bind('<Control-h>', lambda e: self.show_hotkeys_help())
        
        # Фокус на окне для работы горячих клавиш
        self.root.focus_set()
    
    def show_hotkeys_help(self):
        """Показывает справку по горячим клавишам"""
        help_text = """Горячие клавиши:

Ctrl+R - Запустить выбранную конфигурацию
Ctrl+S - Запустить службу
Ctrl+T - Остановить службу
Ctrl+F - Найти рабочий Bypass
Ctrl+Y - Проверить работоспособность
Ctrl+Q - Остановить winws.exe
F5 - Обновить статус
Ctrl+H - Показать эту справку

Горячие клавиши работают когда окно приложения активно."""
        messagebox.showinfo("Горячие клавиши", help_text)
    
    def start_traffic_monitor(self):
        """Запускает мониторинг трафика"""
        if self.traffic_monitor_thread and self.traffic_monitor_thread.is_alive():
            return
        
        def monitor_loop():
            while True:
                if self.traffic_monitor_enabled:
                    self.update_traffic_stats()
                threading.Event().wait(2)  # Обновляем каждые 2 секунды
        
        self.traffic_monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.traffic_monitor_thread.start()
    
    def update_traffic_stats(self):
        """Обновляет статистику трафика"""
        try:
            # Проверяем запущен ли winws.exe
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq winws.exe"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            if "winws.exe" in result.stdout:
                # Если процесс запущен, обновляем статистику
                # Используем netstat для получения статистики соединений
                netstat_result = subprocess.run(
                    ["netstat", "-an"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                
                # Подсчитываем активные соединения (TCP ESTABLISHED)
                connections = netstat_result.stdout.count("ESTABLISHED")
                self.traffic_stats['connections'] = connections
                
                # Если мониторинг только начался, запоминаем время
                if self.traffic_stats['start_time'] is None:
                    self.traffic_stats['start_time'] = datetime.now()
                
                # Обновляем отображение
                self.root.after(0, self.update_traffic_display)
            else:
                # Если процесс не запущен, сбрасываем время
                if self.traffic_stats['start_time'] is not None:
                    self.traffic_stats['start_time'] = None
                    self.root.after(0, self.update_traffic_display)
        except Exception as e:
            pass  # Игнорируем ошибки мониторинга
    
    def update_traffic_display(self):
        """Обновляет отображение статистики трафика"""
        try:
            # Обновляем метки
            self.packets_sent_label.configure(
                text=f"Пакетов отправлено: {self.traffic_stats['packets_sent']:,}"
            )
            self.bytes_sent_label.configure(
                text=f"Байт отправлено: {self.format_bytes(self.traffic_stats['bytes_sent'])}"
            )
            self.packets_received_label.configure(
                text=f"Пакетов получено: {self.traffic_stats['packets_received']:,}"
            )
            self.bytes_received_label.configure(
                text=f"Байт получено: {self.format_bytes(self.traffic_stats['bytes_received'])}"
            )
            
            total_packets = self.traffic_stats['packets_sent'] + self.traffic_stats['packets_received']
            total_bytes = self.traffic_stats['bytes_sent'] + self.traffic_stats['bytes_received']
            
            self.total_packets_label.configure(
                text=f"Всего пакетов: {total_packets:,}"
            )
            self.total_bytes_label.configure(
                text=f"Всего байт: {self.format_bytes(total_bytes)}"
            )
            self.connections_label.configure(
                text=f"Соединений: {self.traffic_stats['connections']}"
            )
            
            # Время работы
            if self.traffic_stats['start_time']:
                uptime = datetime.now() - self.traffic_stats['start_time']
                hours, remainder = divmod(int(uptime.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.uptime_label.configure(
                    text=f"Время работы: {hours:02d}:{minutes:02d}:{seconds:02d}"
                )
            else:
                self.uptime_label.configure(text="Время работы: 00:00:00")
        except Exception as e:
            pass
    
    def format_bytes(self, bytes_count):
        """Форматирует байты в читаемый формат"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.2f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.2f} PB"
    
    def toggle_traffic_monitor(self):
        """Переключает мониторинг трафика"""
        self.traffic_monitor_enabled = not self.traffic_monitor_enabled
        
        if self.traffic_monitor_enabled:
            self.traffic_stats['start_time'] = datetime.now()
            self.traffic_monitor_btn.configure(
                text="⏸️ Остановить мониторинг",
                fg_color="orange",
                hover_color="darkorange"
            )
            self.log_to_console("Мониторинг трафика запущен\n")
        else:
            self.traffic_monitor_btn.configure(
                text="▶️ Запустить мониторинг",
                fg_color="green",
                hover_color="darkgreen"
            )
            self.log_to_console("Мониторинг трафика остановлен\n")
    
    def reset_traffic_stats(self):
        """Сбрасывает статистику трафика"""
        self.traffic_stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'connections': 0,
            'start_time': None
        }
        self.update_traffic_display()
        self.log_to_console("Статистика трафика сброшена\n")
    
    def export_traffic_stats(self):
        """Экспортирует статистику трафика в файл"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Экспорт статистики трафика"
        )
        if filename:
            try:
                total_packets = self.traffic_stats['packets_sent'] + self.traffic_stats['packets_received']
                total_bytes = self.traffic_stats['bytes_sent'] + self.traffic_stats['bytes_received']
                
                uptime_str = "00:00:00"
                if self.traffic_stats['start_time']:
                    uptime = datetime.now() - self.traffic_stats['start_time']
                    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== Статистика трафика Zapret ===\n\n")
                    f.write(f"Дата экспорта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("Исходящий трафик:\n")
                    f.write(f"  Пакетов отправлено: {self.traffic_stats['packets_sent']:,}\n")
                    f.write(f"  Байт отправлено: {self.format_bytes(self.traffic_stats['bytes_sent'])}\n\n")
                    f.write("Входящий трафик:\n")
                    f.write(f"  Пакетов получено: {self.traffic_stats['packets_received']:,}\n")
                    f.write(f"  Байт получено: {self.format_bytes(self.traffic_stats['bytes_received'])}\n\n")
                    f.write("Общая статистика:\n")
                    f.write(f"  Всего пакетов: {total_packets:,}\n")
                    f.write(f"  Всего байт: {self.format_bytes(total_bytes)}\n")
                    f.write(f"  Активных соединений: {self.traffic_stats['connections']}\n")
                    f.write(f"  Время работы: {uptime_str}\n")
                
                messagebox.showinfo("Успех", f"Статистика экспортирована в:\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать статистику: {str(e)}")
    
    def log_to_console(self, message):
        """Выводит сообщение в консоль"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_text.insert("end", f"[{timestamp}] {message}")
        if self.console_auto_scroll.get():
            self.console_text.see("end")
        self.root.update_idletasks()
    
    def check_admin(self):
        """Проверяет, запущено ли приложение от имени администратора"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def update_admin_status(self):
        """Обновляет отображение статуса администратора"""
        if self.is_admin:
            self.admin_status_label.configure(
                text="✓ Администратор",
                text_color="green"
            )
        else:
            self.admin_status_label.configure(
                text="⚠ Не администратор",
                text_color="orange"
            )
    
    def request_admin_restart(self):
        """Запрашивает перезапуск с правами администратора"""
        result = messagebox.askyesno(
            "Требуются права администратора",
            "Для полной функциональности приложение должно быть запущено от имени администратора.\n\n"
            "Перезапустить приложение с правами администратора?",
            icon="warning"
        )
        if result:
            try:
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, f'"{__file__}" asadmin', None, 1
                )
                self.root.quit()
            except Exception as e:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось перезапустить с правами администратора: {str(e)}\n\n"
                    "Запустите приложение вручную от имени администратора."
                )
        else:
            self.log_to_console("ВНИМАНИЕ: Приложение запущено без прав администратора. Некоторые функции могут не работать.\n")
    
    def extract_embedded_data(self):
        """Распаковывает встроенные данные (bin, lists, .bat файлы) при первом запуске exe"""
        import shutil
        
        # Проверяем нужно ли распаковывать
        if self.bin_path.exists() and self.lists_path.exists() and self.service_bat.exists():
            # Данные уже распакованы
            return
        
        try:
            # Путь к встроенным данным в exe
            embedded_bin = self.temp_dir / "bin"
            embedded_lists = self.temp_dir / "lists"
            embedded_bats = list(self.temp_dir.glob("*.bat"))
            
            # Создаем директории если их нет
            self.bin_path.mkdir(exist_ok=True)
            self.lists_path.mkdir(exist_ok=True)
            
            # Копируем bin
            if embedded_bin.exists():
                for item in embedded_bin.iterdir():
                    dest = self.bin_path / item.name
                    if not dest.exists():
                        if item.is_file():
                            shutil.copy2(item, dest)
                        elif item.is_dir():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
            
            # Копируем lists
            if embedded_lists.exists():
                for item in embedded_lists.iterdir():
                    dest = self.lists_path / item.name
                    if not dest.exists():
                        if item.is_file():
                            shutil.copy2(item, dest)
                        elif item.is_dir():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
            
            # Копируем .bat файлы (кроме служебных)
            excluded_bats = {"build.bat", "run_gui.bat", "install_dependencies.bat"}
            for bat_file in embedded_bats:
                if bat_file.name not in excluded_bats:
                    dest = self.script_dir / bat_file.name
                    if not dest.exists():
                        shutil.copy2(bat_file, dest)
            
            self.log_to_console(f"Данные распакованы в: {self.script_dir}\n")
        except Exception as e:
            self.log_to_console(f"Ошибка распаковки данных: {str(e)}\n")
            messagebox.showerror(
                "Ошибка",
                f"Не удалось распаковать данные приложения:\n{str(e)}\n\n"
                "Убедитесь что у приложения есть права на запись в директорию."
            )
    
    def load_settings(self):
        """Загружает настройки"""
        # Загружаем из файла настроек
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # Загружаем настройки
                if 'game_filter' in settings:
                    self.game_filter_var.set(settings['game_filter'])
                    if settings['game_filter'] == "enabled":
                        self.game_filter_switch.select()
                
                if 'ipset_mode' in settings:
                    self.ipset_var.set(settings['ipset_mode'])
                
                if 'auto_check' in settings:
                    self.auto_check_var.set(settings['auto_check'])
                    self.auto_check_enabled = settings['auto_check']
                    if settings['auto_check']:
                        self.auto_check_switch.select()
                
                if 'auto_check_interval' in settings:
                    self.auto_check_interval_var.set(str(settings['auto_check_interval']))
                    self.auto_check_interval_seconds = settings['auto_check_interval']
                
                if 'theme' in settings:
                    self.theme_var.set(settings['theme'])
                    self.change_theme(settings['theme'])
                
                if 'autostart' in settings:
                    self.autostart_var.set(settings['autostart'])
                    # Применяем автозапуск
                    if settings['autostart']:
                        self.set_autostart(True)
                
                if 'auto_start_bypass' in settings:
                    self.auto_start_bypass_var.set(settings['auto_start_bypass'])
                
                if 'last_config' in settings:
                    # Восстанавливаем последнюю конфигурацию в списке
                    if settings['last_config'] in self.configurations:
                        self.config_var.set(settings['last_config'])
                
                # Запускаем автоматическую проверку если включена
                if self.auto_check_enabled:
                    self.start_auto_check()
            except Exception as e:
                self.log_to_console(f"Ошибка загрузки настроек: {str(e)}\n")
        
        # Загружаем Game Filter из флага (для совместимости)
        flag_file = self.bin_path / "game_filter.enabled"
        if flag_file.exists() and not self.settings_file.exists():
            self.game_filter_var.set("enabled")
            self.game_filter_switch.select()
    
    def save_last_config(self, config_name):
        """Сохраняет последнюю использованную конфигурацию"""
        try:
            settings = {}
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            settings['last_config'] = config_name
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass  # Игнорируем ошибки сохранения
    
    def auto_start_last_bypass(self):
        """Автоматически запускает последний использованный bypass при старте"""
        if not self.auto_start_bypass_var.get():
            return
        
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                if 'last_config' in settings:
                    last_config = settings['last_config']
                    if last_config in self.configurations:
                        # Небольшая задержка для полной инициализации интерфейса
                        self.root.after(2000, lambda: self.run_bat_file(last_config))
                        self.log_to_console(f"Автозапуск последнего bypass: {last_config}\n")
        except Exception as e:
            pass  # Игнорируем ошибки
    
    def toggle_auto_start_bypass(self):
        """Переключает автозапуск последнего bypass"""
        self.save_settings()
    
    def save_settings(self):
        """Сохраняет настройки в файл"""
        try:
            # Загружаем существующие настройки чтобы сохранить last_config
            settings = {}
            if self.settings_file.exists():
                try:
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                except:
                    pass
            
            # Обновляем настройки
            settings.update({
                'game_filter': self.game_filter_var.get(),
                'ipset_mode': self.ipset_var.get(),
                'auto_check': self.auto_check_var.get(),
                'auto_check_interval': int(self.auto_check_interval_var.get()),
                'theme': self.theme_var.get(),
                'autostart': self.autostart_var.get(),
                'auto_start_bypass': self.auto_start_bypass_var.get()
            })
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log_to_console(f"Ошибка сохранения настроек: {str(e)}\n")
    
    def update_status_label(self, text):
        """Обновляет текст в строке статуса"""
        self.status_label.configure(text=text)
    
    def run(self):
        """Запускает приложение"""
        if self.is_admin:
            self.log_to_console("Приложение запущено с правами администратора ✓\n")
        else:
            self.log_to_console("⚠ ВНИМАНИЕ: Приложение запущено без прав администратора\n")
            self.log_to_console("Некоторые функции могут не работать. Перезапустите с правами администратора.\n")
        self.log_to_console(f"Рабочая директория: {self.script_dir}\n\n")
        self.root.mainloop()

if __name__ == "__main__":
    # Проверка прав администратора и автоматический запрос
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            # Автоматический запрос прав администратора
            try:
                # Перезапускаем с правами администратора
                if sys.argv[-1] != 'asadmin':
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable, f'"{__file__}" asadmin', None, 1
                    )
                    sys.exit(0)
            except Exception as e:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось запросить права администратора: {str(e)}\n\n"
                    "Запустите приложение вручную от имени администратора."
                )
                sys.exit(1)
    except Exception as e:
        print(f"Ошибка проверки прав администратора: {e}")
    
    app = ZapretGUI()
    app.run()
