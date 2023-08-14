from new_attempt.agent import Agent, AgentArguments
from new_attempt.model import Model
from new_attempt.view import View, AgentRow, AgentDetails


class Controller:
    def __init__(self) -> None:
        self.model = Model(
            self.send_new_agent_to_view
        )

        self.view = View(
            self.add_agent_to_model,
            self.get_agents_as_rows_from_model,
            self.get_agent_details_from_model
        )

    def get_agent_details_from_model(self, agent_id: str) -> AgentDetails:
        agent = self.model.agent_storage.retrieve_agent(agent_id)
        return AgentDetails(
            agent.agent_id,
            agent.arguments.task,
            agent.summary,
            agent.status,
            agent.past_steps
        )

    def get_agents_as_rows_from_model(self) -> list[AgentRow]:
        agent_rows = [
            {"id": each_agent.agent_id, "task": each_agent.arguments.task, "status": each_agent.status}
            for each_agent in self.model.agent_storage.retrieve_agents()
        ]
        return agent_rows

    def add_agent_to_model(self, agent_setup: dict[str, any]) -> AgentRow:
        arguments = AgentArguments(**agent_setup)
        agent = self.model.new_agent(arguments)
        return {"id": agent.agent_id, "task": agent.arguments.task, "status": agent.status}

    def send_new_agent_to_view(self, agent: Agent) -> None:
        agent_row = {"id": agent.agent_id, "task": agent.arguments.task, "status": agent.status}
        self.view.add_agent_rows([agent_row])
