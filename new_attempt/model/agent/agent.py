from __future__ import annotations

import enum
import random
import threading
import time
from dataclasses import asdict, dataclass

from new_attempt.model.agent.callbacks import Callbacks
from new_attempt.model.agent.step_elements import Thought, Fact, Action, ActionArguments, ActionOutput, ActionWasSuccessful, Summary, IsFulfilled, ActionAttempt, Step
from new_attempt.model.storages.vector_storage.storage import VectorStorage


@dataclass
class AgentArguments:
    task:                   str

    read_facts_global:      bool
    read_actions_global:    bool
    write_facts_local:      bool
    write_actions_local:    bool

    confirm_actions:        bool
    action_attempts:        int

    llm_thought:            str
    llm_action:             str
    llm_parameter:          str
    llm_result:             str
    llm_fact:               str
    llm_summary:            str


class Status(enum.StrEnum):
    FINISHED = "finished"
    PENDING = "pending"
    WORKING = "working"
    PAUSED = "paused"


class Agent(threading.Thread):
    @staticmethod
    def from_dict(agent_dict: dict[str, any], fact_storage: VectorStorage[Fact], action_storage: VectorStorage[Action], callbacks: Callbacks) -> Agent:

        arguments = agent_dict.pop("arguments")
        agent_arguments = AgentArguments(**arguments)

        history = agent_dict.pop("history")

        return Agent(
            agent_dict["agent_id"], agent_arguments,
            fact_storage, action_storage, callbacks,
            _status=Status(agent_dict["status"]),
            _summary=agent_dict["summary"],
            _history=[Step.from_dict(each_step) for each_step in history] if history is not None else None,
        )

    def __init__(self,
                 agent_id: str, arguments: AgentArguments,
                 fact_storage: VectorStorage[Fact], action_storage: VectorStorage[Action], callbacks: Callbacks,
                 _status: Status = Status.PAUSED, _summary: str = "", _history: list[Step] | None = None) -> None:

        if callbacks is None:
            raise ValueError("Agent callbacks not set.")

        self.agent_id = agent_id  # must be here for hash required in Thread.__init__
        super().__init__()
        self.arguments = arguments

        self.fact_storage = fact_storage
        self.action_storage = action_storage

        self.status = _status
        self.summary = _summary

        self.history = _history or list[Step]()
        self.working_on = Thought

        self.callbacks = callbacks

        self.save_state = None

        self.iterations = 0

    def __hash__(self) -> int:
        return hash(self.agent_id)

    def to_dict(self) -> dict[str, any]:
        return {
            "agent_id": self.agent_id,
            "arguments": asdict(self.arguments),
            "status": self.status.value,
            "summary": self.summary,
            "history": [each_step.to_dict() for each_step in self.history],
        }

    def _infer(self, user_input: str, summary: str) -> Thought:
        time.sleep(2)

        return Thought(f"thought {self.iterations}")

    def _retrieve_action_from_repo(self, thought: str, exclude: list[Action] | None = None) -> Action:
        time.sleep(2)

        action, = self.action_storage.store_contents([f"action for {thought}"], self.agent_id)
        return action

    def _retrieve_facts_from_memory(self, thought: str) -> list[Fact]:
        time.sleep(2)

        all_global_facts = self.fact_storage.get_elements()
        all_local_facts = self.fact_storage.get_elements(ids=None, local_agent_id=self.agent_id)
        selected_global = random.sample(all_global_facts, k=min(3, len(all_global_facts)))
        selected_local = random.sample(all_local_facts, k=min(2, len(all_local_facts)))
        total = selected_local + selected_global
        now = time.time()
        for each_fact in total:
            each_fact.retrieved = now
        self.fact_storage.update_elements(total)
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
        fact, = self.fact_storage.store_contents([fact_content], self.agent_id)
        return fact, ActionWasSuccessful(random.choice([True, False]))

    def _update_summary(self, request: str, previous_summary: str, fact: Fact) -> tuple[Summary, IsFulfilled]:
        time.sleep(2)

        return Summary(f"summary including {fact.storage_id}"), IsFulfilled(random.random() < .1)

    def _increase_action_value(self, action: Action) -> None:
        action.success += 1
        self.action_storage.update_elements([action])

    def _decrease_action_value(self, action: Action) -> None:
        action.failure += 1
        self.action_storage.update_elements([action])

    def run(self) -> None:
        if self.callbacks is None:
            raise ValueError("View callbacks not connected")

        iteration = 0

        while self.status == "working":
            current_step = Step()
            self.history.append(current_step)

            thought = self._infer(self.arguments.task, self.summary)
            current_step.thought = thought
            self.callbacks.new_thought(thought)

            retrieved_facts = self._retrieve_facts_from_memory(thought)
            current_step.relevant_facts = retrieved_facts
            self.callbacks.new_relevant_facts(retrieved_facts)

            failed_actions = list()
            while True:
                current_action_attempt = ActionAttempt()
                current_step.action_attempts.append(current_action_attempt)
                self.callbacks.new_action_attempts()

                selected_action = self._retrieve_action_from_repo(thought, failed_actions)
                current_action_attempt.action = selected_action
                self.callbacks.new_action(selected_action)

                action_arguments = self._extract_arguments(thought, retrieved_facts, selected_action)
                current_action_attempt.action_arguments = action_arguments
                self.callbacks.new_action_arguments(action_arguments)

                output = self._execute_action(selected_action, action_arguments)
                current_action_attempt.output = output
                self.callbacks.new_action_output(output)

                fact, was_successful = self._generate_fact(thought, output)
                current_action_attempt.fact = fact
                self.callbacks.new_fact(fact)
                current_action_attempt.was_successful = was_successful
                self.callbacks.new_was_successful(was_successful)

                if was_successful:
                    self._increase_action_value(selected_action)
                    break

                self._decrease_action_value(selected_action)

                failed_actions.append(selected_action)
                if len(failed_actions) >= self.arguments.action_attempts:
                    break

            self.summary, is_fulfilled = self._update_summary(self.arguments.task, self.summary, fact)
            current_step.summary = self.summary
            self.callbacks.new_summary(self.summary)

            current_step.is_fulfilled = is_fulfilled
            self.callbacks.new_is_fulfilled(is_fulfilled)

            self.save_state(self)

            if is_fulfilled:
                self.status = "finished"

            iteration += 1
