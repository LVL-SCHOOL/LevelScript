from src.core.exceptions import InvalidSyntaxError
from src.core.tokens import Tokens, END_LINE_TOKENS, ServiceTokens, ALIASES_MAP
from src.core.types.line import Line, Info


class Lexer:
    def separate(self, line: Line) -> list[str]:
        self._check_quotes(line)
        raw_line = line.raw_data

        is_string = False

        # Убираем комментарии из сырой строки
        for offset, symbol in enumerate(raw_line):
            if symbol == Tokens.quotation:
                is_string = not is_string

            if is_string:
                continue

            match symbol:
                case Tokens.comment:
                    raw_line = raw_line[:offset].rstrip()
                    break

        end_symbols = END_LINE_TOKENS

        for end_symbol in end_symbols:
            if raw_line.endswith(end_symbol):
                break
        else:
            raise InvalidSyntaxError(
                f"Некорректная строка: '{line.raw_data}', возможно Вы забыли один из этих знаков в конце: "
                f"{", ".join([f"'{s}'" for s in end_symbols])}\n\n"
                f"{line.raw_data}\n{" " * len(line.raw_data)}^\n\n",
                info=line.get_file_info()
            )

        separated_line = self.__split(raw_line)

        tokens = []

        for token in separated_line:
            if token in Tokens:
                tokens.append(token)
                continue

            unknown_token = ""

            for symbol in token:
                if symbol in (
                        Tokens.left_bracket, Tokens.right_bracket, Tokens.comma, Tokens.star,
                        Tokens.left_square_bracket, Tokens.right_square_bracket, Tokens.equal,
                        Tokens.plus, Tokens.minus, Tokens.div, Tokens.quotation, Tokens.exponentiation,
                        Tokens.attr_access
                ):
                    if unknown_token:
                        tokens.append(unknown_token)
                        unknown_token = ""

                    tokens.append(symbol)
                else:
                    unknown_token += symbol

            if unknown_token:
                tokens.append(unknown_token)

        match list(tokens[-1]):
            case [*old, end]:
                if old:
                    tokens[-1] = "".join(old)
                    tokens.append(end)
                else:
                    tokens[-1] = end

        self._check_tokens(tokens, line.get_file_info())
        return self._convert_aliases_to_token(tokens)

    @staticmethod
    def _check_tokens(tokens: list[str], info: Info):
        for token in tokens:
            if token in ServiceTokens:
                raise InvalidSyntaxError(
                    f"Ошибка синтаксиса. Недопустимый токен: '{token}'", info=info
                )

    @staticmethod
    def _convert_aliases_to_token(tokens: list[str]) -> list[str]:
        converted_tokens = []
        is_string = False

        for token in tokens:
            if token == Tokens.quotation:
                is_string = not is_string

            if is_string:
                converted_tokens.append(token)
                continue

            for target, aliases in ALIASES_MAP.items():
                if token in aliases:
                    token = target

            converted_tokens.append(token)

        return converted_tokens

    @staticmethod
    def _check_quotes(line: Line) -> None:
        raw_line = line.raw_data
        count_quotes = sum(1 for symbol in raw_line if symbol == Tokens.quotation)

        if count_quotes % 2 == 1:
            raise InvalidSyntaxError(
                f"Некорректная строка: '{raw_line}', возможно Вы забыли закрывающую кавычку",
                info=line.get_file_info()
            )

    @staticmethod
    def __split(raw_line: str) -> list[str]:
        result = []
        token = ""
        jump = 0

        for offset, symbol in enumerate(raw_line):
            if offset < jump:
                continue

            if symbol == Tokens.quotation:
                result.append(token)
                token = ""

                for sub_offset, sub_symbol in enumerate(raw_line[offset + 1:]):
                    if sub_symbol == Tokens.quotation:
                        result.append(f'"{token}"')
                        token = ""
                        jump = offset + sub_offset + 2
                        break

                    token += sub_symbol
                continue

            if symbol == " ":
                if token:
                    result.append(token)
                    token = ""
                continue

            token += symbol

        result.append(token)
        return result
