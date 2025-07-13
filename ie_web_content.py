import ctypes
import ctypes.wintypes
import atexit
import sys
import os
from threading import Thread
from queue import Queue

if os.name == 'nt':
    ole32 = ctypes.windll.ole32
    oleaut32 = ctypes.windll.oleaut32
    urlmon = ctypes.windll.urlmon
    winhttp = ctypes.windll.winhttp

class IEWebContent:
    """Класс для работы с веб-контентом через Internet Explorer COM API"""
    
    def __init__(self):
        self._init_com()
        self._browser = None
        self._event_queue = Queue()
        atexit.register(self.cleanup)
    
    def _init_com(self):
        """Инициализация COM"""
        ole32.CoInitialize(0)
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self._browser:
            self._browser.Quit()
            self._browser = None
        ole32.CoUninitialize()
    
    def create_browser(self, visible=True):
        """Создает экземпляр IE браузера"""
        CLSID_WebBrowser = "{8856F961-340A-11D0-A96B-00C04FD705A2}"
        
        clsid = ctypes.create_string_buffer(ctypes.sizeof(ctypes.wintypes.IID))
        ole32.CLSIDFromString(CLSID_WebBrowser, ctypes.byref(clsid))
        
        pUnknown = ctypes.c_void_p()
        ole32.CoCreateInstance(
            ctypes.byref(clsid),
            None,
            0x1,  # CLSCTX_INPROC_SERVER
            ctypes.byref(ctypes.wintypes.IID(ctypes.wintypes.IID.from_progid("Unknown"))),
            ctypes.byref(pUnknown)
        )
        
        pWebBrowser = ctypes.c_void_p()
        ole32.IIDFromString("{0002DF05-0000-0000-C000-000000000046}", ctypes.byref(clsid))
        pUnknown.QueryInterface(ctypes.byref(clsid), ctypes.byref(pWebBrowser))
        
        self._browser = ctypes.cast(pWebBrowser, ctypes.POINTER(ctypes.c_void_p))
        
        if visible:
            self._browser.put_Visible(True)
    
    def navigate(self, url):
        """Переходит по указанному URL"""
        if not self._browser:
            self.create_browser()
        
        variant_url = ctypes.wintypes.VARIANT()
        oleaut32.VariantInit(ctypes.byref(variant_url))
        variant_url.vt = 8  # VT_BSTR
        variant_url.bstrVal = ctypes.c_wchar_p(url)
        
        self._browser.Navigate(ctypes.byref(variant_url), 0, 0, 0, 0)
    
    def get_html(self):
        """Получает HTML содержимое текущей страницы"""
        if not self._browser:
            return ""
        
        pDocument = ctypes.c_void_p()
        self._browser.get_Document(ctypes.byref(pDocument))
        
        if not pDocument:
            return ""
        
        pHtmlDocument2 = ctypes.c_void_p()
        ole32.IIDFromString("{332C4425-26CB-11D0-B483-00C04FD90119}", ctypes.byref(ctypes.wintypes.IID()))
        pDocument.QueryInterface(ctypes.byref(ctypes.wintypes.IID()), ctypes.byref(pHtmlDocument2))
        
        if not pHtmlDocument2:
            return ""
        
        pBody = ctypes.c_void_p()
        pHtmlDocument2.get_body(ctypes.byref(pBody))
        
        if not pBody:
            return ""
        
        pInnerHtml = ctypes.c_wchar_p()
        pBody.get_innerHTML(ctypes.byref(pInnerHtml))
        
        html = pInnerHtml.value if pInnerHtml else ""
        
        # Освобождаем ресурсы
        if pInnerHtml:
            oleaut32.SysFreeString(pInnerHtml)
        if pBody:
            pBody.Release()
        if pHtmlDocument2:
            pHtmlDocument2.Release()
        if pDocument:
            pDocument.Release()
        
        return html
    
    def download_file(self, url, local_path):
        """Скачивает файл по URL"""
        hr = urlmon.URLDownloadToFileW(
            0,  # pCaller
            url,
            local_path,
            0,  # dwReserved
            0   # lpfnCB
        )
        return hr == 0  # S_OK
    
    def http_request(self, url, method="GET", headers=None):
        """Выполняет HTTP запрос через WinHTTP"""
        hSession = winhttp.WinHttpOpen(
            "Python IEWebContent/1.0",
            0,  # WINHTTP_ACCESS_TYPE_DEFAULT_PROXY
            0,  # WINHTTP_NO_PROXY_NAME
            0,  # WINHTTP_NO_PROXY_BYPASS
            0   # dwFlags
        )
        
        if not hSession:
            return None
        
        hConnect = winhttp.WinHttpConnect(
            hSession,
            ctypes.c_wchar_p(self._get_host_from_url(url)),
            self._get_port_from_url(url),
            0
        )
        
        if not hConnect:
            winhttp.WinHttpCloseHandle(hSession)
            return None
        
        hRequest = winhttp.WinHttpOpenRequest(
            hConnect,
            method,
            ctypes.c_wchar_p(self._get_path_from_url(url)),
            None,  # pwszVersion
            None,  # pwszReferrer
            None,  # ppwszAcceptTypes
            0      # dwFlags
        )
        
        if not hRequest:
            winhttp.WinHttpCloseHandle(hConnect)
            winhttp.WinHttpCloseHandle(hSession)
            return None
        
        if headers:
            for header in headers:
                winhttp.WinHttpAddRequestHeaders(
                    hRequest,
                    header,
                    -1,  # WINHTTP_ADDREQ_FLAG_ADD
                    0    # dwModifiers
                )
        
        winhttp.WinHttpSendRequest(
            hRequest,
            None,  # pwszHeaders
            0,     # dwHeadersLength
            None,  # lpOptional
            0,     # dwOptionalLength
            0,     # dwTotalLength
            0      # dwContext
        )
        
        winhttp.WinHttpReceiveResponse(hRequest, 0)
        
        # Читаем ответ
        dwSize = ctypes.wintypes.DWORD()
        winhttp.WinHttpQueryDataAvailable(hRequest, ctypes.byref(dwSize))
        
        data = bytearray()
        while dwSize.value > 0:
            buffer = (ctypes.c_byte * dwSize.value)()
            dwDownloaded = ctypes.wintypes.DWORD()
            
            winhttp.WinHttpReadData(
                hRequest,
                ctypes.byref(buffer),
                dwSize,
                ctypes.byref(dwDownloaded)
            )
            
            data.extend(buffer[:dwDownloaded.value])
            winhttp.WinHttpQueryDataAvailable(hRequest, ctypes.byref(dwSize))
        
        # Освобождаем ресурсы
        winhttp.WinHttpCloseHandle(hRequest)
        winhttp.WinHttpCloseHandle(hConnect)
        winhttp.WinHttpCloseHandle(hSession)
        
        return bytes(data)
    
    def _get_host_from_url(self, url):
        # Упрощенная реализация для демонстрации
        if "://" in url:
            return url.split("://")[1].split("/")[0].split(":")[0]
        return url.split("/")[0].split(":")[0]
    
    def _get_port_from_url(self, url):
        if "://" in url:
            host_part = url.split("://")[1].split("/")[0]
            if ":" in host_part:
                return int(host_part.split(":")[1])
        return 80 if url.startswith("http://") else 443
    
    def _get_path_from_url(self, url):
        if "://" in url:
            return "/" + "/".join(url.split("://")[1].split("/")[1:])
        return "/" + "/".join(url.split("/")[1:])
