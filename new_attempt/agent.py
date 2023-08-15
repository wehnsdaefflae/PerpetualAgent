from __future__ import annotations
import threading
from dataclasses import dataclass
from typing import NamedTuple

from new_attempt.dummy_data.actions import ACTIONS
from new_attempt.dummy_data.facts import FACTS
from new_attempt.model.storages.action_storage import ActionStorage
from new_attempt.model.storages.fact_storage import FactStorage


@dataclass
class AgentArguments:
    task: str

    read_facts_global: bool
    read_actions_global: bool
    write_facts_local: bool
    write_actions_local: bool

    confirm_actions: bool

    llm_thought: str
    llm_action: str
    llm_parameter: str
    llm_result: str
    llm_fact: str
    llm_summary: str


@dataclass
class Step:
    thought: str
    action_id: str
    action_is_local: bool
    arguments: dict[str, any]
    result: str
    fact_id: str
    fact_is_local: bool


class Agent(threading.Thread):
    global_fact_storage = FactStorage(_facts=FACTS)             # same data source as in model.model.Model
    global_action_storage = ActionStorage(_actions=ACTIONS)     # same data source as in model.model.Model

    def __init__(self, agent_id: str, arguments: AgentArguments, max_steps: int = 20, _summary: str | None = None, _past_steps: list[Step] | None = None) -> None:
        super().__init__()
        self.agent_id = agent_id
        self.arguments = arguments
        """
        read_facts_global: bool
        read_actions_global: bool
        write_facts_local: bool
        write_actions_local: bool
        """

        self.status = "working"
        if _summary is None:
            self.summary = ""
        else:
            self.summary = _summary

        self.max_steps = max_steps
        if _past_steps is None:
            self.past_steps = list[Step]()
        else:
            self.past_steps = list[Step](_past_steps[-max_steps:])

        self.local_fact_storage = FactStorage()
        self.local_action_storage = ActionStorage()

    def _infer(self, user_input: str, summary: str) -> str:
        thought = ""

        pass

    def _retrieve_action_from_repo(self, thought: str) -> str:
        action = Agent.global_action_storage.retrieve_action(thought)
        if action is None:
            action = ""
        return action

    def _retrieve_facts_from_memory(self, thought: str) -> list[str]:
        return Agent.global_fact_storage.retrieve_facts(thought)

    def _extract_parameters(self, thought: str, retrieved_facts: list[str], selected_action: str) -> dict[str, any]:
        pass

    def _execute_action(self, selected_action: str, action_params: dict[str, any]) -> str:
        pass

    def _generate_fact(self, thought: str, result: str) -> tuple[str, bool]:
        pass

    def _update_initiate_summary(self, request: str, previous_summary: str, new_fact: str) -> tuple[str, bool]:
        pass

    def _increase_action_value(self, action: str) -> None:
        # add, if not present
        Agent.global_action_storage.add_action(str(len(Agent.global_action_storage)), action)
        # increase success count
        pass

    def _decrease_action_value(self, action: str) -> None:
        # decrease success count
        c = 0
        # remove if below threshold
        if c < 0:
            Agent.global_action_storage.remove_action(action)
        pass

    def _save_summary(self, summary: str, is_fulfilled: bool) -> None:
        pass

    def process(self) -> None:
        iteration = 0

        while True:
            thought = self._infer(self.arguments.task, self.summary)
            selected_action = self._retrieve_action_from_repo(thought)
            retrieved_facts = self._retrieve_facts_from_memory(thought)
            action_params = self._extract_parameters(thought, retrieved_facts, selected_action)
            result = self._execute_action(selected_action, action_params)
            new_fact, was_successful = self._generate_fact(thought, result)
            Agent.global_fact_storage.add_fact(new_fact)

            if was_successful:
                self._increase_action_value(selected_action)
            else:
                self._decrease_action_value(selected_action)

            self.summary, is_fulfilled = self._update_initiate_summary(self.arguments.task, self.summary, new_fact)
            self._save_summary(self.summary, is_fulfilled)

            iteration += 1

    def run(self) -> None:
        self.process()
