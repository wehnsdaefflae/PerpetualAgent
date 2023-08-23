from __future__ import annotations

import time
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Fact:
    fact: str
    element_id: str
    last_access: float = time.time()


@dataclass(frozen=True)
class Action:
    action: str
    element_id: str
    success: int = 0
    failure: int = 0


@dataclass
class AgentArguments:
    task:                   str

    read_facts_global:      bool
    read_actions_global:    bool
    write_facts_local:      bool
    write_actions_local:    bool

    confirm_actions:        bool
    action_attempts:         int

    llm_thought:            str
    llm_action:             str
    llm_parameter:          str
    llm_result:             str
    llm_fact:               str
    llm_summary:            str


ActionArguments = dict[str, any]


@dataclass
class Step:
    @staticmethod
    def from_dict(step_dict: dict[str, any]) -> Step:
        return Step(
            thought=step_dict["thought"],
            action=Action(**step_dict["action"]),
            relevant_facts={Fact(**fact_dict) for fact_dict in step_dict["relevant_facts"]},
            action_arguments=step_dict["action_arguments"],
            output=step_dict["output"],
            fact=Fact(**step_dict["fact"]),
            was_successful=step_dict["was_successful"],
            summary=step_dict["summary"],
        )

    thought:            str
    action:             Action
    relevant_facts:     set[Fact]
    action_arguments:   ActionArguments
    output:             str
    fact:               Fact
    was_successful:     bool
    summary:            str

    def to_dict(self) -> dict[str, any]:
        return {
            "thought":          self.thought,
            "action":           asdict(self.action),
            "relevant_facts":   [asdict(fact) for fact in self.relevant_facts],
            "action_arguments": self.action_arguments,
            "output":           self.output,
            "fact":             asdict(self.fact),
            "was_successful":   self.was_successful,
            "summary":          self.summary,
        }
