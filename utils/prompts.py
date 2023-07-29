# coding=utf-8
PROGRESS_REPORT = (
    "# Progress report\n"
    "## Request\n"
    "{request}\n"
    "\n"
    "## Current progress\n"
    "{progress}\n"
    "\n"
    "## Last step\n"
    "### Action\n"
    "{action}\n"
    "\n"
    "### Result\n"
    "{result}")

_EXAMPLE = PROGRESS_REPORT.format(
    request="Arrange a meeting with my project team next Tuesday at 10 am, and find a suitable restaurant for lunch afterwards.",
    progress="After checking the users digital calendar, it was determined that the user is available on next Tuesday at 10 am.",
    action="Send meeting invitations to the members of the project team through the email contacts or a platform like Google Meet, Microsoft Teams, etc.",
    result="All team members accept the invitation, and the meeting is successfully scheduled for next Tuesday at 10 am."
)

PROGRESS_UPDATER = (
    f"## Instructions\n"
    f"Gradually update the current progress with the last step (i.e., action and result) that has been taken to fulfill the request.\n"
    f"\n"
    f"<! -- BEGIN EXAMPLE -->\n"
    f"{_EXAMPLE}\n"
    f"\n"
    f"## Updated progress report\n"
    f"After finding a suitable time for the user, the project team members were invited for the next Tuesday at 10 am "
    f"and everyone accepted the invitation for lunch.\n"
    f"<! -- END EXAMPLE -->\n"
    f"\n"
    f"{{PROGRESS_REPORT}}\n"
    f"\n"
    f"## Updated progress report"
)

STEP_SUMMARIZER = (
    "## Instructions\n"
    "Summarize the action taken as well as its result, providing a concise report on the progress in fulfilling the request.\n"
    "\n"
    "## Request\n"
    "{request}\n"
    "\n"
    "## Action\n"
    "{action}\n"
    "\n"
    "## Result\n"
    "{result}\n"
    "\n"
    "## Progress report")

DOCSTRING_WRITER = (
    "## Action description\n"
    "{action}\n"
    "\n"
    "## Instructions"
    "Generate a Google style docstring in triple quotation marks for a Python function that could "
    "perform the action above. Don't incorporate literal information from the action description but use "
    "function arguments to make sure that the function can perform similar actions as well.\n"
    "The docstring must follow the Google style format, contain a function description, as well as "
    "the sections \"Example\", \"Args\", and \"Returns\". Make sure to indent the content of each "
    "section.\n"
    "- In the description: Do not mention the name of the function. Do not mention particular use "
    "cases or contexts. Describe what the function does, not how it is done. Describe the function "
    "as if it already existed. Make it is easy to infer from the description which in which use cases and "
    "contexts the function can be used.\n"
    "- In the 'Example' section: Call the function like so: `>>> function_name(arg, [...], kwarg=val, "
    "[...])`. Make sure to pass all arguments by name. Provide only one example with arguments for a "
    "representative use case. Do not show the return value of the function call.\n"
    "- In the 'Args' section: Use exactly one line for each argument. Make sure to put the argument type "
    "in brackets behind the name.\n"
    "- In the 'Returns' section: If the function returns a dictionary, describe all keys that the dictionary "
    "contains, as well as their according values and types.\n"
    f"Keep it below 500 characters.")

REQUEST_IMPROVER = (
    "## Request\n"
    "{request}\n"
    "\n"
    "## Instructions\n"
    "Provide an improved version of this request by incorporating the following points:\n"
    "1. Identify the Purpose of the Request: What is the objective of the request? Understand the aim behind the "
    "request. This will give the instruction a clear direction.\n"
    "2. Specify the Action: What needs to be done? The action should be clearly defined. Instead of saying \"improve "
    "the report\", say \"add more data analysis and revise the formatting of the report.\"\n"
    "3. Details Matter: Give as much detail as you can. Be specific about what exactly needs to be done. Use precise, "
    "concrete language.\n"
    "4. Define the Scope: What is the extent of the request? For instance, does the request pertain to one particular "
    "chapter of a report or the entire report?\n"
    "5. Indicate the Format: If there is a specific way to fulfill the request, provide this information. For "
    "example, if you are requesting a report, specify whether you want it in Word, PDF, or another format.\n"
    "6. Clarify the Success Criteria: How will you judge whether the request has been fulfilled? What does the end "
    "result look like? It's important to convey your expectations.\n"
    "7. Address Potential Challenges: Think about the possible difficulties in fulfilling the request, and provide "
    "solutions or suggestions on how to deal with them.\n"
    "8. Provide Resources or Assistance if Needed: If there are any tools, references, or people that might help "
    "fulfill the request, mention them.\n"
    "Respond only with the improved version of the request. Make it concise and to the point. Write between two and "
    "five sentences, do not use bullet points, do not address the points above explicitly, do not include any of the "
    "above points in your response, and do not encourage checking back. They're on their own on this one.")

CODER = (
    f"## Available helper functions\n"
    "{tool_descriptions}\n"
    f"\n"
    f"## Docstring\n"
    "{docstring}\n"
    f"\n"
    "## Instructions\n"
    "Generate a fully functioning type hinted Python function that implements the docstring above.\n"
    "Make use of the available helper functions from the provided list by importing them from the tools module (e.g. for the calculate tool: `from tools.calculate "
    "import calculate`).\n"
    "Do not simulate behavior or use placeholder logic or variables that must be filled in manually (e.g. API keys)!\n"
    "Respond with a single Python code block containing as statements nothing else but the required imports and one single definition of a working function.")
