import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from socketserver import ThreadingMixIn
from typing import Type, Optional

from src.core.background_task.schedule import get_task_scheduler
from src.core.background_task.task import NativePythonFuncThreadBackgroundTask
from src.core.types.atomic import CustomAtomicType, String, Table
from http.server import BaseHTTPRequestHandler, HTTPServer


class Server(CustomAtomicType):
    def __init__(self, server: HTTPServer):
        super().__init__()
        self.server = server

    def __str__(self) -> str:
        return "HTTP Сервер"

    @classmethod
    def type_name(cls):
        return "HTTPСервер"


class HTTPRequestHandler(CustomAtomicType):
    def __init__(self, handler: Type[BaseHTTPRequestHandler]):
        super().__init__()
        self.handler = handler

    def __str__(self) -> str:
        return "HTTP Обработчик"

    @classmethod
    def type_name(cls):
        return "HTTPОбработчик"


class HTTPRequest(CustomAtomicType):
    def __init__(
            self, body: String, headers: Table, path: String, query_params: Table, method: String,
            ip_address: String = String("unknown"), cookies: Optional[Table] = None
    ):
        super().__init__()
        self.context = Table()
        self.body = body
        self.headers = headers
        self.path = path
        self.query_params = query_params
        self.ip_address = ip_address
        self.cookies = cookies if cookies is not None else Table()
        self.content_type = self.headers.get(String("Content-type"), String("text/plain"))
        self.timestamp = String(datetime.now().isoformat())
        self.method = method

        self.fields = {
            "контекст": self.context,
            "тело": self.body,
            "заголовки": self.headers,
            "путь": self.path,
            "параметры_запроса": self.query_params,
            "адрес": self.ip_address,
            "куки": self.cookies,
            "тип_контента": self.content_type,
            "время_запроса": self.timestamp,
            "метод": self.method,
        }

    def __str__(self) -> str:
        return f"HTTP Запрос(тело={self.body}, заголовки={self.headers})"

    @classmethod
    def type_name(cls):
        return "HTTPЗапрос"


class HTTPDriver(CustomAtomicType):
    def __init__(self, driver: Type[HTTPServer]):
        super().__init__()
        self.driver = driver

    def __str__(self) -> str:
        return f"HTTP Движок(движок={self.driver})"

    @classmethod
    def type_name(cls):
        return "HTTPДвижок"


class ConfigServerMixIn:
    allow_reuse_address = True
    request_queue_size = 128


class ThreadPoolHTTPServerImpl(ThreadingMixIn, ConfigServerMixIn, HTTPServer):
    daemon_threads = True

    def __init__(self, *args, max_workers=os.cpu_count(), **kwargs):
        super().__init__(*args, **kwargs)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def process_request(self, request, client_address):
        self.executor.submit(
            self.process_request_thread,
            request,
            client_address
        )


class SyncHTTPServerImpl(ConfigServerMixIn, HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AsyncHTTPServerImpl(SyncHTTPServerImpl):
    def process_request_task(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception as e:
            print(e)
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        get_task_scheduler().schedule_task(
            NativePythonFuncThreadBackgroundTask(
                "обработчик_интернет_запроса", self.process_request_task, request, client_address
            )
        )
