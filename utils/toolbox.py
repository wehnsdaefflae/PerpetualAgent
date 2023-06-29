# coding=utf-8
import os
import types
from typing import Union
import logging
import ast
import importlib.util
import inspect

import hyperdb
from docstring_parser import parse, Docstring

from utils.basic_llm_calls import get_embeddings
from utils.logging_handler import logging_handlers


class ToolBox:
    def __init__(self, tool_folder: str, database_path: str = "tool_database.pickle.gz", tool_memory: int = 100):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        for each_handler in logging_handlers():
            self.logger.addHandler(each_handler)

        self.tool_folder = tool_folder
        self.tool_memory = tool_memory
        self.database_path = database_path
        self.vector_db = self._initialize_database(database_path)

    def _initialize_database(self, database_path: str) -> hyperdb.HyperDB():
        db = hyperdb.HyperDB()
        tool_names = sorted(self.get_all_tools())

        if os.path.isfile(database_path):
            db.load(database_path)

            tool_names_from_db = sorted(db.documents)

            if tool_names_from_db == tool_names:
                self.logger.info(f"Loading Database already initialized with {len(tool_names)} tools")
                return db

            db = hyperdb.HyperDB()

        self.logger.info(f"Initializing database with {len(tool_names)} tools")
        descriptions = [self.get_docstring_description_from_name(each_name) for each_name in tool_names]
        embeddings = get_embeddings(descriptions)
        db.add_documents(tool_names, vectors=embeddings)
        db.save(database_path)
        return db

    def get_all_tools(self) -> dict[str, types.FunctionType]:
        functions = dict()
        for file_name in os.listdir(self.tool_folder):
            if not file_name.endswith(".py") or file_name.startswith("_"):
                continue
            each_name = file_name[:-3]
            specification = importlib.util.spec_from_file_location(each_name, location=os.path.join(self.tool_folder, file_name))
            module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(module)
            functions[each_name] = getattr(module, each_name)

        self.logger.info(f"Loaded {len(functions)} tools from {self.tool_folder}")
        return functions

    def _save_tool_code(self, code: str, is_temp: bool) -> None:
        tool_name = self.get_name_from_code(code)
        name = "_tmp.py" if is_temp else f"{tool_name}.py"
        self.logger.info(f"Saving tool {tool_name} to {name}")
        with open(os.path.join(self.tool_folder, name), mode="w" if is_temp else "x") as file:
            file.write(code)

    def save_tool_code(self, code: str, is_temp: bool) -> None:
        self._save_tool_code(code, is_temp=is_temp)
        if not is_temp:
            description = self.get_docstring_description_from_code(code)
            embedding, = get_embeddings([description])
            tool_name = self.get_name_from_code(code)
            self.vector_db.add_document(tool_name, embedding)
            self.vector_db.save(self.database_path)

    @staticmethod
    def _type_to_schema(t: any) -> dict[str, any]:
        if t == int:
            return {"type": "integer"}
        if t == float:
            return {"type": "number"}
        if t == str:
            return {"type": "string"}
        if t == bool:
            return {"type": "boolean"}
        if t == types.NoneType:
            return {"type": "null"}

        if isinstance(t, types.UnionType):
            return {"anyOf": [ToolBox._type_to_schema(i) for i in t.__args__]}

        if hasattr(t, "__origin__"):
            if t.__origin__ == Union:
                return {"anyOf": [ToolBox._type_to_schema(i) for i in t.__args__]}
            if t.__origin__ == list:
                return {"type": "array", "items": ToolBox._type_to_schema(t.__args__[0])}
            if t.__origin__ == tuple:
                if len(t.__args__) == 2 and t.__args__[1] is ...:
                    return {"type": "array", "items": ToolBox._type_to_schema(t.__args__[0])}

                return {"type": "array", "items": [ToolBox._type_to_schema(i) for i in t.__args__]}

            if t.__origin__ == dict:
                if t.__args__[0] != str:
                    raise ValueError("Dictionary keys must be strings")

                return {"type": "object"}

        raise ValueError(f"Unsupported type: {t}")

    def get_schema_from_code(self, code: str) -> dict[str, str]:
        docstring = self.get_docstring_from_code(code)
        parsed_doc = parse(docstring)
        args_section = parsed_doc.params

        tool = self.get_temp_tool_from_code(code)
        arguments = (each_argument for each_argument in tool.__annotations__.items() if each_argument[0] != 'return')
        properties = dict()

        for (arg_name, arg_type), each_arg in zip(arguments, args_section, strict=True):
            arg_description = each_arg.description

            if arg_description is None:
                raise ValueError(f"Argument {arg_name} is missing a description")

            properties[arg_name] = {"description": arg_description, **ToolBox._type_to_schema(arg_type)}

        schema = {
            "name": self.get_name_from_code(code),
            "description": self.get_docstring_description_from_code(code),
            "parameters": {
                "type": "object",
                # "properties": {k: type_to_schema(v) for k, v in fun.__annotations__.items() if k != 'return'},
                "properties": properties,
                "required": self.get_required_from_code(code)
            }
        }

        return schema

    def get_docstring_from_tool(self, tool: types.FunctionType) -> Docstring:
        tool_doc = inspect.getdoc(tool)
        parsed_doc = parse(tool_doc)
        return parsed_doc

    def get_docstring_from_code(self, code: str) -> str:
        module = ast.parse(code)
        for node in module.body:
            if isinstance(node, ast.FunctionDef):
                # noinspection PyTypeChecker
                return ast.get_docstring(node)  # type documentation seems to be wrong here
        raise ValueError("No docstring found in code.")

    def get_docstring_description_from_name(self, name: str) -> str:
        code = self.get_code_from_name(name)
        return self.get_docstring_description_from_code(code)

    def get_docstring_description_from_code(self, code: str) -> str:
        tool_doc = self.get_docstring_from_code(code)
        parsed_doc = parse(tool_doc)
        tool_short_description = parsed_doc.short_description
        tool_long_description = parsed_doc.long_description
        if tool_long_description is None:
            return tool_short_description
        return tool_short_description + " " + tool_long_description

    def get_required_from_code(self, code: str) -> list[str]:
        module = ast.parse(code)
        for node in module.body:
            if isinstance(node, ast.FunctionDef):
                arguments = node.args
                return [arg.arg for arg in arguments.args]
        return list()

    def get_schema_from_name(self, name: str) -> dict[str, str]:
        with open(os.path.join(self.tool_folder, f"{name}.py"), mode="r") as file:
            return self.get_schema_from_code(file.read())

    def get_schema_from_tool(self, tool: types.FunctionType) -> dict[str, any]:
        # name = tool.__name__
        # return self.get_schema_from_name(name)

        code = self.get_code_from_tool(tool)
        return self.get_schema_from_code(code)

    def get_description_from_name(self, name: str) -> str:
        code = self.get_code_from_name(name)
        return self.get_description_from_code(code)

    def get_signature_from_code(self, code: str) -> str:
        name = self.get_name_from_code(code)
        lines = code.split("\n")
        line_start = f"def {name}"
        for each_line in lines:
            if each_line.startswith(line_start):
                return each_line.removeprefix(line_start).strip().removesuffix(":")

        raise ValueError(f"Could not find signature for tool {name}.")

    def get_description_from_code(self, code: str) -> str:
        name = self.get_name_from_code(code)
        signature = self.get_signature_from_code(code)
        docstring_description = self.get_docstring_description_from_code(code)
        example_arguments = self.get_example_arguments_from_code(code)
        example_arguments_str = ", ".join(
            [
                f"{each_key}=\"{each_value}\"" if isinstance(each_value, str) else
                f"{each_key}={each_value}"
                for each_key, each_value in example_arguments.items()
            ]
        )

        example_str = "" if len(example_arguments_str) < 1 else f" Example arguments: {example_arguments_str}"
        return f"{name}{signature}: {docstring_description}{example_str}"

    def get_example_arguments_from_code(self, tool_source: str) -> dict[str, any]:
        module = ast.parse(tool_source)
        for node in module.body:
            if isinstance(node, ast.FunctionDef):
                func_def = node
                break
        else:
            raise ValueError(f"The first node is not a function definition.")

        docstring = self.get_docstring_from_code(tool_source)
        for each_line in docstring.split("\n"):
            each_line_stripped = each_line.strip()
            if each_line_stripped.startswith(">>> "):
                call_str = each_line_stripped.removeprefix(">>> ")
                break
        else:
            raise ValueError(f"No example call found in docstring for tool '{func_def.name}'.")

        parsed_call = ast.parse(call_str)

        for each_node in ast.walk(parsed_call):
            if isinstance(each_node, ast.Call) and isinstance(each_node.func, ast.Name) and each_node.func.id == func_def.name:
                function_call_node = each_node
                break
        else:
            raise ValueError(f"The example call in the docstring for tool '{func_def.name}' is not a function call.")

        # Extract function definition arguments
        function_def_args = func_def.args

        # Extract function call arguments
        function_call_args = function_call_node.args
        function_call_keywords = function_call_node.keywords

        # Map the call arguments to their respective names
        arg_names_values = dict()

        # Positional arguments
        for i, arg in enumerate(function_call_args):
            arg_names_values[function_def_args.args[i].arg] = ast.literal_eval(arg)

        # Keyword arguments
        for kwarg in function_call_keywords:
            arg_names_values[kwarg.arg] = ast.literal_eval(kwarg.value)

        # Default values for missing keyword arguments
        for i, default_arg in enumerate(function_def_args.defaults):
            default_arg_name = function_def_args.args[len(function_call_args) + i].arg
            if default_arg_name not in arg_names_values:
                arg_names_values[default_arg_name] = ast.literal_eval(default_arg)

        return arg_names_values

    def get_name_from_code(self, code: str) -> str:
        for each_node in ast.walk(ast.parse(code)):
            if isinstance(each_node, ast.FunctionDef):
                return each_node.name

    def get_code_from_tool(self, tool: types.FunctionType) -> str:
        file = inspect.getfile(tool)
        with open(file, mode="r") as file:
            return file.read()

    def get_tool_from_name(self, name: str) -> types.FunctionType:
        all_tools = self.get_all_tools()
        return all_tools[name]

    def get_code_from_name(self, name: str) -> str:
        with open(os.path.join(self.tool_folder, f"{name}.py"), mode="r") as file:
            return file.read()

    def get_temp_tool_from_code(self, code: str) -> types.FunctionType:
        self.save_tool_code(code, True)
        name = self.get_name_from_code(code)
        specification = importlib.util.spec_from_file_location(name, location=os.path.join(self.tool_folder, "_tmp.py"))
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        return getattr(module, name)
