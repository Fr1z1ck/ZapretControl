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
            if hasattr(sys, '_MEIPASS'):
                self.temp_dir = Path(sys._MEIPASS)
            else:
                self.temp_dir = Path(sys.executable).parent
            self.script_dir = Path(sys.executable).parent.absolute()
        else:
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
        self.youtube_status = None
        self.last_youtube_check = None
        self.current_winws_process = None
        self.auto_check_enabled = False
        self.auto_check_thread = None
        self.auto_check_interval_seconds = 60
        self.settings_file = self.script_dir / "zapret_settings.json"
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
        self.check_youtube_now()
        self.start_traffic_monitor()
        self.auto_start_last_bypass()
    
    def create_widgets(self):
        """Создает полностью переработанный современный интерфейс"""
        # Главный контейнер с градиентом
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
        """Создает страницу управления"""
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
    
    # Все остальные методы остаются без изменений...
    # (extract_embedded_data, load_settings, save_settings, и т.д.)
    
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
                text_color=COLORS['success']
            )
        else:
            self.admin_status_label.configure(
                text="⚠ Не администратор",
                text_color=COLORS['warning']
            )
    
    def log_to_console(self, message):
        """Выводит сообщение в консоль"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_text.insert("end", f"[{timestamp}] {message}")
        if self.console_auto_scroll.get():
            self.console_text.see("end")
        self.root.update_idletasks()
    
    def setup_hotkeys(self):
        """Настраивает горячие клавиши"""
        self.root.bind('<Control-r>', lambda e: self.run_selected_config())
        self.root.bind('<Control-s>', lambda e: self.start_service())
        self.root.bind('<Control-t>', lambda e: self.stop_service())
        self.root.bind('<Control-f>', lambda e: self.find_working_bypass())
        self.root.bind('<Control-y>', lambda e: self.check_youtube_now())
        self.root.bind('<Control-q>', lambda e: self.stop_winws())
        self.root.bind('<F5>', lambda e: self.update_status())
        self.root.bind('<Control-h>', lambda e: self.show_hotkeys_help())
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
    
    # Заглушки для методов, которые нужно будет добавить из оригинального файла
    def extract_embedded_data(self): pass
    def load_settings(self): pass
    def save_settings(self): pass
    def save_last_config(self, config_name): pass
    def auto_start_last_bypass(self): pass
    def toggle_auto_start_bypass(self): pass
    def load_configurations(self, parent_frame): pass
    def run_selected_config(self): pass
    def run_bat_file(self, bat_file): pass
    def stop_winws(self): pass
    def find_working_bypass(self): pass
    def check_youtube_now(self): pass
    def update_status(self): pass
    def install_service(self): pass
    def remove_service(self): pass
    def start_service(self): pass
    def stop_service(self): pass
    def toggle_game_filter(self): pass
    def change_ipset_mode(self, value): pass
    def update_ipset(self): pass
    def toggle_auto_check(self): pass
    def start_auto_check(self): pass
    def stop_auto_check(self): pass
    def change_theme(self, theme): pass
    def toggle_autostart(self): pass
    def set_autostart(self, enabled): pass
    def export_settings(self): pass
    def import_settings(self): pass
    def start_traffic_monitor(self): pass
    def toggle_traffic_monitor(self): pass
    def reset_traffic_stats(self): pass
    def export_traffic_stats(self): pass
    def update_traffic_stats(self): pass
    def update_traffic_display(self): pass
    def format_bytes(self, bytes_count): pass
    def request_admin_restart(self): pass
    def update_status_label(self, text): pass
    
    def run(self):
        """Запускает приложение"""
        if self.is_admin:
            self.log_to_console("Приложение запущено с правами администратора ✓\n")
        else:
            self.log_to_console("⚠ ВНИМАНИЕ: Приложение запущено без прав администратора\n")
        self.log_to_console(f"Рабочая директория: {self.script_dir}\n\n")
        self.root.mainloop()

if __name__ == "__main__":
    app = ZapretGUI()
    app.run()


