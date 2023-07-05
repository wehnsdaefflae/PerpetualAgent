# coding=utf-8
SUMMARY_ACTION_RESULT = (
    "=== Current summary ===\n"
    "{summary}\n"
    "LAST ACTION: {last_action}"
    "ACTION RESULT: {action_result}"
)

example = SUMMARY_ACTION_RESULT.format(
    summary="After checking the users digital calendar, it was determined that the user is available on next Tuesday at 10 am.",
    last_action="Send meeting invitations to the members of the project team through the email contacts or a platform like Google Meet, Microsoft Teams, etc.",
    action_result="All team members accept the invitation, and the meeting is successfully scheduled for next Tuesday at 10 am."
)

STEP_SUMMARIZER = (
    "Gradually expand the current summary with the last action taken to fulfil the request and the result of that "
    "action, adding to the previous summary and creating a new one.\n"
    "\n"
    "EXAMPLE\n"
    "=== Request ===\n"
    "Arrange a meeting with my project team next Tuesday at 10 am, and find a suitable restaurant for lunch afterwards.\n"
    "\n",
    f"{example}\n"
    "=== New summary ===\n"
    "After finding a suitable time for the user, the project team members were invited for the next Tuesday at 10 am "
    "and everyone accepted the invitation for lunch.\n"
    "END OF EXAMPLE\n"
    "\n"
    "=== Request ===\n"
    "{request}\n"
    "\n"
    "=== Current summary ===\n"
    "{summary}\n"
    "\n"
    "=== New summary ==="
)

DOCSTRING_WRITER = (
    "Task:\n"
    "{task}\n"
    "===\n"
    "\n"
    "Generate a Google style docstring in triple quotation marks for a Python function that could "
    "solve the task above. Describe the function as if it already existed. Make it is easy to infer "
    "from the description which use cases and contexts the function applies to. Use function "
    "arguments to make sure that the function can be applied to other tasks as well.\n"
    "\n"
    "The docstring must contain a function description, as well as the sections \"Example\", "
    "\"Args\", and \"Returns\". Make sure to indent the content of each section.\n"
    "\n"
    "Call the function in the Example section like so: `>>> function_name(arg, [...], kwarg=val, "
    "[...])`. Make sure to include the names of keyword arguments. Provide only one example with "
    "arguments for a representative use case. Do not show the return value of the function call.\n"
    "\n"
    "Use exactly one line for each argument in the Args section.\n"
    "\n"
    "If the function returns a dictionary, list all keys that the dictionary contains and describe "
    "their according values in the Returns section.\n"
    "\n"
    "Do not mention particular use cases or contexts in the description.\n"
    "Mention the name of the function only in the Example section but not in the description.\n"
    "Describe what the function does, not how it is done.\n"
    f"\n"
    f"Keep it below 500 characters.")

REQUEST_IMPROVER = (
    "Request:\n"
    "{request}\n"
    "==============\n"
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
    "\n"
    "Respond only with the improved version of the request. Make it concise and to the point. Write between two and "
    "five sentences, do not use bullet points, do not address the points above explicitly, do not include any of the "
    "above points in your response, and do not encourage checking back. They're on their own on this one.")

CODER = (
    f"Available helper functions:\n"
    "{tool_descriptions}\n"
    f"=================\n"
    f"Docstring:\n"
    "{docstring}\n"
    f"=================\n"
    "Generate a Python function that fully implements the docstring above. Make it general enough to be used in "
    "diverse use cases and contexts. The function must be type hinted, working, and every aspect must be implement "
    "according to the docstring.\n"
    "\n"
    "Make use of the available helper functions from the list above by importing them from the tools module (e.g. for "
    "the calculate tool: `from tools.calculate import calculate`).\n"
    "\n"
    "Do not use placeholders that must be filled in later (e.g. API keys).\n"
    "\n"
    "Respond with a single Python code block containing only the required imports as well as the function including "
    "the above docstring. Format the docstring according to the Google style guide.")