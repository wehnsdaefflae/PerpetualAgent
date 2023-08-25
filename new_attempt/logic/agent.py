from __future__ import annotations

import random
import threading
import time
from dataclasses import asdict, dataclass
from typing import Literal, Callable

from new_attempt.controller.classes import Fact, Action, ActionArguments, AgentArguments
from new_attempt.model.storages.generic_storage import VectorStorage


@dataclass
class Step:
    @staticmethod
    def from_dict(step_dict: dict[str, any]) -> Step:
        action = step_dict["action"]
        relevant_facts = step_dict["relevant_facts"]
        fact = step_dict["fact"]

        return Step(
            thought=step_dict["thought"],
            action=None if action is None else Action.from_dict(action),
            relevant_facts=None if relevant_facts is None else [Fact.from_dict(fact_dict) for fact_dict in relevant_facts],
            action_arguments=step_dict["action_arguments"],
            output=step_dict["output"],
            fact=None if fact is None else Fact.from_dict(fact),
            was_successful=step_dict["was_successful"],
            summary=step_dict["summary"],
        )

    thought:            str | None = None
    action:             Action | None = None
    relevant_facts:     list[Fact] | None = None
    action_arguments:   ActionArguments | None = None
    output:             str | None = None
    fact:               Fact | None = None
    was_successful:     bool | None = None
    summary:            str | None = None

    def to_dict(self) -> dict[str, any]:
        return {
            "thought":          self.thought,
            "action":           None if self.action is None else self.action.to_dict(),
            "relevant_facts":   None if self.relevant_facts is None else [fact.to_dict() for fact in self.relevant_facts],
            "action_arguments": self.action_arguments,
            "output":           self.output,
            "fact":             None if self.fact is None else self.fact.to_dict(),
            "was_successful":   self.was_successful,
            "summary":          self.summary,
        }


class StepHistory:
    @staticmethod
    def from_dict(step_history_dict: dict[str, any]) -> StepHistory:
        past_steps = step_history_dict["past_steps"]
        return StepHistory(
            max_steps=step_history_dict["max_steps"],
            _past_steps=[Step.from_dict(each_step) for each_step in past_steps],
        )

    def __init__(self, max_steps: int = 20, _past_steps: list[Step] | None = None) -> None:
        self.max_steps = max_steps
        if _past_steps is None:
            self.current_step = Step()
            self.past_steps = [self.current_step]
        else:
            self.past_steps = _past_steps
            self.current_step = self.past_steps[-1]

    def to_dict(self) -> dict[str, any]:
        return {
            "max_steps": self.max_steps,
            "past_steps": [each_step.to_dict() for each_step in self.past_steps],
        }

    def next_step(self) -> None:
        self.current_step = Step()
        self.past_steps.append(self.current_step)
        del self.past_steps[:-self.max_steps]

    def set_thought(self, thought: str) -> None:
        self.current_step.thought = thought

    def set_action(self, action: Action) -> None:
        self.current_step.action = action

    def set_relevant_facts(self, relevant_facts: list[Fact]) -> None:
        self.current_step.relevant_facts = relevant_facts

    def set_action_arguments(self, action_arguments: ActionArguments) -> None:
        self.current_step.action_arguments = action_arguments

    def set_output(self, output: str) -> None:
        self.current_step.output = output

    def set_fact(self, fact: Fact) -> None:
        self.current_step.fact = fact

    def set_was_successful(self, was_successful: bool) -> None:
        self.current_step.was_successful = was_successful

    def set_summary(self, summary: str) -> None:
        self.current_step.summary = summary


class Agent(threading.Thread):
    @staticmethod
    def from_dict(agent_dict: dict[str, any],
                  fact_storage: VectorStorage[Fact], action_storage: VectorStorage[Action]) -> Agent:

        arguments = agent_dict.pop("arguments")
        agent_arguments = AgentArguments(**arguments)

        history = agent_dict.pop("history")

        return Agent(
            agent_dict["agent_id"],
            agent_arguments,
            fact_storage, action_storage,
            _status=agent_dict["status"],
            _summary=agent_dict["summary"],
            _history=StepHistory.from_dict(history),
        )

    def __init__(self,
                 agent_id: str, arguments: AgentArguments,
                 fact_storage: VectorStorage[Fact], action_storage: VectorStorage[Action],
                 _status: Literal["finished", "pending", "working", "paused"] = "paused", _summary: str = "", _history: StepHistory | None = None) -> None:

        self.agent_id = agent_id  # must be here for hash required in Thread.__init__
        super().__init__()
        self.arguments = arguments

        self.status = _status
        self.summary = _summary

        self.history = _history or StepHistory()

        self.fact_storage = fact_storage
        self.action_storage = action_storage

        self.update_details_view = None
        self.save_state = None

        self.iterations = 0

    def __hash__(self) -> int:
        return hash(self.agent_id)

    def to_dict(self) -> dict[str, any]:
        return {
            "agent_id": self.agent_id,
            "arguments": asdict(self.arguments),
            "status": self.status,
            "summary": self.summary,
            "history": self.history.to_dict(),
        }

    def connect_view(self, update_details_view: Callable[[Agent], None],) -> None:
        self.update_details_view = update_details_view

    def connect_model(self, save_state: Callable[[Agent], None]) -> None:
        self.save_state = save_state

    def _infer(self, user_input: str, summary: str) -> str:
        time.sleep(2)

        return f"thought {self.iterations}"

    def _retrieve_action_from_repo(self, thought: str, exclude: list[Action] | None = None) -> Action:
        time.sleep(2)

        action,  = self.action_storage.store_contents([f"action for {thought}"], local_agent_id=self.agent_id)
        return action

    def _retrieve_facts_from_memory(self, thought: str) -> list[Fact]:
        time.sleep(2)

        all_global_facts = self.fact_storage.get_elements()
        all_local_facts = self.fact_storage.get_elements(local_agent_id=self.agent_id)
        selected_global = random.sample(all_global_facts, k=min(3, len(all_global_facts)))
        selected_local = random.sample(all_local_facts, k=min(2, len(all_local_facts)))
        return selected_local + selected_global

    def _extract_arguments(self, thought: str, retrieved_facts: list[Fact], selected_action: Action) -> ActionArguments:
        time.sleep(2)

        return {
            "action_name": selected_action.content,
            "arguments_from": thought,
            "no_retrieved_facts": len(retrieved_facts)
        }

    def _execute_action(self, selected_action: Action, action_arguments: ActionArguments) -> str:
        time.sleep(2)

        return f"output for {selected_action.content}"

    def _generate_fact(self, thought: str, output: str) -> tuple[Fact, bool]:
        time.sleep(2)

        fact_content = f"fact combining {thought} and {output}"
        fact, = self.fact_storage.store_contents([fact_content], local_agent_id=self.agent_id)
        return fact, random.choice([True, False])

    def _update_summary(self, request: str, previous_summary: str, fact: Fact) -> tuple[str, bool]:
        time.sleep(2)

        return f"summary including {fact.storage_id}", random.random() < .1

    def _increase_action_value(self, action: Action) -> None:
        action.success += 1
        self.action_storage.update_elements([action])

    def _decrease_action_value(self, action: Action) -> None:
        action.failure += 1
        self.action_storage.update_elements([action])

    def run(self) -> None:
        if self.update_details_view is None:
            raise ValueError("Agent callbacks not connected")

        iteration = 0

        while self.status == "working":
            thought = self._infer(self.arguments.task, self.summary)
            self.history.set_thought(thought)
            self.update_details_view(self)

            retrieved_facts = self._retrieve_facts_from_memory(thought)
            self.history.set_relevant_facts(retrieved_facts)
            self.update_details_view(self)

            failed_actions = list()
            while True:
                selected_action = self._retrieve_action_from_repo(thought, failed_actions)
                self.history.set_action(selected_action)
                self.update_details_view(self)

                action_arguments = self._extract_arguments(thought, retrieved_facts, selected_action)
                self.history.set_action_arguments(action_arguments)
                self.update_details_view(self)

                output = self._execute_action(selected_action, action_arguments)
                self.history.set_output(output)
                self.update_details_view(self)

                fact, was_successful = self._generate_fact(thought, output)
                self.history.set_fact(fact)
                self.history.set_was_successful(was_successful)

                if was_successful:
                    self._increase_action_value(selected_action)
                    break

                self._decrease_action_value(selected_action)

                failed_actions.append(selected_action)
                if len(failed_actions) >= self.arguments.action_attempts:
                    break

            self.summary, is_fulfilled = self._update_summary(self.arguments.task, self.summary, fact)
            self.history.set_summary(self.summary)
            self.update_details_view(self)

            self.save_state(self)

            if is_fulfilled:
                self.status = "finished"
            else:
                self.history.next_step()

            iteration += 1
