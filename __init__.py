from .guisher import Window, show_cnt

__all__ = ['Window', 'show_cnt']

def create_window(width=400, height=300, title="Guisher Window"):
    """Создает новое окно"""
    return Window(width, height, title)

def run():
    """Запускает главный цикл приложения"""
    # В нашей реализации главный цикл запускается при вызове show()
    pass
