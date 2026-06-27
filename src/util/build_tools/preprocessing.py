import os
import re
from typing import Optional, Union

from pathlib import Path
import dill

from config import settings
from src.core.tokens import Tokens
from src.core.types.line import Line
from src.core.util import kill_process
from src.util.build_tools.compile import Compiled


class Comment: ...


COMMENT_MARK = Comment()
STANDARD_LIB_PATH = Path(__file__).resolve().parent.parent.parent
STANDARD_LIB_PATH = f"{STANDARD_LIB_PATH}{settings.standard_lib_path_postfix}"
STD_NAME = settings.std_name


def _standard_lib_alias(path: str) -> str:
    if _is_std(path):
        return path.replace(STD_NAME, STANDARD_LIB_PATH)

    return path


def _is_std(path: str) -> bool:
    return STD_NAME in path


def import_preprocess(path, byte_mode: Optional[bool] = True) -> Union[Compiled, str]:
    try:
        if byte_mode:
            with open(path, "rb") as file:
                compiled = dill.load(file)
                return compiled

        with open(path, "r", encoding="utf-8") as file:
            raw_code = file.read()
            return raw_code

    except FileNotFoundError:
        raise FileNotFoundError
    except RecursionError as e:
        raise e


def delete_end_expr_for_include_directive(directive: list[str]):
    if not directive:
        return directive

    first_token, last_token = directive[0], directive[-1]

    if not first_token.startswith(Tokens.include):
        return directive

    if Tokens.end_expr in last_token:
        index_end_expr = last_token.find(Tokens.end_expr)
        directive[-1] = last_token[:index_end_expr]

        return directive

    return directive


def _file_priority(filename: str) -> int:
    if filename.endswith(f".{settings.compiled_postfix}"):
        return 0
    elif filename.endswith(f".{settings.py_extend_postfix}"):
        return 1
    elif filename.endswith(f".{settings.raw_postfix}"):
        return 2
    return 3


class Preprocessor:
    def __init__(self):
        self.imports = set()

    def preprocess(self, raw_code, path: str) -> list:
        folder = os.path.dirname(path)

        raw_prepared_code = [line.strip() for line in raw_code.split("\n")]
        prepared_code = []
        code = []

        for line in raw_prepared_code:
            is_string = False
            clean_line = ""

            if line.startswith(Tokens.comment):
                prepared_code.append(COMMENT_MARK)
                continue

            for symbol in line:
                clean_line += symbol

                if symbol == Tokens.quotation:
                    is_string = not is_string

                if is_string:
                    continue

                if symbol == Tokens.comment:
                    clean_line = clean_line[:-1]
                    prepared_code.append(clean_line)
                    break
            else:
                prepared_code.append(clean_line)

        for offset, line in enumerate(prepared_code):
            if not line:
                continue

            if isinstance(line, Comment):
                continue

            if Tokens.end_expr in line and not line.startswith(Tokens.comment):
                count_end_expr = 0
                is_string = False
                current_expr = ""
                exprs = []

                for offset_, symbol in enumerate(line):
                    current_expr += symbol

                    if symbol == Tokens.quotation:
                        is_string = not is_string

                    if is_string:
                        continue

                    if symbol == Tokens.comment:
                        exprs.append(current_expr[:-1])
                        break

                    if symbol == Tokens.end_expr:
                        count_end_expr += 1
                        exprs.append(current_expr)
                        current_expr = ""
                else:
                    exprs.append(current_expr)

                if not exprs:
                    continue

                for offset_, expr in enumerate(exprs):
                    if not expr or not expr.replace(" ", ""):
                        continue

                    end = ""

                    add_expr_conditions = (
                        not expr.endswith(Tokens.end_expr),
                        not expr.endswith(Tokens.left_bracket),
                        not expr.endswith(Tokens.comma),
                    )

                    if all(add_expr_conditions):
                        end = Tokens.end_expr

                    line_ = Line(expr.strip() + end, num=offset + 1, file=path)
                    line_.raw_line = line
                    code.append(line_)

                continue

            code.append(Line(line.strip(), num=offset + 1, file=path))

        preprocessed = []

        for offset, line in enumerate(code):
            separate_line = delete_end_expr_for_include_directive(line.split(" "))

            match separate_line:
                case [Tokens.include, package] if package.endswith(Tokens.star):
                    is_std_path = _is_std(package)
                    package = _standard_lib_alias(package)

                    if package in self.imports:
                        continue

                    self.imports.add(package)

                    # Удаляем * из пути и получаем директорию
                    package = package[:-1].replace(Tokens.dot, "/")

                    dir_path = os.path.dirname(package)

                    if not is_std_path:
                        dir_path = os.path.join(os.getcwd(), f"{folder}/{package}")
                    try:
                        files = os.listdir(dir_path)
                    except FileNotFoundError:
                        kill_process(f"Модуль для включения не найден: '{dir_path}'")

                    try:
                        checked_files = set()

                        # Сортируем файлы по приоритету: compiled -> py_extend -> raw
                        files.sort(key=_file_priority)

                        for filename in files:
                            file_without_ext = os.path.splitext(filename)[0]

                            if file_without_ext in checked_files:
                                continue

                            if filename.endswith(f".{settings.compiled_postfix}"):
                                file_path = os.path.join(dir_path, filename)
                                preprocessed.append(import_preprocess(file_path))
                                checked_files.add(file_without_ext)
                            elif filename.endswith(f".{settings.py_extend_postfix}"):
                                file_path = os.path.join(dir_path, filename)
                                preprocessed.append(import_preprocess(file_path))
                                checked_files.add(file_without_ext)
                            elif filename.endswith(f".{settings.raw_postfix}"):
                                file_path = os.path.join(dir_path, filename)
                                preprocessed.extend(self.preprocess(
                                    import_preprocess(file_path, byte_mode=False), file_path)
                                )
                                checked_files.add(file_without_ext)

                    except RecursionError:
                        kill_process(
                            f"Обнаружен циклический импорт '{path}', {line}"
                        )

                case [Tokens.include, module] if re.search(r'\.\S+$', module):
                    is_std_path = _is_std(module)
                    module = _standard_lib_alias(module)

                    if module in self.imports:
                        continue

                    self.imports.add(module)

                    module = module.replace(".", "/", module.count("."))
                    path = module

                    if not is_std_path:
                        path = os.path.join(os.getcwd(), f"{folder}/{module}")

                    law_path = (f"{path}.{settings.compiled_postfix}", True)
                    pyl_path = (f"{path}.{settings.py_extend_postfix}", True)
                    raw_path = (f"{path}.{settings.raw_postfix}", False)

                    for path_data in [law_path, pyl_path, raw_path]:
                        path_, byte_mode = path_data

                        try:
                            if not byte_mode:
                                preprocessed.extend(
                                    self.preprocess(import_preprocess(path_, byte_mode=byte_mode), path_)
                                )
                            else:
                                preprocessed.append(import_preprocess(path_, byte_mode=byte_mode))
                        except FileNotFoundError:
                            continue
                        except RecursionError:
                            kill_process(
                                f"Обнаружен циклический импорт '{path}', {line}"
                            )
                        else:
                            break

                    else:
                        kill_process(f"Невозможно включить модуль. Модуль '{path}' не найден.")

                case [Tokens.include, module]:
                    if module in self.imports:
                        continue

                    self.imports.add(module)

                    module = module.replace(Tokens.dot, "/")
                    path = os.path.join(os.getcwd(), f"{folder}/{module}")

                    law_path = (f"{path}.{settings.compiled_postfix}", True)
                    pyl_path = (f"{path}.{settings.py_extend_postfix}", True)
                    raw_path = (f"{path}.{settings.raw_postfix}", False)

                    for path_data in [law_path, pyl_path, raw_path]:
                        path_, byte_mode = path_data

                        try:
                            if not byte_mode:
                                preprocessed.extend(
                                    self.preprocess(import_preprocess(path_, byte_mode=byte_mode), path_)
                                )
                            else:
                                preprocessed.append(import_preprocess(path_, byte_mode=byte_mode))
                        except FileNotFoundError:
                            continue
                        except RecursionError:
                            kill_process(
                                f"Обнаружен циклический импорт '{path}', {line}"
                            )
                        else:
                            break

                    else:
                        kill_process(f"Невозможно включить модуль. Модуль '{path}' не найден.")

                case _:
                    preprocessed.append(line)

                    self.imports.add(path)

        return [line for line in preprocessed if line]
