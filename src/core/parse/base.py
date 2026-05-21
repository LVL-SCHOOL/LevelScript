import re
from abc import ABC, abstractmethod
from typing import Type, Sequence, Union, Optional

from src.core.parse.lexer import Lexer
from src.core.types.basetype import BaseType
from src.core.tokens import Tokens
from src.core.types.line import Line, Info


_INTEGER_PATTERN = re.compile(r"^-?\d+$")
_FLOAT_PATTERN = re.compile(r"^-?\d+(\.\d+)?$")
_IDENTIFIER_PATTERN = re.compile(r"^[А-Яа-яЁёA-Za-z_][А-Яа-яЁёA-Za-z0-9_]*(?::[А-Яа-яЁёA-Za-z_][А-Яа-яЁёA-Za-z0-9_]*)*$")


def is_integer(s: str) -> bool:
    return bool(_INTEGER_PATTERN.match(str(s)))


def is_float(s: str) -> bool:
    return bool(_FLOAT_PATTERN.match(str(s)))


def is_identifier(s: str) -> bool:
    return bool(_IDENTIFIER_PATTERN.match(str(s)))


class Image:
    def __init__(self, name: str, obj: Type[BaseType], image_args: tuple, *, info: Info):
        self.name = name
        self.obj = obj
        self.image_args = image_args
        self.info = info

    def build(self) -> BaseType:
        unpacked_obj = self.obj(self.name, *self.image_args) # noqa
        unpacked_obj.set_info(self.info)

        return unpacked_obj


class MetaObject(ABC):
    def __init__(self, stop_num: int):
        self.__stop_num = stop_num

    @property
    def stop_num(self) -> int: return self.__stop_num

    @abstractmethod
    def create_image(self, *args, **kwargs) -> Image: ...


class Parser(ABC):
    def __init__(self):
        self.jump: int = -1
        self.info: Optional[Info] = None
        self.lexer = Lexer()

    @abstractmethod
    def parse(self, body: list[str], jump: int) -> int: ...

    @abstractmethod
    def create_metadata(self, stop_num: int) -> MetaObject: ...

    @staticmethod
    def parse_sequence_words_to_str(words: Sequence[str]):
        return " ".join(words)

    def execute_parse(
            self, parser: Union["Parser", Type["Parser"]], code: list[Line], num: int
    ) -> Union[MetaObject, BaseType]:
        if isinstance(parser, type) and issubclass(parser, Parser):
            parser = parser()
        meta = parse_execute(parser, code, num)
        self.jump = self.next_num_line(meta.stop_num)

        return meta

    @staticmethod
    def next_num_line(num_line: int) -> int:
        return num_line + 1

    def jump_to_next_line(self):
        self.jump = self.next_num_line(self.jump)

    @staticmethod
    def previous_num_line(num_line: int) -> int:
        return num_line - 1

    def jump_to_previous_line(self):
        self.jump = self.previous_num_line(self.jump)

    @staticmethod
    def auto_added_end_token_for_expr(line: Line):
        raw_data = line.raw_data.rstrip()

        if raw_data in (Tokens.left_bracket, Tokens.right_bracket):
            return

        if raw_data.endswith(Tokens.left_bracket):
            return

        if not raw_data.endswith((Tokens.end_expr, Tokens.comma)):
            line.raw_data = raw_data + Tokens.end_expr

    def separate_line_to_token(self, line: Line) -> list[str]:
        return self.lexer.separate(line)


def parse_execute(parser: Parser, code: list[Line], num_line: int) -> MetaObject:
    stop_num = parser.parse(code, num_line)
    meta = parser.create_metadata(stop_num)

    return meta
