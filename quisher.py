import sys
import os
import ctypes
from ctypes import wintypes
import atexit

# Подготовка структур и констант для Windows API
if os.name == 'nt':
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    
    # Константы
    WS_OVERLAPPEDWINDOW = 0x00CF0000
    WS_VISIBLE = 0x10000000
    CW_USEDEFAULT = 0x80000000
    WM_DESTROY = 0x0002
    WM_COMMAND = 0x0111
    WM_PAINT = 0x000F
    COLOR_WINDOW = 5
    IDOK = 1
    IDCANCEL = 2
    DT_CENTER = 0x00000001
    DT_VCENTER = 0x00000004
    DT_SINGLELINE = 0x00000020
    
    # Структуры
    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]
    
    class PAINTSTRUCT(ctypes.Structure):
        _fields_ = [
            ("hdc", wintypes.HDC),
            ("fErase", wintypes.BOOL),
            ("rcPaint", RECT),
            ("fRestore", wintypes.BOOL),
            ("fIncUpdate", wintypes.BOOL),
            ("rgbReserved", wintypes.BYTE * 32),
        ]
    
    class WNDCLASS(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", ctypes.c_void_p),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HANDLE),
            ("hIcon", wintypes.HANDLE),
            ("hCursor", wintypes.HANDLE),
            ("hbrBackground", wintypes.HANDLE),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]

class Window:
    _windows = {}
    _button_handlers = {}
    _next_button_id = 1000
    _labels = {}
    
    def __init__(self, width=400, height=300, title="Guisher Window"):
        self.width = width
        self.height = height
        self.title = title
        self.hwnd = None
        self.controls = []
        self._create_window()
    
    def _create_window(self):
        if os.name != 'nt':
            raise NotImplementedError("guisher currently supports only Windows")
        
        instance = ctypes.windll.kernel32.GetModuleHandleW(None)
        
        class_name = "GuisherWindowClass"
        
        wndclass = WNDCLASS()
        wndclass.lpfnWndProc = ctypes.WINFUNCTYPE(
            ctypes.c_long, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM
        )(self._window_proc)
        wndclass.hInstance = instance
        wndclass.lpszClassName = class_name
        wndclass.hbrBackground = user32.GetSysColorBrush(COLOR_WINDOW)
        
        user32.RegisterClassW(ctypes.byref(wndclass))
        
        self.hwnd = user32.CreateWindowExW(
            0,
            class_name,
            self.title,
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            self.width,
            self.height,
            0,
            0,
            instance,
            None
        )
        
        Window._windows[self.hwnd] = self
        atexit.register(self._cleanup)
    
    def _window_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        elif msg == WM_COMMAND:
            button_id = wparam & 0xFFFF
            if button_id in Window._button_handlers:
                Window._button_handlers[button_id]()
                return 0
        elif msg == WM_PAINT:
            self._handle_paint(hwnd)
            return 0
        
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
    
    def _handle_paint(self, hwnd):
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
        
        for label in self._labels.get(hwnd, []):
            rect = RECT()
            rect.left = label['x']
            rect.top = label['y']
            rect.right = label['x'] + 200
            rect.bottom = label['y'] + 30
            
            user32.DrawTextW(
                hdc,
                str(label['text']),
                -1,
                ctypes.byref(rect),
                DT_SINGLELINE | DT_VCENTER
            )
        
        user32.EndPaint(hwnd, ctypes.byref(ps))
    
    def add_button(self, text, x, y, width=100, height=30, handler=None):
        button_id = Window._next_button_id
        Window._next_button_id += 1
        
        hwnd_button = user32.CreateWindowExW(
            0,
            "BUTTON",
            text,
            0x50000000,  # WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON
            x,
            y,
            width,
            height,
            self.hwnd,
            button_id,
            ctypes.windll.kernel32.GetModuleHandleW(None),
            None
        )
        
        if handler:
            Window._button_handlers[button_id] = handler
        
        self.controls.append(hwnd_button)
        return button_id
    
    def add_label(self, text, x, y):
        if self.hwnd not in self._labels:
            self._labels[self.hwnd] = []
        
        self._labels[self.hwnd].append({
            'text': text,
            'x': x,
            'y': y
        })
        
        user32.InvalidateRect(self.hwnd, None, True)
    
    def update_label(self, label_id, new_text):
        if self.hwnd in self._labels and label_id < len(self._labels[self.hwnd]):
            self._labels[self.hwnd][label_id]['text'] = new_text
            user32.InvalidateRect(self.hwnd, None, True)
    
    def show(self):
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    
    def _cleanup(self):
        if self.hwnd in Window._windows:
            del Window._windows[self.hwnd]

def show_cnt(handler):
    """Декоратор для обработчиков кнопок"""
    return handler
