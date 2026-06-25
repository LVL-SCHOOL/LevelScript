from typing import Final, Callable

from src.core.exceptions import InvalidExpression
from src.core.parse.base import is_identifier, is_float, is_integer
from src.core.tokens import Tokens, ServiceTokens, ALL_TOKENS, BOOL_OP_TOKENS, MATH_OP_TOKENS

_ERROR_MESSAGE: Final[str] = "Оператор '{next_tok}' не может встречаться после '{token}'\n\n"


def _error_with_arrow(err: str, expr: list[str], offset: int):
    prefix_len = sum(len(op) for op in expr[:offset]) + offset + len(expr[offset]) + 1
    return f"{err}\n{' '.join(expr)}\n{' ' * prefix_len}^\n\n"


def get_next_tok(expr: list[str], offset: int):
    next_offset = offset + 1

    if len(expr) <= next_offset:
        return None

    return expr[next_offset]


def check_right_bracket(expr: list[str], token: Tokens, offset: int):
    valid_tokens = {
        Tokens.right_bracket,
        Tokens.comma,
        Tokens.end_expr,
        *MATH_OP_TOKENS,
        *BOOL_OP_TOKENS,
    }

    next_tok = get_next_tok(expr, offset)

    if next_tok is None:
        return

    if next_tok in valid_tokens:
        return

    raise InvalidExpression(_error_with_arrow(_ERROR_MESSAGE.format(next_tok=next_tok, token=token), expr, offset))


def check_wait(expr: list[str], token: Tokens, offset: int):
    valid_tokens = {
        Tokens.in_,
        Tokens.left_bracket,
        ServiceTokens.in_background,
    }

    next_tok = get_next_tok(expr, offset)

    if next_tok is None:
        return

    if is_identifier(next_tok):
        return

    if next_tok in valid_tokens:
        return

    raise InvalidExpression(_error_with_arrow(_ERROR_MESSAGE.format(next_tok=next_tok, token=token), expr, offset))


def check_math_ops(expr: list[str], token: Tokens, offset: int):
    valid_tokens = {
        Tokens.left_bracket,
        Tokens.quotation,
    }

    next_tok = get_next_tok(expr, offset)

    if next_tok is None:
        return

    if is_identifier(next_tok) or is_float(next_tok) or is_integer(next_tok):
        if next_tok not in BOOL_OP_TOKENS:
            return

    if next_tok in valid_tokens:
        return

    raise InvalidExpression(_error_with_arrow(_ERROR_MESSAGE.format(next_tok=next_tok, token=token), expr, offset))


def check_bool_ops(expr: list[str], token: Tokens, offset: int):
    valid_tokens = {
        Tokens.left_bracket,
        Tokens.quotation,
        Tokens.true,
        Tokens.false,
        Tokens.plus,
        Tokens.minus,
        *BOOL_OP_TOKENS,
    }

    next_tok = get_next_tok(expr, offset)

    if next_tok is None:
        return

    if is_identifier(next_tok) or is_float(next_tok) or is_integer(next_tok):
        return

    if next_tok in valid_tokens:
        return

    raise InvalidExpression(_error_with_arrow(_ERROR_MESSAGE.format(next_tok=next_tok, token=token), expr, offset))


def check_quotation(expr: list[str], token: Tokens, offset: int):
    valid_tokens = {
        Tokens.right_bracket,
        Tokens.comma,
        Tokens.attr_access,
        *MATH_OP_TOKENS,
        *BOOL_OP_TOKENS,
    }

    next_tok = get_next_tok(expr, offset)

    if next_tok is None:
        return

    if next_tok in valid_tokens:
        return

    raise InvalidExpression(_error_with_arrow(_ERROR_MESSAGE.format(next_tok=next_tok, token=token), expr, offset))


def check_true_false(expr: list[str], token: Tokens, offset: int):
    valid_tokens = {
        Tokens.right_bracket,
        Tokens.comma,
        Tokens.attr_access,
        *MATH_OP_TOKENS,
        *BOOL_OP_TOKENS,
    }

    next_tok = get_next_tok(expr, offset)

    if next_tok is None:
        return

    if next_tok in valid_tokens:
        return

    raise InvalidExpression(_error_with_arrow(_ERROR_MESSAGE.format(next_tok=next_tok, token=token), expr, offset))


def check_default(expr: list[str], token: Tokens, offset: int):
    valid_tokens = {
        *ALL_TOKENS,
    }

    next_tok = get_next_tok(expr, offset)

    if next_tok is None:
        return

    if next_tok in valid_tokens:
        return

    next_tok_condition = (
            (is_identifier(next_tok) or is_float(next_tok) or is_integer(next_tok)) and next_tok not in ALL_TOKENS
    )
    current_tok_condition = (
            (is_identifier(token) or is_float(token) or is_integer(token)) and token not in ALL_TOKENS
    )

    if current_tok_condition and next_tok_condition:
        raise InvalidExpression(_error_with_arrow(_ERROR_MESSAGE.format(next_tok=next_tok, token=token), expr, offset))


NEXT_TOKEN_CHECKERS: dict[str, Callable[[list[str], str, int], None]] = {
    Tokens.right_bracket: check_right_bracket,
    Tokens.wait: check_wait,
    Tokens.plus: check_math_ops,
    Tokens.minus: check_math_ops,
    Tokens.star: check_math_ops,
    Tokens.exponentiation: check_math_ops,
    Tokens.div: check_math_ops,
    Tokens.percent: check_math_ops,
    Tokens.not_: check_bool_ops,
    Tokens.and_: check_bool_ops,
    Tokens.or_: check_bool_ops,
    Tokens.bool_equal: check_bool_ops,
    Tokens.bool_not_equal: check_bool_ops,
    Tokens.less: check_bool_ops,
    Tokens.greater: check_bool_ops,
    Tokens.quotation: check_quotation,
    Tokens.true: check_true_false,
    Tokens.false: check_true_false,
}
