from src.core.executors.execute_block import ExecuteBlockExecutor
from src.core.types.execute_block import ExecuteBlock
from src.util.build_tools.compile import Compiled


class Interpreter:
    def __init__(self, compiled: Compiled):
        self.compiled = compiled

    def run(self):
        for name, obj in self.compiled.compiled_code.items():
            if isinstance(obj, ExecuteBlock):
                executor = ExecuteBlockExecutor(obj, self.compiled)
                executor.execute()
