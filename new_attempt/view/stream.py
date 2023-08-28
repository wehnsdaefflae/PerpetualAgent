from dataclasses import dataclass

import nicegui

from new_attempt.logic.classes import Fact


@dataclass
class ActionAttempt:
    name: str
    arguments_json: str | None = None
    output_json: str | None = None
    resulting_fact: Fact | None = None
    is_successful: bool | None = None


@dataclass
class Step:
    thought: str
    relevant_facts: list[Fact] | None = None
    action_attempts: tuple[ActionAttempt, ...] = tuple[ActionAttempt]()
    is_successful: bool | None = None
    summary: str | None = None


class Stream(nicegui.ui.column):
    def __init__(self):
        super().__init__()
        self.steps = list[Step]()

    def draw(self) -> None:
        for each_step in self.steps:
            with (nicegui.ui.expansion(text=each_step.thought) as thought_expansion):
                if each_step.is_successful is None:
                    thought_expansion.classes("full-width bg-yellow-300 rounded-lg")
                elif each_step.is_successful:
                    thought_expansion.classes("full-width bg-green-300 rounded-lg")
                else:
                    thought_expansion.classes("full-width bg-red-300 rounded-lg")

                if each_step.relevant_facts is None:
                    each_label = nicegui.ui.label("retrieving relevant facts...")
                    return
                with nicegui.ui.expansion(text="relevant facts") as fact_expansion:
                    fact_expansion.classes("full-width pl-8 bg-blue-300")
                    for each_fact in each_step.relevant_facts:
                        each_label = nicegui.ui.label(each_fact.content)
                        each_label.classes("flex-1 m-3 p-3 rounded-lg")

                for each_action_attempt in each_step.action_attempts:
                    if each_action_attempt.name is None:
                        each_label = nicegui.ui.label("deciding on action...")
                        return
                    with nicegui.ui.expansion(text=f"attempt #{each_action_attempt.name}") as action_expansion:
                        if each_action_attempt.is_successful is None:
                            action_expansion.classes("full-width pl-8 bg-yellow-300")
                        elif each_action_attempt.is_successful:
                            action_expansion.classes("full-width pl-8 bg-green-300")
                        else:
                            action_expansion.classes("full-width pl-8 bg-red-300")

                        if each_action_attempt.arguments_json is None:
                            each_label = nicegui.ui.label("extracting action parameters...")
                            return
                        nicegui.ui.markdown(f"```json\n{each_action_attempt.arguments_json}\n```")

                        if each_action_attempt.output_json is None:
                            each_label = nicegui.ui.label("executing action...")
                            return
                        nicegui.ui.markdown(f"```json\n{each_action_attempt.output_json}\n```")

                        if each_action_attempt.resulting_fact is None:
                            each_label = nicegui.ui.label("composing fact...")
                            return
                        each_label = nicegui.ui.label(each_action_attempt.resulting_fact.content)
                        each_label.classes("flex-1 m-3 p-3 bg-blue-200 rounded-lg")

                if each_step.summary is None:
                    each_label = nicegui.ui.label("summarizing...")
                    return

                each_label = nicegui.ui.label(each_step.summary)
                each_label.classes("flex-1 m-3 p-3 bg-white rounded-lg")
