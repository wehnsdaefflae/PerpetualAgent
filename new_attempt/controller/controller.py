from dataclasses import asdict

from new_attempt.agent import Agent, AgentArguments
from new_attempt.model.model import Model, AgentModel, StepModel
from new_attempt.model.storages.action_interface import ActionInterface
from new_attempt.model.storages.fact_interface import FactInterface
from new_attempt.view.view import View, AgentView, StepView, FactView, ActionView


class Controller:
    def __init__(self) -> None:
        self.model = Model(
            self.send_new_agent_to_view
        )

        self.view = View(
            self.add_agent_to_model,
            self.get_agents_from_model,
            self.get_agent_details_from_model,
            self.get_fact_from_model,
            self.get_action_from_model,
            self.get_local_facts,
            self.get_local_actions,
            self.get_global_facts,
            self.get_global_actions,
        )

        self.agents = dict()

    def get_local_facts(self, agent_id: str) -> list[FactView]:
        agent = self.model.agent_storage.get_agent(agent_id)
        local_fact_storage = agent.local_fact_storage
        return [FactView(fact, fact_id) for fact_id, fact in local_fact_storage.facts.items()]

    def get_local_actions(self, agent_id: str) -> list[ActionView]:
        agent = self.model.agent_storage.get_agent(agent_id)
        local_action_storage = agent.local_action_storage
        return [ActionView(action, action_id) for action_id, action in local_action_storage.actions.items()]

    def get_global_facts(self) -> list[FactView]:
        global_fact_storage = self.model.global_fact_storage   # or Agent.global_fact_storage
        return [FactView(fact, fact_id) for fact_id, fact in global_fact_storage.facts.items()]

    def get_global_actions(self) -> list[ActionView]:
        global_action_storage = self.model.global_action_storage   # or Agent.global_action_storage
        return [ActionView(action, action_id) for action_id, action in global_action_storage.actions.items()]

    def get_action_from_model(self, action_id: str) -> str:
        return self.model.global_action_storage.get_action(action_id)

    def get_fact_from_model(self, fact_id: str) -> str:
        return self.model.global_fact_storage.get_fact(fact_id)

    @staticmethod
    def _step_model_to_view(step_model: StepModel) -> StepView:
        return StepView(
            thought=step_model.thought,
            action_id=step_model.action_id,
            action_is_local=step_model.action_is_local,
            arguments=step_model.arguments,
            result=step_model.result,
            fact_id=step_model.fact_id,
            fact_is_local=step_model.fact_is_local,
        )

    @staticmethod
    def _agent_model_to_view(agent_model: AgentModel) -> AgentView:
        return AgentView(
            agent_id=agent_model.agent_id,
            task=agent_model.arguments.task,
            summary=agent_model.summary,
            status=agent_model.status,
            steps=[Controller._step_model_to_view(each_step) for each_step in agent_model.past_steps],
        )

    def get_agent_details_from_model(self, agent_id: str) -> AgentView:
        agent_dict = self.model.get_agent(agent_id)
        steps_view = [StepView(**asdict(each_step)) for each_step in agent_dict.past_steps]

        return AgentView(
            **agent_dict,
            steps=steps_view,
        )

    def get_agents_from_model(self) -> list[AgentView]:
        agents = [
            Controller._agent_model_to_view(each_agent)
            for each_agent in self.model.agent_interface.retrieve_agents()
        ]
        return agents

    def add_agent_to_model(self, arguments: AgentArguments) -> None:
        agent_id = self.model.get_next_agent_id()

        local_facts = self.model.create_local_facts_collection(agent_id)
        local_actions = self.model.create_local_actions_collection(agent_id)

        agent_view = AgentView(
            agent_id=agent_id,
            task=arguments.task,
            summary="",
            status="paused",
            steps=[],
        )

        agent = Agent(agent_id, arguments,
                      self.model.global_fact_interface,
                      self.model.global_action_interface,
                      FactInterface(local_facts),
                      ActionInterface(local_actions))

        self.agents[agent_id] = agent
        # todo: start agent thread

        self.model.agent_interface.add_agents([agent_view])

    def send_new_agent_to_view(self, agent_model: AgentModel) -> None:
        agent_view = Controller._agent_model_to_view(agent_model)
        self.view.add_agents([agent_view])
