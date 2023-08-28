from new_attempt.logic.classes import AgentArguments
from new_attempt.logic.agent import Agent, ModelCallbacks as AgentCallsModel, ViewCallbacks as AgentCallsView
from new_attempt.model.model import Model
from new_attempt.view.view import View, ViewCallbacks as ViewCallsRest


class Controller:
    def __init__(self) -> None:
        self.model = Model()

        self.agent_model_callbacks = AgentCallsModel(
            self.model.action_storage.update_elements,
            self.model.fact_storage.update_elements,
            self.model.fact_storage.get_elements,
            self.model.action_storage.get_elements,
            self.model.fact_storage.store_contents,
            self.model.action_storage.store_contents
        )

        view_callbacks = ViewCallsRest(
            self.send_new_agent_to_model,
            self.receive_agents,
            self.model.fact_storage.get_elements,
            self.model.action_storage.get_elements,
            self.pause_agent,
            self.start_agent,
            self.delete_agent,
        )

        self.view = View(view_callbacks)

        self.agent_view_callbacks = AgentCallsView(
            self.view.update_thought,
            self.view.update_relevant_facts,
            self.view.update_action_attempt,
            self.view.update_action,
            self.view.update_action_arguments,
            self.view.update_action_output,
            self.view.update_fact,
            self.view.update_action_is_successful,
            self.view.update_summary,
            self.view.update_is_fulfilled,

            self.view.fill_main
        )

        self.agents = set()

    def pause_agent(self, agent: Agent) -> None:
        agent.stopped = True

    def start_agent(self, agent: Agent) -> None:
        agent.stopped = False
        agent.start()
        agent.join()

    def delete_agent(self, agent: Agent) -> None:
        self.pause_agent(agent)
        self.model.agent_storage.remove_agent(agent.agent_id)

    def receive_agents(self, ids: list[str] | None = None, paused: bool = True) -> list[Agent]:
        if ids is None:
            agents = self.model.agent_storage.retrieve_agents()
        else:
            agents = [self.model.agent_storage.get_agent(agent_id) for agent_id in ids]

        for each_agent in agents:
            self.agents.add(each_agent)
            each_agent.connect_model_callbacks(self.agent_model_callbacks)
            each_agent.connect_view_callbacks(self.agent_view_callbacks)

        if paused:
            for each_agent in agents:
                each_agent.status = "paused"

        return agents

    def send_new_agent_to_model(self, arguments: AgentArguments) -> Agent:
        agent_id = self.model.agent_storage.next_agent_id()
        agent = Agent(agent_id, arguments, self.model.fact_storage, self.model.action_storage)
        agent.connect_model_callbacks(self.agent_model_callbacks)
        agent.connect_view_callbacks(self.agent_view_callbacks)

        self.agents.add(agent)
        self.model.agent_storage.add_agent(agent)
        return agent

    def send_new_agent_to_view(self, agent: Agent) -> None:
        self.view.add_agents([agent])
