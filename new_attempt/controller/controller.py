from dataclasses import asdict

from new_attempt.agent import Agent, AgentArguments
from new_attempt.model.model import Model
from new_attempt.view.view import View, AgentRow, AgentView, StepView, FactView, ActionView


class Controller:
    def __init__(self) -> None:
        self.model = Model(
        )

        self.view = View(
            self.add_agent_to_model,
            self.get_agents_as_rows_from_model,
            self.get_agent_details_from_model,
            self.get_fact_from_model,
            self.get_action_from_model,
            self.get_local_facts,
            self.get_local_actions,
            self.get_global_facts,
            self.get_global_actions,
        )

    def get_local_facts(self, agent_id: str) -> list[FactView]:
        agent = self.model.agent_storage.get_agent(agent_id)
        local_fact_storage = agent.local_fact_storage
        return [FactView(fact, fact_id) for fact_id, fact in local_fact_storage.facts.items()]

    def get_local_actions(self, agent_id: str) -> list[ActionView]:
        agent = self.model.agent_storage.get_agent(agent_id)
        local_action_storage = agent.local_action_storage
        return [ActionView(action, action_id) for action_id, action in local_action_storage.actions.items()]

    def get_global_facts(self) -> list[FactView]:
        global_fact_storage = self.model.fact_storage   # or Agent.global_fact_storage
        return [FactView(fact, fact_id) for fact_id, fact in global_fact_storage.facts.items()]

    def get_global_actions(self) -> list[ActionView]:
        global_action_storage = self.model.action_storage   # or Agent.global_action_storage
        return [ActionView(action, action_id) for action_id, action in global_action_storage.actions.items()]

    def get_action_from_model(self, action_id: str) -> str:
        return self.model.action_storage.get_action(action_id)

    def get_fact_from_model(self, fact_id: str) -> str:
        return self.model.fact_storage.get_fact(fact_id)

    def get_agent_details_from_model(self, agent_id: str) -> AgentView:
        agent = self.model.agent_storage.get_agent(agent_id)
        steps_view = [StepView(**asdict(each_step)) for each_step in agent.past_steps]

        return AgentView(
            agent.agent_id,
            agent.arguments.task,
            agent.summary,
            agent.status,
            steps_view
        )

    def get_agents_as_rows_from_model(self) -> list[AgentRow]:
        agent_rows = [
            {"id": each_agent.agent_id, "task": each_agent.arguments.task, "status": each_agent.status}
            for each_agent in self.model.agent_storage.retrieve_agents()
        ]
        return agent_rows

    def add_agent_to_model(self, agent_setup: dict[str, any]) -> AgentRow:
        arguments = AgentArguments(**agent_setup)
        agent_id = "0"
        agent = Agent(agent_id, arguments)
        self.model.add_agent(agent)
        self.send_new_agent_to_view(agent)

        return {"id": agent.agent_id, "task": agent.arguments.task, "status": agent.status}

    def send_new_agent_to_view(self, agent: Agent) -> None:
        agent_row = {"id": agent.agent_id, "task": agent.arguments.task, "status": agent.status}
        self.view.add_agent_rows([agent_row])
