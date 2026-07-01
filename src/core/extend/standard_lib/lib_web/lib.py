from http.server import HTTPServer
from typing import Optional

from pathlib import Path

from src.core.extend.function_wrap import PyExtendWrapper, PyExtendBuilder
from src.core.extend.standard_lib.lib_web.util import HTTPRequestHandler, Server, HTTPDriver
from src.core.types.atomic import String, Number, Table, Array, convert_atomic_type_to_py_type
from src.core.types.basetype import BaseAtomicType

builder = PyExtendBuilder()
standard_lib_path = f"{Path(__file__).resolve().parent.parent}/modules/_/"
MOD_NAME = "web"


@builder.collect(func_name='запрос_в_интернет')
class Request(PyExtendWrapper):
    def __init__(self, func_name: str):
        super().__init__(func_name)
        self.empty_args = False
        self.offset_required_args = 3
        self.count_args = 6

    def call(self, args: Optional[list[BaseAtomicType]] = None):
        import json

        import requests

        from src.core.types.atomic import Table, String, Number, Boolean, convert_py_type_to_atomic_type
        from src.core.exceptions import ErrorType, ErrorValue, HttpError

        headers = Table()
        cookies = Table()
        timeout = Number(30)

        if len(args) == self.offset_required_args:
            method, url, data = args
        else:
            method, url, data, *tail = args

            headers = tail[0]

            if len(tail) == 2:
                cookies = tail[1]

            elif len(tail) == 3:
                cookies = tail[1]
                timeout = tail[2]

        if not isinstance(method, String):
            raise ErrorType(f"Первый аргумент должен иметь тип '{String.type_name()}'!")

        if not isinstance(url, String):
            raise ErrorType(f"Второй аргумент должен иметь тип '{String.type_name()}'!")

        if not isinstance(data, Table):
            raise ErrorType(f"Третий аргумент должен иметь тип '{Table.type_name()}'!")

        if not isinstance(headers, Table):
            raise ErrorType(f"Четвертый аргумент должен иметь тип '{Table.type_name()}'!")

        if not isinstance(cookies, Table):
            raise ErrorType(f"Пятый аргумент должен иметь тип '{Table.type_name()}'!")

        method, url, data, *_ = self.parse_args(args)
        headers, cookies, timeout = [convert_atomic_type_to_py_type(arg) for arg in [headers, cookies, timeout]]

        methods_map = {
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "HEAD",
            "OPTIONS",
            "PATCH",
        }

        if method not in methods_map:
           raise ErrorValue(
               f"Первый аргумент принимает только одно из этих значений: {list(methods_map)}, но не '{method}'"
           )

        try:
            resp = requests.request(method, url, data=data, headers=headers, cookies=cookies, timeout=timeout)
        except requests.exceptions.RequestException as e:
            raise HttpError(msg=f"При запросе произошла ошибка. Детали: '{e}'")

        try:
            json_data = resp.json()
        except json.JSONDecodeError:
            json_data = {}

        text_data = resp.text

        result = Table({
            String("статус_код"): Number(resp.status_code),
            String("заголовки"): convert_py_type_to_atomic_type(resp.headers),
            String("cookies"): convert_py_type_to_atomic_type(resp.cookies),
            String("json"): convert_py_type_to_atomic_type(json_data),
            String("текст"): String(text_data),
            String("успешно"): Boolean(resp.status_code < 400),
        })

        return result


@builder.collect(func_name='многопоточный_серверный_движок')
class CreateServer(PyExtendWrapper):
    def __init__(self, func_name: str):
        super().__init__(func_name)
        self.count_args = 0
        self.empty_args = True

    def call(self, args: Optional[list[BaseAtomicType]] = None):
        from src.core.extend.standard_lib.lib_web.util import ThreadPoolHTTPServerImpl

        return HTTPDriver(ThreadPoolHTTPServerImpl)


@builder.collect(func_name='асинхронный_серверный_движок')
class CreateServer(PyExtendWrapper):
    def __init__(self, func_name: str):
        super().__init__(func_name)
        self.count_args = 0
        self.empty_args = True

    def call(self, args: Optional[list[BaseAtomicType]] = None):
        from src.core.extend.standard_lib.lib_web.util import AsyncHTTPServerImpl

        return HTTPDriver(AsyncHTTPServerImpl)


@builder.collect(func_name='создать_сервер')
class CreateServer(PyExtendWrapper):
    def __init__(self, func_name: str):
        super().__init__(func_name)
        self.count_args = 4
        self.signature = (String, Number, HTTPRequestHandler, HTTPDriver)

    def call(self, args: Optional[list[BaseAtomicType]] = None):
        from src.core.extend.standard_lib.lib_web.util import Server

        host, port, handler, driver = args

        return Server(driver.driver((host.value, port.value), handler.handler))


@builder.collect(func_name='запустить_сервер')
class RunServer(PyExtendWrapper):
    def __init__(self, func_name: str):
        super().__init__(func_name)
        self.count_args = 1
        self.signature = (Server,)

    def call(self, args: Optional[list[BaseAtomicType]] = None):
        from src.core.types.atomic import VOID

        server: Server = args[0]

        server.server.serve_forever()

        return VOID


@builder.collect(func_name='создать_обработчик_запросов')
class CreateRequestHandler(PyExtendWrapper):
    def __init__(self, func_name: str):
        super().__init__(func_name)
        self.count_args = 2
        self.signature = (Table, Array)
        self._callable_wrap = builder.callable_wrapper

    def call(self, args: Optional[list[BaseAtomicType]] = None):
        from urllib.parse import urlparse, parse_qs

        from http.server import BaseHTTPRequestHandler
        from src.core.extend.standard_lib.lib_web.util import HTTPRequestHandler, HTTPRequest
        from src.core.types.atomic import (
            String, Table, Array,
            convert_atomic_type_to_py_type, convert_py_type_to_atomic_type
        )
        from src.core.types.procedure import Procedure
        from src.util.console_worker import printer

        enclosed_self = self
        handlers: Table[Procedure] = args[0]
        middlewares: Array[Procedure] = args[1]

        class Handler(BaseHTTPRequestHandler):
            def _response_render(self, response: BaseAtomicType):
                fields = {}

                for key, atomic in response.fields.items():
                    fields[key] = convert_atomic_type_to_py_type(atomic.value, strict=True)

                self.send_response(fields.get("статус_код", 500))

                for key, value in fields.get("заголовки", {}).items():
                    self.send_header(key, value)

                self.end_headers()

                try:
                    self.wfile.write(fields.get("тело", "Ошибка сервера").encode())
                except Exception as e:
                    printer.print_error(str(e))

            def _handle(self, http_method: str):
                nonlocal enclosed_self
                nonlocal middlewares
                nonlocal handlers

                content_length = int(self.headers.get('Content-Length', 0))

                parsed = urlparse(self.path)
                path_only = parsed.path
                query_params = parse_qs(parsed.query)
                converted_query_params = {}

                for key, param in query_params.items():
                    converted_query_params[String(key)] = convert_py_type_to_atomic_type(param)

                body = ""

                if content_length > 0:
                    body_bytes = self.rfile.read(content_length)
                    body = body_bytes.decode("utf-8")

                converted_headers: Table = convert_py_type_to_atomic_type(dict(self.headers)) # type: ignore

                cookies = {}
                if "Cookie" in self.headers:
                    for c in self.headers["Cookie"].split(';'):
                        if '=' in c:
                            k, v = c.strip().split('=', 1)
                            cookies[String(k)] = convert_py_type_to_atomic_type(v)

                request = HTTPRequest(
                    method=String(http_method),
                    path=String(path_only),
                    query_params=Table(converted_query_params),
                    body=String(body),
                    headers=converted_headers,
                    ip_address=String(self.client_address[0]),
                    cookies=Table(cookies),
                )

                for middleware in middlewares.value:
                    enclosed_self.run_procedure(middleware, [request])
                    if request.context.get(String("прервать")).value:
                        response = request.context[String("прервать")]

                        self._response_render(response)
                        return

                get_http_method_handlers = handlers.get(String(http_method))
                handler = get_http_method_handlers.get(String(path_only), handlers.get(String("404")))

                response = enclosed_self.run_procedure(handler, [String(path_only), request])

                self._response_render(response)

            def do_GET(self):
                self._handle("GET")

            def do_POST(self):
                self._handle("POST")

            def do_PATCH(self):
                self._handle("PATCH")

            def do_PUT(self):
                self._handle("PUT")

            def do_DELETE(self):
                self._handle("DELETE")

            def do_HEAD(self):
                self._handle("HEAD")

            def do_OPTIONS(self):
                self._handle("OPTIONS")

        for method in ("GET", "POST", "PATCH", "PUT", "DELETE", "HEAD", "OPTIONS"):
            original = getattr(Handler, f"do_{method}")
            wrapped = self._callable_wrap.callable_py_wrap(original, f"{method}_обработчик")
            setattr(Handler, f"do_{method}", wrapped)

        return HTTPRequestHandler(Handler)


def build_module():
    builder.build_python_extend(f"{standard_lib_path}{MOD_NAME}")


if __name__ == '__main__':
    build_module()
