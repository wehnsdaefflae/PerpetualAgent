from __future__ import annotations

from typing import Callable

from new_attempt.model.agent.step_elements import Thought, Fact, Action, ActionArguments, ActionOutput, ActionWasSuccessful, Summary, IsFulfilled


class Callbacks:
    def __init__(self,
                 new_thought: Callable[[Thought], None],
                 new_relevant_facts: Callable[[list[Fact]], None],

                 new_action_attempts: Callable[[], None],
                 new_action: Callable[[Action], None],
                 new_action_arguments: Callable[[ActionArguments], None],
                 new_action_output: Callable[[ActionOutput], None],
                 new_fact: Callable[[Fact], None],
                 new_was_successful: Callable[[ActionWasSuccessful], None],
                 new_summary: Callable[[Summary], None],
                 new_is_fulfilled: Callable[[IsFulfilled], None],

                 update_view: Callable[[], None]) -> None:

        self._new_thought = new_thought
        self._new_relevant_facts = new_relevant_facts
        self._new_action_attempts = new_action_attempts
        self._new_action = new_action
        self._new_action_arguments = new_action_arguments
        self._new_action_output = new_action_output
        self._new_fact = new_fact
        self._new_was_successful = new_was_successful
        self._new_summary = new_summary
        self._new_is_fulfilled = new_is_fulfilled
        self._update_view = update_view

    def new_thought(self, thought: Thought) -> None:
        self._new_thought(thought)

    def new_relevant_facts(self, relevant_facts: list[Fact]) -> None:
        self._new_relevant_facts(relevant_facts)

    def new_action_attempts(self) -> None:
        self._new_action_attempts()

    def new_action(self, action: Action) -> None:
        self._new_action(action)

    def new_action_arguments(self, action_arguments: ActionArguments) -> None:
        self._new_action_arguments(action_arguments)

    def new_action_output(self, action_output: ActionOutput) -> None:
        self._new_action_output(action_output)

    def new_fact(self, fact: Fact) -> None:
        self._new_fact(fact)

    def new_was_successful(self, was_successful: ActionWasSuccessful) -> None:
        self._new_was_successful(was_successful)

    def new_summary(self, summary: Summary) -> None:
        self._new_summary(summary)

    def new_is_fulfilled(self, is_fulfilled: IsFulfilled) -> None:
        self._new_is_fulfilled(is_fulfilled)

    def update_view(self) -> None:
        self._update_view()

