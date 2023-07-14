extract_next_step = {
    "name": "extract_next_step",
    "description": "Extract the next step to be performed given the current progress towards fulfilling a request as it is documented in the "
                   "conversation history. Think step-by-step and extract reasonably small steps. If the history is empty, respond with the first step.",
    "parameters": {
        "type": "object",
        "properties": {
            "next_step": {
                "description": "A one sentence instruction describing the next step to be performed towards fulfilling the request. Do not repeat steps. If the "
                               "previous step failed, try another approach. If it succeeded, make a new step.",
                "type": "string"
            },
            "is_done": {
                "description": "Whether or not the request is already completely fulfilled. 'True' only if the conversation history shows beyond any doubt that the "
                               "request is fulfilled and there are not outstanding steps left to perform. In this case, the string in `next_step` is irrelevant. "
                               "'False' in case there's any uncertainty or outstanding steps to be performed.",
                "type": "boolean"
            }
        },
        "required": ["next_step", "is_done"]
    }
}

general_solver = {
    "name": "general_solver",
    "description": "Fulfills a general request. Works for all kinds of requests. Use this if there's no better action for the request at hand.",
    "parameters": {
        "type": "object",
        "properties": {
            "request": {
                "description": "The request to be fulfilled.",
                "type": "string"
            }
        },
        "required": ["request"]
    }
}

is_request_fulfilled = {
    "name": "is_request_fulfilled",
    "description": "Registers whether or not the previously performed steps in the conversation history completely fulfill a request.",
    "parameters": {
        "type": "object",
        "properties": {
            "is_fulfilled": {
                "description": "Whether or not the request is completely fulfilled. Pass 'True' only if the conversation history shows beyond any doubt that the "
                               "request is fulfilled and there are not outstanding steps left to perform. In case there's any uncertainty or outstanding steps, "
                               "pass 'False'.",
                "type": "boolean"
            }
        },
        "required": ["is_fulfilled"]
    }
}

composed_response = {
    "name": "composed_response",
    "description": "Sends a response that fulfills a given request and is composed of responses in the message history.",
    "parameters": {
        "type": "object",
        "properties": {
            "response": {
                "description": "The response to the request, composed of responses in the message history.",
                "type": "string"
            }
        },
        "required": ["response"]
    }
}

get_intermediate_results = {
    "name": "get_intermediate_results",
    "description": "Returns the response to a request, split up into a list of intermediate results. Together, these intermediate results provide all the information "
                   "necessary to compose a single complete response that fulfills the given request.",
    "parameters": {
        "type": "object",
        "properties": {
            "request": {
                "description": "The request to be fulfilled.",
                "type": "string"
            }
        },
        "required": ["request"]
    }
}

docstring_schema = {
    "name": "make_docstring",
    "description": "Generates a Google style docstring for a given function.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "description": "A descriptive name for the function.",
                "type": "string"
            },
            "summary": {
                "description": "A one sentence summary of the function.",
                "type": "string"
            },
            "description": {
                "description": "A brief explanation of the function. It should be a clear, concise overview of what the function does.",
                "type": "string"
            },
            "args": {
                "description": "A list of dictionaries describing the function's arguments. Empty if the function does not take any arguments.",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "description": "The name of the argument.",
                            "type": "string"
                        },
                        "python_type": {
                            "description": "The type of the argument.",
                            "type": "string"
                        },
                        "argument_passing_style": {
                            "description": "The passing style of the argument. `positional` if the argument is positional, `keyword` if the argument is optional.",
                            "type": "string",
                            "enum": ["positional", "keyword"]
                        },
                        "description": {
                            "description": "A description of the argument without the default value.",
                            "type": "string"
                        },
                        "default_value": {
                            "description": "Not set for positional arguments. The default value of the keyword argument. `None` if optional."
                        },
                        "example_value": {
                            "description": "An example value for the argument.",
                        }
                    },
                    "required": ["name", "type", "arg_type", "description", "example_value"]
                }
            },
            "return_value": {
                "type": "object",
                "description": "A dictionary describing the function's return value. Empty if the function does not return anything.",
                "properties": {
                    "python_type": {
                        "description": "The type of the return value. `None` if the function does not return anything.",
                        "type": "string"
                    },
                    "description": {
                        "description": "A description of the return value, including all keys, values and their types in case the return type is a dictionary or is "
                                       "composed of dictionaries.",
                        "type": "string"
                    },
                    "example_value": {
                        "description": "An example for the function return value. Make sure it makes sense in combination with the arguments' example values."
                    }
                },
                "required": ["type", "description", "example_value"]
            }
        },
        "required": ["name", "summary", "description", "args", "return_value"]
    }
}
