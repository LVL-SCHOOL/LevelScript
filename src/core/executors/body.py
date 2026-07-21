from copy import copy
from typing import TYPE_CHECKING, Union, Generator, Final, Type, Callable

from src.core.exceptions import (
    ErrorType,
    NameNotDefine,
    InvalidExpression,
    BaseError,
    create_law_script_exception_class_instance,
    InvalidExceptionType,
    is_def_err,
)
from src.core.executors.expression import ExpressionExecutor
from src.core.tokens import Tokens
from src.core.types.atomic import Number, YIELD
from src.core.types.base_declarative_type import BaseDeclarativeType
from src.core.types.basetype import BaseAtomicType, BaseType
from src.core.types.classes import ClassDefinition, ClassField, ClassExceptionDefinition, ClassInstance
from src.core.types.procedure import (
    Print,
    Return,
    AssignField,
    Body,
    When,
    Loop,
    Expression,
    Procedure,
    Continue,
    Break,
    AssignOverrideVariable,
    While,
    Context,
    BlockSync,
    ErrorThrow,
    Defer
)
from src.core.executors.base import Executor
from src.core.types.variable import Variable, ScopeStack, VariableContextCreator, traverse_scope
from src.util.console_worker import printer
from src.core.extend.function_wrap import PyExtendWrapper

if TYPE_CHECKING:
    from src.util.build_tools.compile import Compiled


class Stop: ...


class Skip: ...


STOP: Final[Stop] = Stop()
SKIP: Final[Skip] = Skip()


def handle_expression(dispatch_executor, command: Expression):
    executor = ExpressionExecutor(command, dispatch_executor.tree_variables, dispatch_executor.compiled)

    if dispatch_executor.async_mode:
        yield from executor.execute(dispatch_executor.async_mode)
    else:
        return executor.execute_with_atomic_type()

    return SKIP

def handle_assign_override_variable(dispatch_executor, command: AssignOverrideVariable):
    target_expr_executor = ExpressionExecutor(
        command.target_expr, dispatch_executor.tree_variables, dispatch_executor.compiled
    )
    override_expr_executor = ExpressionExecutor(
        command.override_expr, dispatch_executor.tree_variables, dispatch_executor.compiled
    )

    if dispatch_executor.async_mode:
        override_expr_result = yield from override_expr_executor.execute(dispatch_executor.async_mode)
    else:
        override_expr_result = override_expr_executor.execute_with_atomic_type()

    if len(command.target_expr.operations) == 1:
        target_name = command.target_expr.operations[0].name

        try:
            var = dispatch_executor.tree_variables.get(target_name)
        except NameNotDefine as e:
            raise NameNotDefine(str(e), info=command.meta_info)

        var.set_value(override_expr_result)

        return SKIP

    if dispatch_executor.async_mode:
        target = yield from target_expr_executor.execute(dispatch_executor.async_mode)
    else:
        target = target_expr_executor.execute()

    if not isinstance(target, (ClassField, Variable)):
        raise InvalidExpression(
            f"Для выражения '{target_expr_executor.expression.raw_expr}' "
            f"не поддерживается оператор '{Tokens.equal}'",
            info=command.meta_info
        )

    if isinstance(target, ClassField):
        target.value = override_expr_result
        return SKIP

    try:
        var = dispatch_executor.tree_variables.get(target.name)
    except NameNotDefine as e:
        raise NameNotDefine(str(e), info=command.meta_info)

    var.set_value(override_expr_result)

    return SKIP

def handle_assign_field(dispatch_executor, command: AssignField):
    if command.name in dispatch_executor.tree_variables.scopes[-1].variables:
        raise ErrorType(f"Переменная '{command.name}' уже определена!", info=command.meta_info)

    executor = ExpressionExecutor(command.expression, dispatch_executor.tree_variables, dispatch_executor.compiled)

    if dispatch_executor.async_mode:
        executed = yield from executor.async_execute(as_atomic=True)
    else:
        executed = executor.execute_with_atomic_type()

    var = Variable(command.name, executed)

    dispatch_executor.tree_variables.set(var)

    return SKIP

def handle_print(dispatch_executor, command: Print):
    executor = ExpressionExecutor(command.expression, dispatch_executor.tree_variables, dispatch_executor.compiled)
    if dispatch_executor.async_mode:
        executed = yield from executor.async_execute(as_atomic=True)
    else:
        executed = executor.execute_with_atomic_type()

    printer.raw_print(executed)

    return SKIP


def handle_when(dispatch_executor, command: When):
    executor = ExpressionExecutor(command.expression, dispatch_executor.tree_variables, dispatch_executor.compiled)
    if dispatch_executor.async_mode:
        result = yield from executor.async_execute(as_atomic=True)
    else:
        result = executor.execute_with_atomic_type()

    with VariableContextCreator(dispatch_executor.tree_variables):
        if result.value:
            body_executor = BodyExecutor(command.body, dispatch_executor.tree_variables, dispatch_executor.compiled)
            if dispatch_executor.async_mode:
                executed = yield from body_executor.async_execute()
            else:
                executed = body_executor.execute()

            if not isinstance(executed, Stop):
                return executed
        else:
            for else_when in command.else_whens:
                when_executor = ExpressionExecutor(
                    else_when.expression, dispatch_executor.tree_variables, dispatch_executor.compiled
                )

                if dispatch_executor.async_mode:
                    result = yield from when_executor.async_execute(as_atomic=True)
                else:
                    result = when_executor.execute_with_atomic_type()

                if result.value:
                    body_executor = BodyExecutor(
                        else_when.body, dispatch_executor.tree_variables, dispatch_executor.compiled
                    )

                    if dispatch_executor.async_mode:
                        executed = yield from body_executor.async_execute()
                    else:
                        executed = body_executor.execute()

                    if not isinstance(executed, Stop):
                        return executed

                    break

            else:
                if command.else_ is not None:
                    body_executor = BodyExecutor(command.else_.body, dispatch_executor.tree_variables, dispatch_executor.compiled)
                    if dispatch_executor.async_mode:
                        executed = yield from body_executor.async_execute()
                    else:
                        executed = body_executor.execute()

                    if not isinstance(executed, Stop):
                        return executed

    return SKIP

def handle_while(dispatch_executor, command: While):
    body_executor = BodyExecutor(command.body, dispatch_executor.tree_variables, dispatch_executor.compiled)
    executor = ExpressionExecutor(command.expression, dispatch_executor.tree_variables, dispatch_executor.compiled)

    with VariableContextCreator(dispatch_executor.tree_variables):
        while True:
            if dispatch_executor.async_mode:
                result = yield from executor.async_execute(as_atomic=True)
            else:
                result = executor.execute_with_atomic_type()

            if dispatch_executor.async_mode:
                yield YIELD

            if not result.value:
                break

            if dispatch_executor.async_mode:
                executed = yield from body_executor.async_execute()
            else:
                executed = body_executor.execute()

            if isinstance(executed, Continue):
                continue

            elif isinstance(executed, Break):
                break

            elif not isinstance(executed, Stop):
                return executed

    return SKIP

def handle_loop(dispatch_executor, command: Loop):
    with VariableContextCreator(dispatch_executor.tree_variables):
        executor_from = ExpressionExecutor(
            command.expression_from, dispatch_executor.tree_variables, dispatch_executor.compiled
        )
        executor_to = ExpressionExecutor(
            command.expression_to, dispatch_executor.tree_variables, dispatch_executor.compiled
        )

        if dispatch_executor.async_mode:
            result_from = yield from executor_from.async_execute(as_atomic=True)
        else:
            result_from = executor_from.execute_with_atomic_type()

        if dispatch_executor.async_mode:
            result_to = yield from executor_to.async_execute(as_atomic=True)
        else:
            result_to = executor_to.execute_with_atomic_type()

        if not isinstance(result_from, Number):
            raise ErrorType(
                f"В цикле в блоке '{Tokens.from_}' должно быть число!",
                info=command.meta_info
            )

        if not isinstance(result_to, Number):
            raise ErrorType(
                f"В цикле в блоке '{Tokens.to}' должно быть число!",
                info=command.meta_info
            )

        with VariableContextCreator(dispatch_executor.tree_variables):
            body_executor = BodyExecutor(command.body, dispatch_executor.tree_variables, dispatch_executor.compiled)

            if not body_executor.body.commands:
                return SKIP

            for var in range(result_from.value, result_to.value + 1):
                if dispatch_executor.async_mode:
                    yield YIELD

                if command.name_loop_var is not None:
                    dispatch_executor.tree_variables.set(Variable(command.name_loop_var, Number(var)))

                if dispatch_executor.async_mode:
                    executed = yield from body_executor.async_execute()
                else:
                    executed = body_executor.execute()

                if isinstance(executed, Continue):
                    continue

                elif isinstance(executed, Break):
                    break

                elif not isinstance(executed, Stop):
                    return executed

    return SKIP

def handle_continue(dispatch_executor, command: Continue):
    if dispatch_executor.async_mode:
        yield YIELD

    return command


def handle_break(dispatch_executor, command: Break):
    if dispatch_executor.async_mode:
        yield YIELD

    return command


def handle_error_throw(dispatch_executor, command: ErrorThrow):
    executor = ExpressionExecutor(command.expression, dispatch_executor.tree_variables, dispatch_executor.compiled)
    if dispatch_executor.async_mode:
        executed = yield from executor.async_execute(as_atomic=True)
    else:
        executed = executor.execute_with_atomic_type()

    if isinstance(executed, ClassExceptionDefinition):
        raise executed.base_ex(info=executor.expression.meta_info)
    elif isinstance(executed, ClassInstance):
        if not is_def_err(executed.metadata.parent):
            raise InvalidExceptionType(type_ex=executed)

        info = executed.fields.get(executed.metadata.info_attr_name)

        raise executed.metadata.base_ex(
            info,
            info=executor.expression.meta_info,
        )
    else:
        raise InvalidExceptionType(type_ex=executed, info=executor.expression.meta_info)


def handle_context(dispatch_executor, command: Context):
    with VariableContextCreator(dispatch_executor.tree_variables):
        body_executor = BodyExecutor(command.body, dispatch_executor.tree_variables, dispatch_executor.compiled)
        try:
            if dispatch_executor.async_mode:
                executed = yield from body_executor.async_execute()
            else:
                executed = body_executor.execute()

            if not isinstance(executed, Stop):
                return executed
        except BaseError as e:
            for handler in command.handlers:
                exception = dispatch_executor.compiled.compiled_code.get(handler.exception_class_name)

                if exception is None:
                    continue

                if not isinstance(exception, ClassExceptionDefinition):
                    continue

                if not isinstance(e, exception.base_ex):
                    continue

                if handler.exception_class_name == e.exc_name:
                    ex_inst = create_law_script_exception_class_instance(handler.exception_class_name, e)
                else:
                    ex_inst = exception.create_instance(e)

                dispatch_executor.tree_variables.set(Variable(handler.exception_inst_name, ex_inst))

                body_executor = BodyExecutor(handler.body, dispatch_executor.tree_variables, dispatch_executor.compiled)
                if dispatch_executor.async_mode:
                    executed = yield from body_executor.async_execute()

                    if not isinstance(executed, Stop):
                        return executed
                else:
                    executed = body_executor.execute()

                    if not isinstance(executed, Stop):
                        return executed

                break
            else:
                raise


def handle_return(dispatch_executor, command: Return):
    executor = ExpressionExecutor(command.expression, dispatch_executor.tree_variables, dispatch_executor.compiled)

    if dispatch_executor.async_mode:
        executed = yield from executor.async_execute(as_atomic=True)
    else:
        executed = executor.execute_with_atomic_type()

    return executed


def handle_block_sync(dispatch_executor, command: BlockSync):
    body_executor = BodyExecutor(command.body, dispatch_executor.tree_variables, dispatch_executor.compiled)

    while command.is_blocked:
        if dispatch_executor.async_mode:
            yield YIELD

    with command.lock:
        command.is_blocked = True

    try:
        if dispatch_executor.async_mode:
            executed = yield from body_executor.async_execute()
        else:
            executed = body_executor.execute()
    finally:
        with command.lock:
            command.is_blocked = False

    if not isinstance(executed, Stop):
        return executed


def handle_defer(dispatch_executor, command: Defer):
    dispatch_executor.defers.append(command)


def handle_default(dispatch_executor, command: BaseType):
    raise ErrorType(f"Неизвестная команда '{command.name}'!", info=command.meta_info)


COMMAND_HANDLERS: Final[dict[Type[BaseType]: Callable[['BodyExecutor', BaseType], BaseAtomicType]]] = {
    Expression: handle_expression,
    AssignOverrideVariable: handle_assign_override_variable,
    AssignField: handle_assign_field,
    Print: handle_print,
    When: handle_when,
    While: handle_while,
    Loop: handle_loop,
    Continue: handle_continue,
    Break: handle_break,
    ErrorThrow: handle_error_throw,
    Context: handle_context,
    Return: handle_return,
    BlockSync: handle_block_sync,
    Defer: handle_defer,
}


class BodyExecutor(Executor):
    def __init__(self, body: Body, tree_variables: ScopeStack, compiled: "Compiled"):
        self.body = body
        self.tree_variables = tree_variables
        self.compiled = compiled
        self.catch_comprehensive_procedures()
        self.async_mode = False
        self.defers: list[Defer] = []

    def catch_comprehensive_procedures(self):
        local_vars_names = {lv.name for lv in traverse_scope(self.tree_variables.scopes[-1])}

        for name, var in self.compiled.compiled_code.items():
            if name in local_vars_names:
                continue

            if isinstance(var, Procedure):
                self.tree_variables.set(Variable(var.name, var))
            elif isinstance(var, PyExtendWrapper):
                self.tree_variables.set(Variable(var.name, var))
            elif isinstance(var, ClassDefinition):
                self.tree_variables.set(Variable(var.name, var))
            elif isinstance(var, BaseDeclarativeType):
                self.tree_variables.set(Variable(var.name, var))

    def execute(self) -> Union[Generator, Union[BaseAtomicType, Continue, Break]]:
        try:
            gen = self._execute()

            try:
                while True:
                    next(gen)
            except StopIteration as exc:
                return exc.value
        finally:
            for defer in reversed(self.defers):
                executor = ExpressionExecutor(defer.expression, self.tree_variables, self.compiled)
                executor.execute_with_atomic_type()

    def async_execute(self):
        self.async_mode = True

        try:
            return self._execute()
        finally:
            for defer in reversed(self.defers):
                executor = ExpressionExecutor(defer.expression, self.tree_variables, self.compiled)
                executor.execute_with_atomic_type()

    def _execute(self) -> Union[Generator, Union[BaseAtomicType, Continue, Break]]:
        for command in self.body.commands:
            handler = COMMAND_HANDLERS.get(command.self_type, handle_default)
            result = yield from handler(self, command)

            if result is SKIP:
                continue

            if result is STOP:
                return result

            if self.async_mode:
                yield YIELD

            if isinstance(result, BaseAtomicType):
                return result

        return STOP
