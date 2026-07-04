from jinja2 import Environment, FileSystemLoader
from typing import Type
from dataclasses import dataclass
import os

from src.core.types.procedure import Procedure, CodeBlock, Body, When, Else, ElseWhen, Loop, While
from src.util.build_tools.compile import Compiled


@dataclass
class FunctionDoc:
    name: str
    docs: str
    args: list[dict[str, str]]
    blocks: list[dict[str, str]]


@dataclass
class SanctionDoc:
    name: str
    article : str


@dataclass
class LawDoc:
    name: str
    desc: str


@dataclass
class RuleDoc:
    name: str
    desc: str


@dataclass
class DutyDoc:
    name: str
    desc: str


@dataclass
class SubjectDoc:
    name: str
    subject_name: str


@dataclass
class ObjectDoc:
    name: str
    name_object: str


@dataclass
class ConditionDoc:
    name: str
    desc: str
    criteria: list[str]


@dataclass
class DocumentDoc:
    name: str
    hypothesis: str
    disposition: str
    sanction: str


@dataclass
class FactSituationDoc:
    name: str
    object_name: str
    subject_name: str
    data: dict[str, str]


@dataclass
class CheckerSituationDoc:
    name: str
    document_name: str
    fact_situation_name: str


class DocsGenerator:
    def __init__(self):
        self.fact_situations = None
        self.verifications = None
        self.documents = None
        self.functions = None
        self.sanctions = None
        self.laws = None
        self.rules = None
        self.duties = None
        self.subjects = None
        self.objects = None
        self.conditions = None

        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def prepare_code(self, compiled_code: Compiled):
        self.functions = self._parse_functions(compiled_code)

    def _parse_body(self, block: CodeBlock, body: Body, wrap: bool = False) -> list[dict[str, str]]:
        if body.docs is None:
            return []

        translate_block_map: dict[Type[CodeBlock], str] = {
            When: "Если",
            ElseWhen: "Иначе если",
            Else: "Иначе",
            Loop: "Цикл со счетчиком",
            While: "Цикл с условием"
        }
        blocks = [
            {
                "type": translate_block_map[type(block)], "docs": block.body.docs.docs_text, "wrap": wrap
            }
        ]

        for command in body.commands:
            if isinstance(command, CodeBlock):
                blocks.extend(self._parse_body(command, command.body, wrap=True))

        return blocks

    def _parse_functions(self, code: Compiled) -> list[FunctionDoc]:
        functions = []

        for name, obj in code.compiled_code.items():
            if isinstance(obj, Procedure):
                default_arguments = obj.default_arguments if obj.default_arguments is not None else {}
                args = [
                    {"name": arg, "docs": "Обязательный" if arg not in default_arguments else "Необязательный"}
                    for arg in obj.arguments_names
                ]
                blocks = []
                main_docs = ""

                if obj.body.docs is not None:
                    main_docs = obj.body.docs.docs_text

                for block in obj.body.commands:
                    if isinstance(block, CodeBlock):
                        blocks.extend(self._parse_body(block, block.body))

                        if isinstance(block, When):
                            for else_when in block.else_whens:
                                blocks.extend(self._parse_body(else_when, else_when.body))

                            if block.else_ is not None:
                                blocks.extend(self._parse_body(block.else_, block.else_.body))

                func = FunctionDoc(name=name, docs=main_docs, args=args, blocks=blocks)

                functions.append(func)

        return functions

    def generate(self, output_path: str, module: str):
        template = self.env.get_template('base.html')

        context = {
            'title': 'Документация модуля',
            'filename': module,
            'functions': self.functions,
            'sanctions': self.sanctions,
            'laws': self.laws,
            'rules': self.rules,
            'duties': self.duties,
            'subjects': self.subjects,
            'objects': self.objects,
            'conditions': self.conditions,
            'documents': self.documents,
            'fact_situations': self.fact_situations,
            'verifications': self.verifications,
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template.render(context))
