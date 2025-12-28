"""
Скрипт для сборки Zapret GUI в один исполняемый файл
Использование: python build_exe.py
"""
import PyInstaller.__main__
import os
from pathlib import Path

# Путь к текущей директории
script_dir = Path(__file__).parent.absolute()

# Параметры сборки
options = [
    'zapret_gui.py',           # Главный файл
    '--onefile',                # Один файл
    '--windowed',               # Без консоли (GUI приложение)
    '--name=ZapretGUI',         # Имя исполняемого файла
    '--clean',                  # Очистить кеш перед сборкой
    '--noconfirm',              # Перезаписать без подтверждения
    
    # Иконка
    icon_path = script_dir / 'icon.ico'
    if icon_path.exists():
        options.append(f'--icon={icon_path}')
        print(f"Используется иконка: {icon_path}")
    else:
        print("Иконка не найдена. Создайте icon.ico или запустите create_icon.py")
    
    # Скрытые импорты
    '--hidden-import=customtkinter',
    '--hidden-import=tkinter',
    '--hidden-import=tkinter.scrolledtext',
    '--hidden-import=ctypes',
    '--hidden-import=urllib',
    '--hidden-import=urllib.request',
    '--hidden-import=socket',
    
    # Добавляем данные если нужно
    # f'--add-data={script_dir / "lists"};lists',
    # f'--add-data={script_dir / "bin"};bin',
    
    # Дополнительные опции
    '--exclude-module=matplotlib',
    '--exclude-module=numpy',
    '--exclude-module=pandas',
]

print("=" * 60)
print("Сборка Zapret GUI в исполняемый файл")
print("=" * 60)
print("\nПараметры сборки:")
for opt in options:
    print(f"  {opt}")
print("\nНачинаю сборку...\n")

try:
    PyInstaller.__main__.run(options)
    print("\n" + "=" * 60)
    print("✅ Сборка завершена успешно!")
    print(f"Исполняемый файл находится в: {script_dir / 'dist' / 'ZapretGUI.exe'}")
    print("=" * 60)
except Exception as e:
    print(f"\n❌ Ошибка при сборке: {e}")
    print("\nУбедитесь что установлен PyInstaller:")
    print("  python -m pip install pyinstaller")
    input("\nНажмите Enter для выхода...")

