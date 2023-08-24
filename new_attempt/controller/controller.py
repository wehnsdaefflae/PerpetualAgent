from new_attempt.controller.classes import AgentArguments
from new_attempt.logic.agent import Agent
from new_attempt.model.model import Model
from new_attempt.view.view import View, ViewCallbacks


class Controller:
    def __init__(self) -> None:
        self.model = Model()

        view_callbacks = ViewCallbacks(
            self.send_new_agent_to_model,
            self.receive_agents,
            self.model.fact_storage.get_elements,
            self.model.action_storage.get_elements,
            self.pause_agent,
            self.start_agent,
            self.delete_agent,
        )
        self.view = View(view_callbacks)

        self.running_agents = dict()

    def connect_agent(self, agent: Agent) -> None:
        agent.connect_model(self.model.agent_storage.add_agent)
        agent.connect_view(self.view.update_details)

    def pause_agent(self, agent: Agent) -> None:
        agent.stopped = True
        self.running_agents.pop(agent.agent_id, None)

    def start_agent(self, agent: Agent) -> None:
        agent.stopped = False
        agent.start()
        agent.join()
        self.running_agents[agent.agent_id] = agent

    def delete_agent(self, agent: Agent) -> None:
        self.pause_agent(agent)
        self.model.agent_storage.remove_agent(agent.agent_id)

    def receive_agents(self, ids: list[str] | None = None, paused: bool = True) -> list[Agent]:
        if ids is None:
            agents = self.model.agent_storage.retrieve_agents()
        else:
            agents = [self.model.agent_storage.get_agent(agent_id) for agent_id in ids]

        for each_agent in agents:
            self.connect_agent(each_agent)

        if paused:
            for each_agent in agents:
                each_agent.status = "paused"

        return agents

    def send_new_agent_to_model(self, arguments: AgentArguments) -> Agent:
        agent_id = self.model.agent_storage.next_agent_id()
        agent = Agent(
            agent_id, arguments, self.model.fact_storage, self.model.action_storage
        )
        self.connect_agent(agent)
        self.model.agent_storage.add_agent(agent)
        return agent

    def send_new_agent_to_view(self, agent: Agent) -> None:
        self.view.add_agents([agent])
