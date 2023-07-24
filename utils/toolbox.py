# coding=utf-8
import json
import os
import types
from typing import Union
import ast
import importlib.util

import hyperdb

from utils.basic_llm_calls import get_embeddings
from utils.misc import LOGGER


class SchemaExtractionException(Exception):
    pass


class ToolBox:
    def __init__(self, tool_folder: str, database_path: str = "tool_database.pickle.gz", tool_memory: int = 100):
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
                LOGGER.info(f"Loading Database already initialized with {len(tool_names)} tools")
                return db

            db = hyperdb.HyperDB()
            LOGGER.warning(f"Database already initialized with {len(tool_names_from_db)} tools, but {len(tool_names)} tools found in folder. "
                                f"Reinitializing database.")

        LOGGER.info(f"Initializing database with {len(tool_names)} tools")
        docstrings = [self.get_docstring_dict(each_name) for each_name in tool_names]
        descriptions = list()
        for each_docstring in docstrings:
            description = self.description_from_docstring_dict(each_docstring)
            descriptions.append(description)
        embeddings = get_embeddings(descriptions)
        db.add_documents(tool_names, vectors=embeddings)
        db.save(database_path)
        return db

    def get_docstring_file_from_name(self, tool_name: str) -> str:
        return os.path.join(self.tool_folder, tool_name + ".json")
    
    def get_docstring_dict(self, tool_name: str) -> dict[str, any]:
        schema_file = self.get_docstring_file_from_name(tool_name)
        with open(schema_file, mode="r") as schema_file:
            return json.load(schema_file)
    
    def get_all_descriptions(self) -> list[str]:
        return [self.get_description_from_name(each_name) for each_name in self.get_all_tools()]

    def get_all_descriptions_string(self) -> str:
        return "\n".join(f"- {each_description}" for each_description in self.get_all_descriptions())

    def get_all_tools(self) -> dict[str, types.FunctionType]:
        functions = dict()
        for file_name in os.listdir(self.tool_folder):
            each_name, extension = os.path.splitext(file_name)
            docstring_file = self.get_docstring_file_from_name(each_name)
            if not extension == ".py" or each_name.startswith("_") or not os.path.isfile(docstring_file):
                continue
            specification = importlib.util.spec_from_file_location(file_name, location=os.path.join(self.tool_folder, file_name))
            module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(module)
            functions[each_name] = getattr(module, each_name)

        LOGGER.info(f"Loaded {len(functions)} tools from {self.tool_folder}")
        return functions

    def _save_tool_code(self, code: str, docstring_dict: dict[str, any], is_temp: bool) -> None:
        tool_name = self.get_name_from_code(code)
        name = "_tmp" if is_temp else tool_name
        LOGGER.info(f"Saving tool {tool_name}...")
        with open(os.path.join(self.tool_folder, name + ".py"), mode="w" if is_temp else "x") as file:
            file.write(code)
        with open(os.path.join(self.tool_folder, name + ".json"), mode="w" if is_temp else "x") as file:
            json.dump(docstring_dict, file, indent=4, sort_keys=True)

    def save_tool_code(self, code: str, docstring_dict: dict[str, any], is_temp: bool) -> None:
        self._save_tool_code(code, docstring_dict, is_temp=is_temp)
        if not is_temp:
            description = self.description_from_docstring_dict(docstring_dict)
            embedding, = get_embeddings([description])
            tool_name = docstring_dict["name"]
            self.vector_db.add_document(tool_name, vector=embedding)
            self.vector_db.save(self.database_path)

    def description_from_docstring_dict(self, docstring_dict: dict[str, any]) -> str:
        return docstring_dict["summary"] + "\n" + docstring_dict["description"]

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
                    raise SchemaExtractionException("Dictionary keys must be strings")

                return {"type": "object"}

        raise SchemaExtractionException(f"Unsupported type: {t}")

    def get_tool_schema(self, code: str, docstring_dict: dict[str, any]) -> dict[str, any]:
        # todo: check:
        #   1. tool_name,
        #   2. argument dict list with name, type, and example,
        #   3. keyword argument dict from name to type, default, and example,
        #   4. return dict with type and example

        args_docstring = docstring_dict["args"]

        tool = self.get_temp_tool_from_code(code, docstring_dict)
        arguments = tuple(each_argument for each_argument in tool.__annotations__.items() if each_argument[0] != 'return')
        properties = dict()

        if len(args_docstring) != len(arguments):
            raise SchemaExtractionException(f"Number of arguments in docstring ({len(args_docstring)}) does not match number of arguments in code ({len(arguments)})")

        for (arg_name, arg_type), each_arg in zip(arguments, args_docstring, strict=True):
            arg_description = each_arg['description']
            if arg_description is None:
                raise SchemaExtractionException(f"Argument {arg_name} is missing a description")

            properties[arg_name] = {"description": arg_description, **ToolBox._type_to_schema(arg_type)}

        if not self.get_name_from_code(code) == docstring_dict["name"]:
            raise SchemaExtractionException(f"Tool name in code ({self.get_name_from_code(code)}) does not match tool name in docstring ({docstring_dict['name']})")

        positional_arguments_code = self.get_required_from_code(code)
        positional_arguments_json = [each_argument["name"] for each_argument in args_docstring if not each_argument["is_keyword_argument"]]

        if not set(positional_arguments_code) == set(positional_arguments_json):
            raise SchemaExtractionException(
                f"Positional arguments in code ({positional_arguments_code}) do not match positional arguments in docstring ({positional_arguments_json})"
            )

        return {
            "name": docstring_dict["name"],
            "description": docstring_dict["description"],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": positional_arguments_code
            }
        }

    def get_required_from_code(self, code: str) -> list[str]:
        module = ast.parse(code)
        for node in module.body:
            if isinstance(node, ast.FunctionDef):
                arguments = node.args
                arg_names = [arg.arg for arg in arguments.args]
                default_values = node.args.defaults
                num_kwargs = len(default_values)
                if num_kwargs < 1:
                    return arg_names
                return arg_names[:-num_kwargs]
        return list()

    def get_schema_from_name(self, name: str) -> dict[str, any]:
        code = self.get_code_from_name(name)
        docstring_dict = self.get_docstring_dict(name)
        schema = self.get_tool_schema(code, docstring_dict)
        return schema

    def get_description_from_name(self, name: str) -> str:
        code = self.get_code_from_name(name)
        signature = self.get_signature_from_code(code)
        docstring_dict = self.get_docstring_dict(name)
        summary = docstring_dict["summary"]
        arguments = docstring_dict["args"]
        example_arguments_str = ", ".join(
            [
                f"{each_arg['name']}=\"{each_arg['example_value']}\"" if each_arg["python_type"] == "str" else
                f"{each_arg['name']}={each_arg['example_value']}"
                for each_arg in arguments
            ]
        )

        example_result = docstring_dict["return_value"]
        example_result_str = "" if example_result["python_type"] == "None" else f", example result: {example_result['example_value']!r}"
        example_str = "" if len(example_arguments_str) < 1 else f" example arguments: {example_arguments_str}"
        return f"{name}{signature}: {summary}{example_str}{example_result_str}"

    def get_signature_from_code(self, code: str) -> str:
        name = self.get_name_from_code(code)
        lines = code.split("\n")
        line_start = f"def {name}"
        for each_line in lines:
            if each_line.startswith(line_start):
                return each_line.removeprefix(line_start).strip().removesuffix(":")

        raise ValueError(f"Could not find signature for tool {name}.")

    def get_name_from_code(self, code: str) -> str:
        for each_node in ast.walk(ast.parse(code)):
            if isinstance(each_node, ast.FunctionDef):
                return each_node.name

    def get_tool_from_name(self, name: str) -> types.FunctionType:
        all_tools = self.get_all_tools()
        return all_tools[name]

    def get_code_from_name(self, name: str) -> str:
        with open(os.path.join(self.tool_folder, f"{name}.py"), mode="r") as file:
            return file.read()

    def get_temp_tool_from_code(self, code: str, docstring_dict: dict[str, any]) -> types.FunctionType:
        self.save_tool_code(code, docstring_dict, True)
        name = self.get_name_from_code(code)
        specification = importlib.util.spec_from_file_location(name, location=os.path.join(self.tool_folder, "_tmp.py"))
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        return getattr(module, name)

    def update_tool_stats(self, tool_call: str, tool_was_effective: bool) -> None:
        stats_file = self.tool_folder + "_stats.json"
        split_call = tool_call.split("(", maxsplit=1)[0]
        if split_call not in self.get_all_tools():
            LOGGER.warning(f"Could not find tool called \'{split_call}\'.")
            return

        if os.path.isfile(stats_file):
            with open(stats_file, mode="r") as file:
                stats = json.load(file)
        else:
            stats = dict()

        key = "is_effective" if tool_was_effective else "not_effective"
        subdict = stats.get(split_call)
        if subdict is None:
            subdict = {key: 1}
            stats[split_call] = subdict

        else:
            subdict[key] = subdict.get(key, 0) + 1

        with open(stats_file, mode="w") as file:
            json.dump(stats, file)
