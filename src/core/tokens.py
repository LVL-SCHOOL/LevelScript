from enum import StrEnum
from typing import Final


class Tokens(StrEnum):
    comment = "!"
    star = "*"
    left_bracket = "("
    right_bracket = ")"
    left_square_bracket = "["
    right_square_bracket = "]"
    comma = ","
    dot = "."
    equal = "="
    plus = "+"
    minus = "-"
    exponentiation = "^"
    percent = "%"
    div = "/"
    end_expr = ";"
    attr_access = ":"
    quotation = "\""
    slash = "\\"
    spec_type = "<Спец. тип>"
    triple_dot = "..."

    define = "ОПРЕДЕЛИТЬ"
    print_ = "НАПЕЧАТАТЬ"
    types = "ТИПЫ"
    include = "ВКЛЮЧИТЬ"
    not_ = "НЕ"
    and_ = "И"
    or_ = "ИЛИ"
    bool_equal = "РАВНО"
    bool_equal_1 = "РАВЕН"
    bool_equal_2 = "РАВНЫ"
    bool_equal_3 = "РАВНА"
    bool_not_equal = "НЕРАВНО"
    bool_not_equal_1 = "НЕРАВЕН"
    bool_not_equal_2 = "НЕРАВНЫ"
    bool_not_equal_3 = "НЕРАВНА"
    less = "МЕНЬШЕ"
    greater = "БОЛЬШЕ"
    between = "МЕЖДУ"
    data = "ДАННЫЕ"
    procedure = "ПРОЦЕДУРА"
    a_procedure = "ПРОЦЕДУРУ"
    assign = "ЗАДАТЬ"
    when = "ЕСЛИ"
    then = "ТО"
    else_ = "ИНАЧЕ"
    loop = "ЦИКЛ"
    from_ = "ОТ"
    to = "ДО"
    while_ = "ПОКА"
    return_ = "ВЕРНУТЬ"
    true = "ИСТИНА"
    false = "ЛОЖЬ"
    continue_ = "ПРОПУСТИТЬ"
    break_ = "ПРЕРВАТЬ"
    void = "ПУСТОТА"
    wait = "ЖДАТЬ"
    run = "ЗАПУСТИТЬ"
    in_ = "В"
    background = "ФОНЕ"
    execute = "ВЫПОЛНИТЬ"
    docs = "ДОКУМЕНТАЦИЯ"
    space = "ПРОБЕЛ"
    class_ = "КЛАСС"
    extend = "НАСЛЕДОВАТЬ"
    constructor = "КОНСТРУКТОР"
    method = "МЕТОД"
    context = "КОНТЕКСТ"
    handler = "ОБРАБОТЧИК"
    as_ = "КАК"
    blocking = "БЛОКИРОВАТЬ"
    error = "ОШИБКА"
    defer = "ОТЛОЖИТЬ"
    defer_1 = "ОТЛОЖЕННО"

    behaviour = "ПОВЕДЕНИЕ"
    behaviour_star = "УМНОЖЕНИЕ"
    behaviour_div = "ДЕЛЕНИЕ"
    behaviour_plus = "СЛОЖЕНИЕ"
    behaviour_minus= "ВЫЧИТАНИЕ"
    behaviour_exponentiation = "СТЕПЕНЬ"
    behaviour_and = "И"
    behaviour_or = "ИЛИ"
    behaviour_greater = "БОЛЬШЕ"
    behaviour_less = "МЕНЬШЕ"
    behaviour_equal = "РАВНО"
    behaviour_not_equal = "НЕРАВНО"


class ServiceTokens(StrEnum):
    unary_minus = "{{%unary_minus%}}"
    unary_plus = "{{%unary_plus%}}"
    void_arg = "{{%void_arg%}}"
    arg_separator = "{{%arg_separator%}}"
    in_background = Tokens.in_ + Tokens.background


ALL_TOKENS: Final[set] = set(list(ServiceTokens) + list(Tokens))
NOT_ALLOWED_TOKENS: Final[set] = set(Tokens) - {
    Tokens.comment, Tokens.star, Tokens.left_bracket, Tokens.right_bracket,
    Tokens.left_square_bracket, Tokens.right_square_bracket, Tokens.comma, Tokens.dot,
    Tokens.equal, Tokens.plus, Tokens.minus, Tokens.exponentiation, Tokens.percent,
    Tokens.div, Tokens.end_expr, Tokens.quotation, Tokens.not_,Tokens.and_, Tokens.or_,
    Tokens.bool_equal, Tokens.bool_not_equal, Tokens.less, Tokens.greater, Tokens.true, Tokens.false,
    Tokens.in_, Tokens.background, Tokens.wait, Tokens.attr_access, Tokens.void
}
ALIASES_MAP: Final[dict] = {
    Tokens.bool_equal: [Tokens.bool_equal_1, Tokens.bool_equal_2, Tokens.bool_equal_3],
    Tokens.bool_not_equal: [Tokens.bool_not_equal_1, Tokens.bool_not_equal_2, Tokens.bool_not_equal_3],
    Tokens.defer: [Tokens.defer_1],
}
END_LINE_TOKENS: Final[tuple] = (Tokens.left_bracket, Tokens.right_bracket, Tokens.comma, Tokens.end_expr)
MATH_OP_TOKENS: Final[set] = {
    Tokens.star,
    Tokens.plus,
    Tokens.minus,
    Tokens.exponentiation,
    Tokens.percent,
    Tokens.div,
}
BOOL_OP_TOKENS: Final[set] = {
    Tokens.and_,
    Tokens.or_,
    Tokens.not_,
    Tokens.bool_equal,
    Tokens.bool_not_equal,
    Tokens.less,
    Tokens.greater,
    *ALIASES_MAP.get(Tokens.bool_equal, []),
    *ALIASES_MAP.get(Tokens.bool_not_equal, []),
}
BEHAVIOURS_TOKENS = {
    Tokens.behaviour_div, Tokens.behaviour_star, Tokens.behaviour_and, Tokens.behaviour_or,
    Tokens.behaviour_minus, Tokens.behaviour_plus, Tokens.behaviour_exponentiation,
    Tokens.behaviour_greater, Tokens.behaviour_less, Tokens.behaviour_equal, Tokens.behaviour_not_equal,
}
