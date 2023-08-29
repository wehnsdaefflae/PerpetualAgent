from new_attempt.model.agent.callbacks import Callbacks as AgentCallbacks
from new_attempt.model.storages.vector_storage.callbacks import Callbacks as VectorCallsView
from new_attempt.model.storages.agent_storage.callbacks import Callbacks as AgentStorageCallsView
from new_attempt.model.model import Model
from new_attempt.view.view import View
from new_attempt.view.callbacks import ViewCallbacks as ViewCallsRest


class Controller:
    def __init__(self) -> None:
        self.model = Model()

        # process ui input
        view_callbacks = ViewCallsRest(
            self.model.agent_storage.create_agent,
            self.model.agent_storage.get_agents,
            self.model.fact_storage.get_elements,
            self.model.action_storage.get_elements,
            lambda agent: print(f"Pausing agent {agent.agent_id}"),
            lambda agent: print(f"Starting agent {agent.agent_id}"),
            lambda agent: print(f"Deleting agent {agent.agent_id}"),
        )
        self.view = View(view_callbacks)

        # update facts memory table
        fact_calls_view = VectorCallsView(
            self.view.upsert_facts,
            self.view.delete_facts
        )
        self.model.fact_storage.connect_callbacks(fact_calls_view)

        # update actions memory table
        action_calls_view = VectorCallsView(
            self.view.upsert_actions,
            self.view.delete_actions
        )
        self.model.action_storage.connect_callbacks(action_calls_view)

        # update agents table
        agent_storage_calls_view = AgentStorageCallsView(
            self.view.upsert_agent,
            self.view.remove_agent
        )
        self.model.agent_storage.connect_callbacks(agent_storage_calls_view)

        # update agent stream of consciousness
        agent_calls_view = AgentCallbacks(
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
        self.model.agent_storage.connect_agent_callbacks(agent_calls_view)
