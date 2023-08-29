from __future__ import annotations

from typing import Callable

from new_attempt.model.agent.agent import Agent


class Callbacks:
    def __init__(self,
                 upsert_agent: Callable[[Agent], None],
                 remove_agent: Callable[[Agent], None]) -> None:

        self._upsert_agent = upsert_agent
        self._remove_agent = remove_agent

    def upsert_agent(self, agent: Agent) -> None:
        self._upsert_agent(agent)

    def remove_agent(self, agent: Agent) -> None:
        self._remove_agent(agent)
