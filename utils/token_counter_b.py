# functions.py
FunctionDef = dict[str, str | dict]
Prop = dict[str, str | int | bool | None | list]
ObjectProp = dict[str, str | dict]


def format_function_definitions(functions: list[FunctionDef]) -> str:
    lines = ["namespace functions {", ""]
    for f in functions:
        if f.get('description'):
            lines.append(f"// {f.get('description')}")
        if f['parameters'].get('properties'):
            lines.append(f"type {f.get('name')} = (_: {{")
            lines.append(format_object_properties(f['parameters'], 0))
            lines.append("}) => any;")
        else:
            lines.append(f"type {f.get('name')} = () => any;")
        lines.append("")
    lines.append("} // namespace functions")
    return "\n".join(lines)


def format_object_properties(obj: ObjectProp, indent: int) -> str:
    lines = []
    for name, param in obj.get('properties', {}).items():
        if param.get('description'):
            lines.append(f"// {param.get('description')}")
        if obj.get('required') and name in obj.get('required'):
            lines.append(f"{name}: {format_type(param, indent)},")
        else:
            lines.append(f"{name}?: {format_type(param, indent)},")
    return "\n".join(' ' * indent + line for line in lines)


def format_type(param: Prop, indent: int) -> str:
    if param['type'] == "string":
        if param.get('enum'):
            return " | ".join(f'"{v}"' for v in param.get('enum'))
        return "string"
    elif param['type'] in ("number", "integer"):
        if param.get('enum'):
            return " | ".join(str(v) for v in param.get('enum'))
        return "number"
    elif param['type'] == "boolean":
        return "boolean"
    elif param['type'] == "null":
        return "null"
    elif param['type'] == "object":
        return "{\n" + format_object_properties(param, indent + 2) + "\n}"
    else:
        return ""
