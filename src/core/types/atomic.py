from typing import Union, Final, Any, MutableMapping, Optional, Generic, TypeVar

from src.core.exceptions import ErrorType, OperationError
from src.core.tokens import Tokens
from src.core.types.basetype import BaseAtomicType


def convert_atomic_type_to_py_type(atomic_obj: BaseAtomicType, *, strict: bool = False) -> Any:
    from src.core.types.classes import ClassField

    if isinstance(atomic_obj, Number):
        value = atomic_obj.value
        return int(value) if isinstance(value, int) or value.is_integer() else float(value)

    elif isinstance(atomic_obj, String):
        return atomic_obj.value

    elif isinstance(atomic_obj, ClassField):
        return convert_atomic_type_to_py_type(atomic_obj.value)

    elif isinstance(atomic_obj, Boolean):
        return atomic_obj.value

    elif isinstance(atomic_obj, Void):
        return atomic_obj.value

    elif isinstance(atomic_obj, Array):
        return [convert_atomic_type_to_py_type(item) for item in atomic_obj.value]

    elif isinstance(atomic_obj, Table):
        result = {}

        for key, value in atomic_obj.value.items():
            if isinstance(key, String):
                py_key = key.value
            else:
                py_key = str(key)
            result[py_key] = convert_atomic_type_to_py_type(value)

        return result

    if strict:
        raise ErrorType(f"Невозможно преобразовать тип '{type(atomic_obj)}' к Python объекту!")

    return atomic_obj


def convert_py_type_to_atomic_type(py_obj: Any) -> BaseAtomicType:
    if isinstance(py_obj, bool):
        return Boolean(py_obj)

    elif isinstance(py_obj, (int, float)):
        return Number(py_obj)

    elif isinstance(py_obj, str):
        return String(py_obj)

    elif py_obj is None:
        return VOID

    elif isinstance(py_obj, (tuple, list)):
        array = []

        for offset, item in enumerate(py_obj):
            array.append(convert_py_type_to_atomic_type(item))

        return Array(array)

    elif isinstance(py_obj, (dict, MutableMapping)):
        table = {}

        for key, value in py_obj.items():
            table[String(str(key))] = convert_py_type_to_atomic_type(value)

        return Table(table)

    raise ErrorType(f"Тип '{type(py_obj)}' невозможно преобразовать")


class CustomAtomicType(BaseAtomicType):
    def __init__(self, value: Any = ...):
        super().__init__(value)
        self.class_instance_type_name = self.type_name()

    def add(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.plus, self.class_instance_type_name)

    def sub(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.minus, self.class_instance_type_name)

    def neg(self):
        raise OperationError(Tokens.minus, self.class_instance_type_name)

    def pos(self):
        raise OperationError(Tokens.plus, self.class_instance_type_name)

    def mul(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.star, self.class_instance_type_name)

    def div(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.div, self.class_instance_type_name)

    def mod(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.percent, self.class_instance_type_name)

    def pow(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.exponentiation, self.class_instance_type_name)

    def eq(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.bool_equal, self.class_instance_type_name)

    def ne(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.bool_not_equal, self.class_instance_type_name)

    def lt(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.less, self.class_instance_type_name)

    def le(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.less, self.class_instance_type_name)

    def gt(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.greater, self.class_instance_type_name)

    def ge(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.greater, self.class_instance_type_name)

    def and_(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.and_, self.class_instance_type_name)

    def or_(self, other: "BaseAtomicType"):
        raise OperationError(Tokens.or_, self.class_instance_type_name)

    def not_(self):
        raise OperationError(Tokens.not_, self.class_instance_type_name)

    def __str__(self) -> str:
        return Tokens.spec_type

class String(BaseAtomicType):
    def __init__(self, value: str):
        super().__init__(value)

    @classmethod
    def type_name(cls):
        return "Строка"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other):
        if isinstance(other, String):
            return self.value == other.value

        return False


class Number(BaseAtomicType):
    def __init__(self, value: Union[float, int]):
        super().__init__(value)

    def is_int(self) -> bool:
        return isinstance(self.value, int)

    @classmethod
    def type_name(cls):
        return "Число"

    def __str__(self) -> str:
        if isinstance(self.value, float):
            if self.value == float("inf"):
                return "Бесконечность"
            elif self.value == float("-inf"):
                return "Отрицательная бесконечность"

        return str(self.value)


class Boolean(BaseAtomicType):
    def __init__(self, value: bool):
        if not isinstance(value, bool):
            value = bool(value)

        super().__init__(value)

    @classmethod
    def type_name(cls):
        return "Логический"

    def __str__(self):
        if self.value:
            return Tokens.true
        else:
            return Tokens.false


_AV = TypeVar('_AV', bound=BaseAtomicType)


class Array(BaseAtomicType, Generic[_AV]):
    def __init__(self, value: Optional[list[_AV]] = None):
        if value is None:
            value = []

        super().__init__(value)
        self.visited = set()

    def append(self, obj: BaseAtomicType):
        self.value.append(obj)

    def remove(self, idx: Number):
        del self.value[idx.value]

    def index(self, idx: Number):
        return self.value[idx.value]

    def pop(self, idx: Number):
        return self.value.pop(idx.value)

    def len(self) -> Number:
        return Number(len(self.value))

    def __contains__(self, idx: Number):
        return idx in self.value

    def __len__(self):
        return len(self.value)

    def __str__(self):
        if id(self) in self.visited:
            return "ЦИКЛИЧЕСКАЯ ССЫЛКА"

        self.visited.add(id(self))

        result = ""

        for value in self.value:
            result += ", "

            if isinstance(value, String):
                result += f"\"{value}\""
            elif value is self:
                result += "ЦИКЛИЧЕСКАЯ ССЫЛКА"
            else:
                result += str(value)

        self.visited.remove(id(self))

        return "[" + result[2:] + "]"

    @classmethod
    def type_name(cls):
        return "Массив"

    def __setitem__(self, key, value):
        self.value[key] = value

    def __getitem__(self, item):
        return self.value[item]


_TV = TypeVar('_TV', bound=BaseAtomicType)


class Table(BaseAtomicType, Generic[_TV]):
    def __init__(self, value: Optional[dict[String, _TV]] = None):
        if value is None:
            value = {}

        super().__init__(value)
        self.visited = set()

    def get(self, key: String, default=None):
        default = VOID if default is None else default
        return self.value.get(key, default)

    def set(self, key: String, value: BaseAtomicType):
        self.value[key] = value

    def del_(self, key: String):
        del self.value[key]

    def len(self) -> Number:
        return Number(len(self.value))

    @classmethod
    def type_name(cls):
        return "Таблица"

    def __contains__(self, key):
        return key in self.value

    def __getitem__(self, item: String):
        return self.value[item]

    def __setitem__(self, key: String, value: BaseAtomicType):
        self.value[key] = value

    def __len__(self):
        return len(self.value)

    def __str__(self):
        if id(self) in self.visited:
            return "ЦИКЛИЧЕСКАЯ ССЫЛКА"

        self.visited.add(id(self))
        result = ""

        for key, value in self.value.items():
            result += ", "

            if isinstance(value, String):
                result += f"\"{key}\": \"{value}\""
            elif value is self:
                result += f"\"{key}\": {'ЦИКЛИЧЕСКАЯ ССЫЛКА'}"
            else:
                result += f"\"{key}\": {value}"

        self.visited.remove(id(self))

        return "{" + result[2:] + "}"


class Void(CustomAtomicType):
    def __init__(self):
        super().__init__(None)

    def eq(self, other: "BaseAtomicType"):
        return self.value == other.value

    def ne(self, other: "BaseAtomicType"):
        return self.value != other.value

    def lt(self, other: "BaseAtomicType"):
        return self.value < other.value

    def le(self, other: "BaseAtomicType"):
        return self.value <= other.value

    def gt(self, other: "BaseAtomicType"):
        return self.value > other.value

    def ge(self, other: "BaseAtomicType"):
        return self.value >= other.value

    def and_(self, other: "BaseAtomicType"):
        return self.value and other.value

    def or_(self, other: "BaseAtomicType"):
        return self.value or other.value

    def not_(self):
        return not self.value

    @classmethod
    def type_name(cls):
        return "Пустота"

    def __str__(self) -> str:
        return Tokens.void


class Yield(BaseAtomicType):
    def __init__(self):
        super().__init__(None)


YIELD: Final[Yield] = Yield()
VOID: Final[Void] = Void()
