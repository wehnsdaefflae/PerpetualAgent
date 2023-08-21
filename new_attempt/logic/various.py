from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Fact:
    fact: str
    fact_id: str


@dataclass
class Action:
    action: str
    action_id: str


@dataclass
class AgentArguments:
    task:                   str

    read_facts_global:      bool
    read_actions_global:    bool
    write_facts_local:      bool
    write_actions_local:    bool

    confirm_actions:        bool

    llm_thought:            str
    llm_action:             str
    llm_parameter:          str
    llm_result:             str
    llm_fact:               str
    llm_summary:            str


ActionArguments = dict[str, any]


@dataclass
class Step:
    thought:            str
    action:             Action
    action_arguments:   ActionArguments
    result:             str
    fact:               Fact
