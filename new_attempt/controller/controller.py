from new_attempt.logic.agent import Agent
from new_attempt.logic.various import AgentArguments, Fact, Action
from new_attempt.model.model import Model
from new_attempt.view.view import View


class Controller:
    def __init__(self) -> None:
        self.model = Model(
            self.send_new_agent_to_view
        )

        self.view = View(
            self.send_new_agent,
            self.receive_agents,
            self.receive_facts,
            self.receive_actions,
        )

        self.no_agents_created = 0

        self.agents = dict()

    def receive_facts(self, fact_ids: list[str] | None = None, local_agent_id: str | None = None) -> list[Fact]:
        local_facts = self.model.fact_storage.get_elements(ids=fact_ids, local_agent_id=local_agent_id)
        return local_facts

    def receive_actions(self, fact_ids: list[str] | None = None, local_agent_id: str | None = None) -> list[Action]:
        local_actions = self.model.action_storage.get_elements(ids=fact_ids, local_agent_id=local_agent_id)
        return local_actions

    def receive_agents(self, ids: list[str] | None = None) -> list[Agent]:
        if ids is None:
            return self.model.agent_storage.retrieve_agents()
        return [self.model.agent_storage.get_agent(agent_id) for agent_id in ids]

    def send_new_agent(self, arguments: AgentArguments) -> None:
        agent_id = str(self.no_agents_created)
        self.no_agents_created += 1

        agent = Agent(agent_id, arguments, self.model.fact_storage, self.model.action_storage)

        self.agents[agent_id] = agent
        # todo: start agent thread

        self.model.agent_storage.add_agent(agent)

    def send_new_agent_to_view(self, agent: Agent) -> None:
        self.view.add_agents([agent])
