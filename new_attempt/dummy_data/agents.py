from new_attempt.agent import Step, AgentArguments, Agent

CAR_ARGUMENTS = AgentArguments(
    task="I want to buy a car",
    read_facts_global=True,
    read_actions_global=True,
    write_facts_local=False,
    write_actions_local=False,
    confirm_actions=False,
    llm_thought="chatgpt-3.5-turbo",
    llm_action="chatgpt-3.5-turbo",
    llm_parameter="chatgpt-3.5-turbo",
    llm_result="chatgpt-3.5-turbo",
    llm_fact="chatgpt-3.5-turbo",
    llm_summary="chatgpt-3.5-turbo",
)

CAR_STEPS = [
    Step(
        thought="I need to find a car.",
        action_id="0",
        arguments={"car": "BMW"},
        result="i8",
        fact_id="0",
    ),
    Step(
        thought="I need to find another car.",
        action_id="1",
        arguments={"car": "Mercedes"},
        result="S-Class",
        fact_id="1",
    )
]

CAR_AGENT = Agent("0", CAR_ARGUMENTS, _past_steps=CAR_STEPS)

BOOK_STEPS = [
    Step(
        thought="I need to find a book.",
        action_id="3",
        arguments={"book": "The Republic"},
        result="The Republic",
        fact_id="2",
    ),
    Step(
        thought="I need to find another book.",
        action_id="4",
        arguments={"book": "The Prince"},
        result="The Prince",
        fact_id="3",
    )
]
BOOK_ARGUMENTS = AgentArguments(
    task="Find philosophical books",
    read_facts_global=True,
    read_actions_global=True,
    write_facts_local=False,
    write_actions_local=False,
    confirm_actions=False,
    llm_thought="chatgpt-3.5-turbo",
    llm_action="chatgpt-3.5-turbo",
    llm_parameter="chatgpt-3.5-turbo",
    llm_result="chatgpt-3.5-turbo",
    llm_fact="chatgpt-3.5-turbo",
    llm_summary="chatgpt-3.5-turbo",
)
BOOK_AGENT = Agent("1", BOOK_ARGUMENTS, _past_steps=BOOK_STEPS)

AGENTS = {
    CAR_AGENT.agent_id: CAR_AGENT,
    BOOK_AGENT.agent_id: BOOK_AGENT,
}
