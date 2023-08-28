from __future__ import annotations

import random
import threading
import time
from dataclasses import asdict, dataclass
from typing import Literal, Callable

from new_attempt.logic.classes import Fact, Action, AgentArguments, Thought, ActionArguments, ActionOutput, ActionWasSuccessful, Summary, IsFulfilled, \
    Dictable


@dataclass
class ViewCallbacks:
    new_thought: Callable[[Thought], None]
    new_relevant_facts: Callable[[list[Fact]], None]
    new_action_attempts: Callable[[], None]
    new_action: Callable[[Action], None]
    new_action_arguments: Callable[[ActionArguments], None]
    new_action_output: Callable[[ActionOutput], None]
    new_fact: Callable[[Fact], None]
    new_was_successful: Callable[[ActionWasSuccessful], None]
    new_summary: Callable[[Summary], None]
    new_is_fulfilled: Callable[[IsFulfilled], None]

    update_view: Callable[[], None]


@dataclass
class ModelCallbacks:
    store_actions: Callable[[list[str], str | None], list[Action]]
    store_facts: Callable[[list[str], str | None], list[Fact]]
    get_actions: Callable[[list[str] | None, str | None], list[Action]]
    get_facts: Callable[[list[str] | None, str | None], list[Fact]]
    update_actions: Callable[[list[Action]], None]
    update_facts: Callable[[list[Fact]], None]


C = Thought | list[Fact] | Action | ActionArguments | ActionOutput | ActionWasSuccessful | Fact | Summary | IsFulfilled


class ActionAttempt(Dictable):
    @staticmethod
    def from_dict(arguments_dict: dict[str, any]) -> ActionAttempt:
        return ActionAttempt(**arguments_dict)

    def __init__(self,
                 action: Action | None = None, action_arguments: ActionArguments | None = None,
                 output: ActionOutput | None = None, fact: Fact | None = None,
                 was_successful: ActionWasSuccessful | None = None) -> None:
        self.action = action
        self.action_arguments = action_arguments
        self.output = output
        self.fact = fact
        self.was_successful = was_successful

    def to_dict(self) -> dict[str, any]:
        return {
            "action": self.action.to_dict() if self.action is not None else None,
            "action_arguments": self.action_arguments.to_dict() if self.action_arguments is not None else None,
            "output": self.output.to_dict() if self.output is not None else None,
            "fact": self.fact.to_dict() if self.fact is not None else None,
            "was_successful": self.was_successful.to_dict() if self.was_successful is not None else None,
        }


class Step(Dictable):
    @staticmethod
    def from_dict(history_dict: dict[str, any]) -> Step:
        thought = history_dict["thought"]
        relevant_facts = history_dict["relevant_facts"]
        action_attempts = history_dict["action_attempts"]
        is_fulfilled = history_dict["is_fulfilled"]
        summary = history_dict["summary"]
        return Step(
            thought=Thought.from_dict(thought),
            relevant_facts=[Fact.from_dict(each_fact) for each_fact in relevant_facts],
            action_attempts=[ActionAttempt.from_dict(each_attempt) for each_attempt in action_attempts],
            is_fulfilled=IsFulfilled.from_dict(is_fulfilled),
            summary=Summary.from_dict(summary),
        )

    def __init__(self,
                 thought: Thought | None = None,
                 relevant_facts: list[Fact] | None = None,
                 action_attempts: list[ActionAttempt] | None = None,
                 is_fulfilled: IsFulfilled | None = None,
                 summary: Summary | None = None) -> None:
        self._thought = thought
        self._relevant_facts = relevant_facts
        self._action_attempts = action_attempts or list[ActionAttempt]()
        self._is_fulfilled = is_fulfilled
        self._summary = summary

    @property
    def thought(self) -> Thought | None:
        return self._thought

    @thought.setter
    def thought(self, thought: Thought) -> None:
        self._thought = thought

    @property
    def relevant_facts(self) -> list[Fact] | None:
        return self._relevant_facts

    @relevant_facts.setter
    def relevant_facts(self, relevant_facts: list[Fact]) -> None:
        self._relevant_facts = relevant_facts

    @property
    def action_attempts(self) -> list[ActionAttempt]:
        return self._action_attempts

    @action_attempts.setter
    def action_attempts(self, action_attempts: list[ActionAttempt]) -> None:
        self._action_attempts = action_attempts

    @property
    def is_fulfilled(self) -> IsFulfilled | None:
        return self._is_fulfilled

    @is_fulfilled.setter
    def is_fulfilled(self, is_fulfilled: IsFulfilled) -> None:
        self._is_fulfilled = is_fulfilled

    @property
    def summary(self) -> Summary | None:
        return self._summary

    @summary.setter
    def summary(self, summary: Summary) -> None:
        self._summary = summary

    def to_dict(self) -> dict[str, any]:
        return {
            "thought": self.thought.to_dict() if self.thought is not None else None,
            "relevant_facts": [each_fact.to_dict() for each_fact in self.relevant_facts] if self.relevant_facts is not None else None,
            "action_attempts": [each_attempt.to_dict() for each_attempt in self.action_attempts] if self.action_attempts is not None else None,
            "is_fulfilled": self.is_fulfilled.to_dict(),
            "summary": self.summary.to_dict() if self.summary is not None else None,
        }


class Agent(threading.Thread):
    @staticmethod
    def from_dict(agent_dict: dict[str, any]) -> Agent:

        arguments = agent_dict.pop("arguments")
        agent_arguments = AgentArguments(**arguments)

        history = agent_dict.pop("history")

        return Agent(
            agent_dict["agent_id"],
            agent_arguments,
            _status=agent_dict["status"],
            _summary=agent_dict["summary"],
            _history=[Step.from_dict(each_step) for each_step in history] if history is not None else None,
        )

    def __init__(self,
                 agent_id: str, arguments: AgentArguments,
                 _status: Literal["finished", "pending", "working", "paused"] = "paused", _summary: str = "", _history: list[Step] | None = None) -> None:

        self.agent_id = agent_id  # must be here for hash required in Thread.__init__
        super().__init__()
        self.arguments = arguments

        self.status = _status
        self.summary = _summary

        self.history = _history or list[Step]()
        self.working_on = Thought

        self.model_callbacks = None
        self.view_callbacks = None

        self.save_state = None

        self.iterations = 0

    def __hash__(self) -> int:
        return hash(self.agent_id)

    def connect_model_callbacks(self, model_callbacks: ModelCallbacks) -> None:
        self.model_callbacks = model_callbacks

    def connect_view_callbacks(self, view_callbacks: ViewCallbacks) -> None:
        self.view_callbacks = view_callbacks

    def to_dict(self) -> dict[str, any]:
        return {
            "agent_id": self.agent_id,
            "arguments": asdict(self.arguments),
            "status": self.status,
            "summary": self.summary,
            "history": [each_step.to_dict() for each_step in self.history],
        }

    def _infer(self, user_input: str, summary: str) -> Thought:
        time.sleep(2)

        return Thought(f"thought {self.iterations}")

    def _retrieve_action_from_repo(self, thought: str, exclude: list[Action] | None = None) -> Action:
        time.sleep(2)

        action,  = self.model_callbacks.store_actions([f"action for {thought}"], self.agent_id)
        return action

    def _retrieve_facts_from_memory(self, thought: str) -> list[Fact]:
        time.sleep(2)

        all_global_facts = self.model_callbacks.get_facts(None, None)
        all_local_facts = self.model_callbacks.get_facts(None, self.agent_id)
        selected_global = random.sample(all_global_facts, k=min(3, len(all_global_facts)))
        selected_local = random.sample(all_local_facts, k=min(2, len(all_local_facts)))
        total = selected_local + selected_global
        now = time.time()
        for each_fact in total:
            each_fact.retrieved = now
        self.model_callbacks.update_facts(total)
        return total

    def _extract_arguments(self, thought: str, retrieved_facts: list[Fact], selected_action: Action) -> ActionArguments:
        time.sleep(2)

        return ActionArguments({
            "action_name": selected_action.content,
            "arguments_from": thought,
            "no_retrieved_facts": len(retrieved_facts)
        })

    def _execute_action(self, selected_action: Action, action_arguments: ActionArguments) -> ActionOutput:
        time.sleep(2)

        return ActionOutput(f"output for {selected_action.content}")

    def _generate_fact(self, thought: str, output: str) -> tuple[Fact, ActionWasSuccessful]:
        time.sleep(2)

        fact_content = f"fact combining {thought} and {output}"
        fact, = self.model_callbacks.store_facts([fact_content], self.agent_id)
        return fact, ActionWasSuccessful(random.choice([True, False]))

    def _update_summary(self, request: str, previous_summary: str, fact: Fact) -> tuple[Summary, IsFulfilled]:
        time.sleep(2)

        return Summary(f"summary including {fact.storage_id}"), IsFulfilled(random.random() < .1)

    def _increase_action_value(self, action: Action) -> None:
        action.success += 1
        self.model_callbacks.update_actions([action])

    def _decrease_action_value(self, action: Action) -> None:
        action.failure += 1
        self.model_callbacks.update_actions([action])

    def run(self) -> None:
        if self.model_callbacks is None:
            raise ValueError("Model callbacks not connected")

        if self.view_callbacks is None:
            raise ValueError("View callbacks not connected")

        iteration = 0

        while self.status == "working":
            current_step = Step()
            self.history.append(current_step)

            thought = self._infer(self.arguments.task, self.summary)
            current_step.thought = thought
            self.view_callbacks.new_thought(thought)

            retrieved_facts = self._retrieve_facts_from_memory(thought)
            current_step.relevant_facts = retrieved_facts
            self.view_callbacks.new_relevant_facts(retrieved_facts)

            failed_actions = list()
            while True:
                current_action_attempt = ActionAttempt()
                current_step.action_attempts.append(current_action_attempt)
                self.view_callbacks.new_action_attempts()

                selected_action = self._retrieve_action_from_repo(thought, failed_actions)
                current_action_attempt.action = selected_action
                self.view_callbacks.new_action(selected_action)

                action_arguments = self._extract_arguments(thought, retrieved_facts, selected_action)
                current_action_attempt.action_arguments = action_arguments
                self.view_callbacks.new_action_arguments(action_arguments)

                output = self._execute_action(selected_action, action_arguments)
                current_action_attempt.output = output
                self.view_callbacks.new_action_output(output)

                fact, was_successful = self._generate_fact(thought, output)
                current_action_attempt.fact = fact
                self.view_callbacks.new_fact(fact)
                current_action_attempt.was_successful = was_successful
                self.view_callbacks.new_was_successful(was_successful)

                if was_successful:
                    self._increase_action_value(selected_action)
                    break

                self._decrease_action_value(selected_action)

                failed_actions.append(selected_action)
                if len(failed_actions) >= self.arguments.action_attempts:
                    break

            self.summary, is_fulfilled = self._update_summary(self.arguments.task, self.summary, fact)
            current_step.summary = self.summary
            self.view_callbacks.new_summary(self.summary)

            current_step.is_fulfilled = is_fulfilled
            self.view_callbacks.new_is_fulfilled(is_fulfilled)

            self.save_state(self)

            if is_fulfilled:
                self.status = "finished"

            iteration += 1
