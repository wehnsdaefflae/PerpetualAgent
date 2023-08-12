class FactsStorage:
    def __init__(self):
        self._facts = []

    def retrieve_fact(self, thought: str) -> str:
        """Simulated retrieval based on thought. You can implement a more detailed retrieval method."""
        for fact in self._facts:
            if thought in fact:
                return fact
        return ""

    def add_fact(self, fact: str):
        self._facts.append(fact)


class ActionsStorage:
    def __init__(self):
        self._actions = []

    def retrieve_action(self, thought: str) -> str:
        """Simulated retrieval based on thought. You can implement a more detailed retrieval method."""
        for action in self._actions:
            if thought in action:
                return action
        return ""

    def add_action(self, action: str):
        self._actions.append(action)


def system_inference(user_input: str, summary: str) -> str:
    pass


def retrieve_action_from_repo(thought: str, actions_storage: ActionsStorage) -> str:
    return actions_storage.retrieve_action(thought)


def retrieve_facts_from_memory(thought: str, facts_storage: FactsStorage) -> str:
    return facts_storage.retrieve_fact(thought)


def extract_parameters(thought: str, retrieved_facts: str, selected_action: str) -> str:
    pass


def execute_action(selected_action: str, action_params: str) -> str:
    pass


def generate_fact(result: str, thought: str) -> str:
    pass


def update_initiate_summary(new_fact: str, previous_summary: str) -> str:
    pass


def check_request_fulfilled(summary: str) -> str:
    pass


def main():
    # Initial data
    user_input = "Your request here"
    summary = ""

    # Instantiate storage
    facts_storage = FactsStorage()
    actions_storage = ActionsStorage()

    while True:
        thought = system_inference(user_input, summary)
        selected_action = retrieve_action_from_repo(thought, actions_storage)
        retrieved_facts = retrieve_facts_from_memory(thought, facts_storage)
        action_params = extract_parameters(thought, retrieved_facts, selected_action)
        result = execute_action(selected_action, action_params)
        new_fact = generate_fact(result, thought)
        facts_storage.add_fact(new_fact)
        summary = update_initiate_summary(new_fact, summary)
        request_status = check_request_fulfilled(summary)

        if request_status == "Fulfilled":
            break


if __name__ == "__main__":
    # https://chat.openai.com/share/4dcf41b8-436c-48d7-b909-fa3c7b6d82f4
    main()
