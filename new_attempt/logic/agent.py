from __future__ import annotations

import random
import threading
from dataclasses import asdict
from typing import Literal, Callable

from new_attempt.logic.various import AgentArguments, Step, Fact, Action, ActionArguments
from new_attempt.model.storages.generic_storage import VectorStorage


class Agent(threading.Thread):
    @staticmethod
    def from_dict(agent_dict: dict[str, any],
                  fact_storage: VectorStorage[Fact], action_storage: VectorStorage[Action],
                  thought_to_view: Callable[[Agent, str], None],
                  action_to_view: Callable[[Agent, Action], None],
                  facts_to_view: Callable[[Agent, set[Fact]], None],
                  params_to_view: Callable[[Agent, ActionArguments], None],
                  output_to_view: Callable[[Agent, str], None],
                  fact_to_view: Callable[[Agent, Fact, bool], None],
                  summary_to_view: Callable[[Agent, str, bool], None],
                  ) -> Agent:
        agent_arguments = AgentArguments(**agent_dict.pop("arguments"))

        return Agent(
            agent_dict["agent_id"],
            agent_arguments,
            fact_storage, action_storage,
            thought_to_view, action_to_view, facts_to_view, params_to_view, output_to_view, fact_to_view, summary_to_view,
            max_steps=agent_dict["max_steps"],
            _status=agent_dict["status"],
            _summary=agent_dict["summary"],
            _past_steps=agent_dict["past_steps"],
        )

    def __init__(self,
                 agent_id: str, arguments: AgentArguments,
                 fact_storage: VectorStorage[Fact], action_storage: VectorStorage[Action],
                 thought_to_view: Callable[[Agent, str], None],
                 action_to_view: Callable[[Agent, Action], None],
                 facts_to_view: Callable[[Agent, set[Fact]], None],
                 params_to_view: Callable[[Agent, ActionArguments], None],
                 output_to_view: Callable[[Agent, str], None],
                 fact_to_view: Callable[[Agent, Fact, bool], None],
                 summary_to_view: Callable[[Agent, str, bool], None],
                 max_steps: int = 20,
                 _status: Literal["finished", "pending", "working", "paused"] = "paused", _summary: str = "", _past_steps: list[Step] | None = None) -> None:
        super().__init__()
        self.agent_id = agent_id
        self.arguments = arguments

        self.status = _status
        self.summary = _summary

        self.max_steps = max_steps
        if _past_steps is None:
            self.past_steps = list[Step]()
        else:
            self.past_steps = list[Step](_past_steps[-max_steps:])

        self.fact_storage = fact_storage
        self.action_storage = action_storage

        self.iterations = 0

    def to_dict(self) -> dict[str, any]:
        return {
            "agent_id": self.agent_id,
            "arguments": asdict(self.arguments),
            "max_steps": self.max_steps,
            "status": self.status,
            "summary": self.summary,
            "past_steps": self.past_steps,
        }

    def _infer(self, user_input: str, summary: str) -> str:
        return f"thought {self.iterations}"

    def _retrieve_action_from_repo(self, thought: str, exclude: list[Action] | None = None) -> Action:
        action = self.action_storage.add_content(f"action for {thought}", local_agent_id=self.agent_id)
        return action

    def _retrieve_facts_from_memory(self, thought: str) -> list[str]:
        all_global_facts = self.fact_storage.get_elements()
        all_local_facts = self.fact_storage.get_elements(local_agent_id=self.agent_id)
        selected_global = random.sample(all_global_facts, k=min(3, len(all_global_facts)))
        selected_local = random.sample(all_local_facts, k=min(2, len(all_local_facts)))
        return selected_local + selected_global

    def _extract_arguments(self, thought: str, retrieved_facts: list[str], selected_action: Action) -> ActionArguments:
        return {
            "action_name": selected_action.action,
            "arguments_from": thought,
            "no_retrieved_facts": len(retrieved_facts)
        }

    def _execute_action(self, selected_action: Action, action_arguments: ActionArguments) -> str:
        return f"output for {selected_action.action}"

    def _generate_fact(self, thought: str, output: str) -> tuple[Fact, bool]:
        fact_content = f"fact combining {thought} and {output}"
        return self.fact_storage.add_content(fact_content, local_agent_id=self.agent_id), random.choice([True, False])

    def _update_initiate_summary(self, request: str, previous_summary: str, fact: Fact) -> tuple[str, bool]:
        pass

    def _increase_action_value(self, action: Action) -> None:
        action.success += 1
        self.action_storage.update_element(action)

    def _decrease_action_value(self, action: Action) -> None:
        action.failure += 1
        self.action_storage.update_element(action)

    def _save_summary(self, summary: str, is_fulfilled: bool) -> None:
        pass

    def run(self) -> None:
        iteration = 0

        while self.status == "working":
            thought = self._infer(self.arguments.task, self.summary)
            # send thought to view

            retrieved_facts = self._retrieve_facts_from_memory(thought)
            # send facts to view

            failed_actions = list()
            while True:
                selected_action = self._retrieve_action_from_repo(thought, failed_actions)
                # send action to view

                action_arguments = self._extract_arguments(thought, retrieved_facts, selected_action)
                # send arguments to view

                output = self._execute_action(selected_action, action_arguments)
                # send output to view

                fact, was_successful = self._generate_fact(thought, output)
                # send new fact, success to view

                if was_successful:
                    self._increase_action_value(selected_action)
                    break

                self._decrease_action_value(selected_action)

                failed_actions.append(selected_action)
                if len(failed_actions) >= self.arguments.action_attempts:
                    break

            self.summary, is_fulfilled = self._update_initiate_summary(self.arguments.task, self.summary, fact)
            # send summary, is_fulfilled to view

            self._save_summary(self.summary, is_fulfilled)

            iteration += 1
