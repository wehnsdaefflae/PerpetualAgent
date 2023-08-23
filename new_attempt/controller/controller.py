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
            self.pause_agent,
            self.delete_agent,
        )

        self.running_agents = dict()

    def pause_agent(self, agent: Agent) -> None:
        agent.stopped = True
        self.running_agents.pop(agent.agent_id, None)

    def start_agent(self, agent: Agent) -> None:
        agent.stopped = False
        agent.join()
        self.running_agents[agent.agent_id] = agent

    def delete_agent(self, agent: Agent) -> None:
        self.pause_agent(agent)
        self.model.agent_storage.remove_agent(agent.agent_id)

    def receive_facts(self, fact_ids: list[str] | None = None, local_agent_id: str | None = None) -> list[Fact]:
        local_facts = self.model.fact_storage.get_elements(ids=fact_ids, local_agent_id=local_agent_id)
        return local_facts

    def receive_actions(self, fact_ids: list[str] | None = None, local_agent_id: str | None = None) -> list[Action]:
        local_actions = self.model.action_storage.get_elements(ids=fact_ids, local_agent_id=local_agent_id)
        return local_actions

    def receive_agents(self, ids: list[str] | None = None, paused: bool = True) -> list[Agent]:
        if ids is None:
            agents = self.model.agent_storage.retrieve_agents()
        else:
            agents = [self.model.agent_storage.get_agent(agent_id) for agent_id in ids]

        if paused:
            for each_agent in agents:
                each_agent.status = "paused"

        return agents

    def send_new_agent(self, arguments: AgentArguments) -> Agent:
        agent_id = self.model.agent_storage.next_agent_id()
        agent = Agent(agent_id, arguments, self.model.fact_storage, self.model.action_storage)
        self.model.agent_storage.add_agent(agent)
        return agent

    def send_new_agent_to_view(self, agent: Agent) -> None:
        self.view.add_agents([agent])
