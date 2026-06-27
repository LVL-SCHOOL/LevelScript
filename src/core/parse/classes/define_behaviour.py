from src.core.exceptions import InvalidSyntaxError
from src.core.parse.classes.define_method import DefineMethodParser
from src.core.tokens import Tokens, BEHAVIOURS_TOKENS
from src.core.types.line import Line
from src.core.util import is_ignore_line
from src.util.console_worker import printer


class DefineBehaviourParser(DefineMethodParser):
    def parse(self, body: list[Line], jump) -> int:
        self.jump = jump

        for num, line in enumerate(body):
            if num < self.jump:
                continue

            if is_ignore_line(line):
                printer.logging(f"Игнорируем строку: {line}", level="INFO")
                continue

            self.info = line.get_file_info()
            line = self.separate_line_to_token(line)

            match line:
                case [
                    Tokens.define, Tokens.behaviour, Tokens.left_bracket, this, Tokens.right_bracket,
                    behaviour_name, Tokens.left_bracket, *arguments, Tokens.right_bracket, Tokens.left_bracket
                ]:
                    if behaviour_name not in BEHAVIOURS_TOKENS:
                        raise InvalidSyntaxError(
                            f"Невозможно определить поведение '{behaviour_name}'",
                            info=self.info,
                        )
                    self.parse_define_procedure(body, behaviour_name, arguments, num, self.info)
                    self.this  = this
                case [Tokens.right_bracket]:
                    return num
                case _:
                    printer.logging(f"Неверный синтаксис: {line}", level="ERROR")
                    raise InvalidSyntaxError(info=self.info)

        raise InvalidSyntaxError(info=self.info)
