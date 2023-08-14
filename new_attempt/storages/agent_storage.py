from new_attempt.agent import Agent, AgentArguments


class AgentStorage:
    def __init__(self) -> None:
        self._agents = {
            "0": Agent("0", AgentArguments(
                request="I want to buy a car",
                facts_global=(True, True),
                actions_global=(True, True),
                facts_local=False,
                actions_local=False,
                confirm_actions=False,
                llm_thought="chatgpt-3.5-turbo",
                llm_action="chatgpt-3.5-turbo",
                llm_parameter="chatgpt-3.5-turbo",
                llm_result="chatgpt-3.5-turbo",
                llm_fact="chatgpt-3.5-turbo",
                llm_summary="chatgpt-3.5-turbo",
            )),
            "1": Agent("1", AgentArguments(
                request="Find philosophical books",
                facts_global=(True, True),
                actions_global=(True, True),
                facts_local=False,
                actions_local=False,
                confirm_actions=False,
                llm_thought="chatgpt-3.5-turbo",
                llm_action="chatgpt-3.5-turbo",
                llm_parameter="chatgpt-3.5-turbo",
                llm_result="chatgpt-3.5-turbo",
                llm_fact="chatgpt-3.5-turbo",
                llm_summary="chatgpt-3.5-turbo",
            )),
        }

    def retrieve_agents(self) -> list[Agent]:
        return sorted(self._agents.values(), key=lambda agent: agent.agent_id)

    def retrieve_agent(self, agent_id: str) -> Agent:
        return self._agents[agent_id]

    def add_agent(self, agent_arguments: AgentArguments) -> Agent:
        agent_id = f"{len(self._agents)}"
        agent = Agent(agent_id, agent_arguments)
        self._agents[agent_id] = agent
        return agent

    def remove_agent(self, agent_id: str) -> None:
        self._agents.pop(agent_id)

