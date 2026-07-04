from typing import Type

from src.core.exceptions import InvalidSyntaxError
from src.core.parse.base import parse_execute, Parser, MetaObject
from src.core.parse.classes.define_class import DefineClassParser
from src.core.parse.procedure.define_execute_block import DefineExecuteBlockParser
from src.core.parse.procedure.define_procedure import DefineProcedureParser
from src.core.tokens import Tokens
from src.core.types.line import Line
from src.core.util import is_ignore_line
from src.util.build_tools.compile import Compiled
from src.util.console_worker import printer


class AbstractSyntaxTreeBuilder:
    def __init__(self, code: list[Line]):
        self.code = code
        self.meta_code = []
        self.jump = -1
        printer.logging("Инициализация AbstractSyntaxTreeBuilder", level="INFO")

    def create_meta(self, parser: Type[Parser], num: int):
        parser = parser()
        meta = parse_execute(parser, self.code, num)
        self.jump = meta.stop_num
        self.meta_code.append(meta)
        printer.logging(
            f"Создана мета-структура с использованием {parser.__class__.__name__} на строке {num}",
            level="INFO"
        )

    def build(self) -> list[MetaObject]:
        for num, line in enumerate(self.code):
            if isinstance(line, Compiled):
                self.meta_code.append(line)
                continue

            if num <= self.jump:
                printer.logging(f"Пропуск строки {num} (переход по jump)", level="DEBUG")
                continue

            if is_ignore_line(line):
                printer.logging(f"Игнорирование пустой или комментарий строки {num}", level="DEBUG")
                continue

            match line.split():
                case [Tokens.define, Tokens.a_procedure, *_]:
                    self.create_meta(DefineProcedureParser, num)
                case [Tokens.execute, *_]:
                    self.create_meta(DefineExecuteBlockParser, num)
                case [Tokens.define, Tokens.class_, *_]:
                    self.create_meta(DefineClassParser, num)
                case [Tokens.extend, Tokens.class_, *_]:
                    self.create_meta(DefineClassParser, num)
                case _:
                    printer.logging(f"Ошибка синтаксиса в строке {num}: {line}", level="ERROR")
                    raise InvalidSyntaxError(line=line.split(), info=line.get_file_info())

        printer.logging("Построение AST завершено", level="INFO")
        return self.meta_code
