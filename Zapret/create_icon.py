"""
Создает простую иконку для приложения
Требуется: pip install pillow
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Создает иконку 256x256 для приложения"""
    size = 256
    img = Image.new('RGB', (size, size), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # Рисуем замок (символ безопасности)
    lock_size = 120
    lock_x = (size - lock_size) // 2
    lock_y = (size - lock_size) // 2 - 20
    
    # Круг (верхняя часть замка)
    draw.ellipse(
        [lock_x + 20, lock_y, lock_x + lock_size - 20, lock_y + 60],
        fill='#00d4ff',
        outline='#0099cc',
        width=4
    )
    
    # Корпус замка
    draw.rectangle(
        [lock_x + 30, lock_y + 40, lock_x + lock_size - 30, lock_y + lock_size - 20],
        fill='#00d4ff',
        outline='#0099cc',
        width=4
    )
    
    # Замочная скважина
    draw.ellipse(
        [lock_x + lock_size // 2 - 15, lock_y + 60, lock_x + lock_size // 2 + 15, lock_y + 90],
        fill='#1a1a2e'
    )
    draw.rectangle(
        [lock_x + lock_size // 2 - 4, lock_y + 90, lock_x + lock_size // 2 + 4, lock_y + lock_size - 30],
        fill='#1a1a2e'
    )
    
    # Сохраняем как ICO
    img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print("Иконка создана: icon.ico")
    
    # Также сохраняем PNG для предпросмотра
    img.save('icon.png', format='PNG')
    print("Предпросмотр создан: icon.png")

if __name__ == "__main__":
    try:
        create_icon()
    except ImportError:
        print("Требуется установить Pillow: pip install pillow")
    except Exception as e:
        print(f"Ошибка: {e}")



