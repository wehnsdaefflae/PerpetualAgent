# coding=utf-8
import json
from typing import Callable

import nicegui
from nicegui.elements.button import Button
from nicegui.elements.dialog import Dialog
from nicegui.elements.table import Table

from new_attempt.model.agent.agent import Agent, AgentArguments
from new_attempt.model.agent.step_elements import Fact, Action, IsFulfilled, ActionOutput, ActionArguments, ActionWasSuccessful, Summary, Thought
from new_attempt.model.storages.vector_storage.element import ContentElement, CONTENT_ELEMENT
from new_attempt.view.callbacks import ViewCallbacks


class View:
    def __init__(self, view_callbacks: ViewCallbacks) -> None:

        # content
        self.local_facts_table = None
        self.local_actions_table = None
        self.global_facts_table = None
        self.global_actions_table = None
        self.agents_table = None
        self.toggle_all_button = None
        self.pause_button = None

        self.current_thought_expansion = None
        self.current_action_attempt = None
        self.waiting_label = None

        self.stream = None

        self.selected_fact_ids = list[dict[str, any]]()
        self.selected_action_ids = list[dict[str, any]]()

        # layout
        self.header = None
        self.left_drawer = None
        self.right_drawer = None
        self.main_section = None
        self.footer = None

        # callbacks
        self.view_callbacks = view_callbacks

        # start
        self.run()

    def _agent_to_row(self, agent: Agent) -> dict[str, any]:
        return {
            "agent_id": agent.agent_id,
            "task": agent.arguments.task,
            "status": agent.status,
        }

    def add_agents(self, agent_views: list[Agent]) -> None:
        new_rows = [self._agent_to_row(each_agent) for each_agent in agent_views]
        self.agents_table.add_rows(*new_rows)

    def modify_page(self) -> None:
        nicegui.ui.query('#c0').classes("h-screen")
        nicegui.ui.query('#c1').classes("h-full")
        nicegui.ui.query('#c2').classes("h-full")
        nicegui.ui.query('#c3').classes("h-full")

    def setup_sections(self) -> None:
        self.header = nicegui.ui.header(elevated=True)
        self.header.classes('items-center justify-between')

        self.main_section = nicegui.ui.row()
        self.main_section.classes("flex flex-col h-full w-full")

        self.left_drawer = nicegui.ui.left_drawer(top_corner=False, bottom_corner=False)
        self.left_drawer.style('background-color: #d7e3f4')
        self.left_drawer.classes("flex flex-col h-full")

        self.right_drawer = nicegui.ui.right_drawer(top_corner=False, bottom_corner=False, value=False)
        self.right_drawer.style('background-color: #ebf1fa')
        self.right_drawer.props(":width=\"500\"")
        self.right_drawer.classes("flex flex-col h-full")

        self.footer = nicegui.ui.footer()
        # debug
        with self.footer:
            nicegui.ui.button("debug", on_click=self._debug_pause)

    def _debug_pause(self) -> None:
        print("breakpoint here")

    def run(self) -> None:
        self.modify_page()

        self.setup_sections()

        self.fill_header()
        self.fill_left_drawer()
        self.fill_main()
        self.fill_right_drawer()
        self.fill_footer()

        nicegui.ui.run()

    def fill_header(self) -> None:
        self.header.clear()
        with self.header:
            nicegui.ui.button(text="agents", on_click=lambda: self.left_drawer.toggle(), icon='arrow_left')
            main_heading = nicegui.ui.label("Details")
            main_heading.style('font-size: 20px')
            nicegui.ui.button(text="memory", on_click=lambda: self.right_drawer.toggle(), icon='arrow_right')

    def fill_left_drawer(self) -> None:
        self.left_drawer.clear()
        with self.left_drawer:
            columns = [
                {"name": "agent_id", "label": "ID", "field": "agent_id", "required": True, "align": "left", "type": "text"},
                {"name": "status", "label": "Status", "field": "status", "required": True, "align": "left", "type": "text"},
                {"name": "task", "label": "Task", "field": "task", "required": True, "align": "left", "type": "text"},
            ]
            with nicegui.ui.scroll_area() as scroll_area:
                scroll_area.classes("flex-1")
                self.agents_table = nicegui.ui.table(columns=columns, rows=list(), row_key="agent_id", selection="single", on_select=self.agent_changed)
                self._update_agents_table(initialize_paused=True)

            nicegui.ui.separator().classes("my-5")
            with nicegui.ui.row() as row:
                row.classes("justify-around full-width flex-none")
                nicegui.ui.button("New task", on_click=self._setup_agent_dialog)
                self.toggle_all_button = nicegui.ui.button("Pause all", on_click=self.toggle_pause_all)

    def _update_agents_table(self, initialize_paused: bool = False) -> None:
        self.agents_table.rows.clear()
        rows = [self._agent_to_row(each_agent) for each_agent in self.view_callbacks.get_agents()]
        self.agents_table.add_rows(*rows)

    def toggle_pause_all(self) -> None:
        agents = self.view_callbacks.get_agents(agent_ids=[each_agent_row["agent_id"] for each_agent_row in self.agents_table.rows])
        if self.toggle_all_button.text == "Pause all":
            for each_agent in agents:
                if each_agent.status == "working":
                    self.view_callbacks.pause_agent(each_agent)

            self._update_agents_table(initialize_paused=False)
            self.toggle_all_button.text = "Resume all"

        elif self.toggle_all_button.text == "Resume all":
            for each_agent in agents:
                if each_agent.status == "paused":
                    self.view_callbacks.start_agent(each_agent)

            self._update_agents_table(initialize_paused=False)
            self.toggle_all_button.text = "Pause all"
            self.agents_table.update()

    def fill_footer(self) -> None:
        with self.footer:
            nicegui.ui.label("Status updates from agents, incl. agent number")

    def switched_memory_tab(self) -> None:
        print("switched tab")

    def fill_right_drawer(self) -> None:
        self.right_drawer.clear()
        agent_id = self.get_selected_agent_id()

        with self.right_drawer:
            with nicegui.ui.tabs(on_change=self.switched_memory_tab) as tabs:
                if agent_id is not None:
                    local_memory = nicegui.ui.tab("local", f"Local (#{agent_id})")

                global_memory = nicegui.ui.tab("global", "Global")

            with nicegui.ui.tab_panels(tabs, value=global_memory if agent_id is None else local_memory) as tab_panels:
                tab_panels.classes("flex-1")

                if agent_id is None:
                    self.local_actions_table, self.local_facts_table = None, None

                else:
                    with nicegui.ui.tab_panel(local_memory):
                        self.local_actions_table, self.local_facts_table = self.memory_tables(agent_id, True)

                with nicegui.ui.tab_panel(global_memory):
                    self.global_actions_table, self.global_facts_table = self.memory_tables(agent_id, False)

    def get_selected_agent_id(self) -> str | None:
        if len(self.agents_table.selected) < 1:
            return None

        selected, = self.agents_table.selected
        agent_id = selected["agent_id"]
        return agent_id

    def fill_main(self) -> None:
        self.main_section.clear()

        agent_id = self.get_selected_agent_id()
        with self.main_section:
            if agent_id is None:
                message = nicegui.ui.label("no agent selected")
                message.classes("text-2xl flex-none")
                return

            agent, = self.view_callbacks.get_agents(agent_ids=[agent_id])

            label_task = nicegui.ui.label(agent.arguments.task)
            label_task.classes("text-2xl flex-none")

            label_progress = nicegui.ui.label(f"{agent.summary} [This is the progress report.]")
            label_progress.classes("flex-none")

            with nicegui.ui.scroll_area() as scroll_area:
                # scroll_area.style('background-color: #f0f4fa')
                scroll_area.classes("flex-1")

                with nicegui.ui.column() as self.stream:
                    self.stream.classes("flex flex-col full-width")

            with nicegui.ui.row().classes('justify-around flex-none full-width'):
                self.pause_button = nicegui.ui.button("Resume" if agent.status == "paused" else "Pause", on_click=lambda: self.pause_from_details(agent))
                if agent.status in ("finished", "pending"):
                    self.pause_button.disable()
                nicegui.ui.button("Delete", on_click=lambda: self._confirm_deletion_dialog(agent), color="negative")

        if self.stream is None:
            raise Exception("stream is None")

        self.stream_of_consciousness()

    def update_thought(self, thought: Thought) -> None:
        with self.main_section:
            if self.current_thought_expansion is None:
                raise Exception("current_thought_expansion is None")
            self.current_thought_expansion.text = thought

    def update_relevant_facts(self, relevant_facts: list[Fact]) -> None:
        pass

    def update_action_attempt(self) -> None:
        pass

    def update_action(self, action: Action) -> None:
        # create new action attempt
        pass

    def update_action_arguments(self, action_arguments: ActionArguments) -> None:
        pass

    def update_action_output(self, action_output: ActionOutput) -> None:
        pass

    def update_fact(self, resulting_fact: Fact) -> None:
        pass

    def update_action_is_successful(self, is_successful: ActionWasSuccessful) -> None:
        pass

    def update_summary(self, summary: Summary) -> None:
        pass

    def update_is_fulfilled(self, is_fulfilled: IsFulfilled) -> None:
        pass

    def stream_of_consciousness(self) -> None:

        # agent, = self.view_callbacks.receive_agents([agent_id], False)

        # if any is none, stop parsing. set pending_message = "thinking about {key}", else set None
        steps = [
            {
                "thought": "Thought 2",  # can be none
                "relevant_facts": [  # can be none
                    "fact 1",
                    "fact 2",
                    "fact 3",
                ],
                "action_attempts": [
                    {
                        "action_name": "action 1",              # can be none
                        "action_arguments": json.dumps({    # can be none
                            "argument 1": "value 1",
                            "argument 2": "value 2",
                        }, indent=4),
                        "action_output": json.dumps({       # can be none
                            "output": "each_output",
                        }, indent=4),
                        "resulting_fact": "resulting fact",     # can be none
                        "is_successful": True,                  # can be none
                    },
                ],
                "is_successful": True,                              # can be none
                "summary": "Summary"                                # can be none
            },
            {
                "thought": "Thought 1",
                "relevant_facts": [
                    "fact 1",
                    "fact 2",
                    "fact 3",
                ],
                "action_attempts": [
                    {
                        "action_name": "action 1",
                        "action_arguments": json.dumps({
                            "argument 1": "value 1",
                            "argument 2": "value 2",
                        }, indent=4),
                        "action_output": json.dumps({
                            "output": "each_output",
                        }, indent=4),
                        "resulting_fact": "resulting fact",
                        "is_successful": False,
                    },
                    {
                        "action_name": "action 1",
                        "action_arguments": json.dumps({
                            "argument 1": "value 1",
                            "argument 2": "value 2",
                        }, indent=4),
                        "action_output": json.dumps({
                            "output": "each_output",
                        }, indent=4),
                        "resulting_fact": "resulting fact",
                        "is_successful": False,
                    },
                ],
                "is_successful": False,
                "summary": "Summary"
            },
        ]

        with self.stream:
            for each_step in steps:
                self.add_thought(each_step)

        self.current_thought_expansion = None
        self.waiting_label = None

    def add_relevant_facts(self, relevant_facts: list[Fact]) -> bool:
        with nicegui.ui.expansion(text="relevant facts") as fact_expansion:
            fact_expansion.classes("full-width pl-8 bg-blue-300")
            if relevant_facts is None:
                self.waiting_label = nicegui.ui.label("retrieving relevant facts...")
                return False

            for each_fact in relevant_facts:
                each_label = nicegui.ui.label(each_fact.content)
                each_label.classes("flex-1 m-3 p-3 rounded-lg")

        return True

    def add_action_attempt(self, action_attempt: dict[str, any]) -> bool:
        action_name = action_attempt.get("action_name")
        if action_name is None:
            self.waiting_label = nicegui.ui.label("deciding on action...")
            return False

        # extract each action attempt into method
        with nicegui.ui.expansion(text=f"attempt #{action_name}") as action_expansion:
            is_successful = action_attempt.get("is_successful")
            if is_successful is None:
                action_expansion.classes("full-width pl-8 bg-yellow-300")
            elif is_successful:
                action_expansion.classes("full-width pl-8 bg-green-300")
            else:
                action_expansion.classes("full-width pl-8 bg-red-300")

            # extract action arguments into method
            action_arguments = action_attempt.get("action_arguments")
            if action_arguments is None:
                self.waiting_label = nicegui.ui.label("extraction action parameters...")
                return False
            nicegui.ui.markdown(f"```json\n{action_arguments}\n```")

            # extract action output into method
            action_output = action_attempt.get("action_output")
            if action_output is None:
                self.waiting_label = nicegui.ui.label("executing action...")
                return False
            nicegui.ui.markdown(f"```json\n{action_output}\n```")

            # extract resulting fact into method
            resulting_fact = action_attempt.get("resulting_fact")
            if resulting_fact is None:
                self.waiting_label = nicegui.ui.label("composing fact...")
                return False
            each_label = nicegui.ui.label(resulting_fact)
            each_label.classes("flex-1 m-3 p-3 bg-blue-200 rounded-lg")

        return True

    def add_summary(self, summary: Summary | None) -> bool:
        if summary is None:
            self.waiting_label = nicegui.ui.label("summarizing...")
            return False

        each_label = nicegui.ui.label(summary)
        each_label.classes("flex-1 m-3 p-3 bg-white rounded-lg")
        return True

    def add_thought(self, each_step: dict[str, any]) -> bool:
        thought = each_step.get("thought")

        with nicegui.ui.expansion(text=thought) as self.current_thought_expansion:
            is_successful = each_step.get("is_successful")
            if is_successful is None:
                self.current_thought_expansion.classes("full-width bg-yellow-300 rounded-lg")
            elif is_successful:
                self.current_thought_expansion.classes("full-width bg-green-300 rounded-lg")
            else:
                self.current_thought_expansion.classes("full-width bg-red-300 rounded-lg")

            if not self.add_relevant_facts(each_step["relevant_facts"]):
                return False

            action_attempts = each_step.get("action_attempts")
            if action_attempts is None:
                self.waiting_label = nicegui.ui.label("attempting action...")
                return False

            for each_action_attempt in action_attempts:
                if not self.add_action_attempt(each_action_attempt):
                    return False

            summary = each_step.get("summary")
            if not self.add_summary(summary):
                return False

            return True

    def pause_from_details(self, agent: Agent) -> None:
        if agent.status == "working":
            self.view_callbacks.pause_agent(agent)
            self.pause_button.text = "Resume"

        elif agent.status == "paused":
            self.view_callbacks.start_agent(agent)
            self.pause_button.text = "Pause"

    async def _confirm_deletion_dialog(self, agent: Agent) -> None:
        with nicegui.ui.dialog() as dialog, nicegui.ui.card():
            nicegui.ui.label(f"Do you really want to do this to agent {agent.agent_id}?")

            with nicegui.ui.row().classes('justify-around flex-none full-width'):
                nicegui.ui.button("Abort", on_click=dialog.close)
                nicegui.ui.button("Delete", on_click=lambda: dialog.submit("delete"), color="negative")

        result = await dialog
        if result is None:
            return

        if result == "delete":
            self.view_callbacks.delete_agent(agent)
            self.agents_table.selected.clear()
            for each_row in self.agents_table.rows:
                if each_row["agent_id"] == agent.agent_id:
                    self.agents_table.remove_rows(each_row)
                    break

        self.agent_changed()

    def show_action(self, action_id: str, arguments: dict[str, any]) -> Dialog:
        action, = self.view_callbacks.get_actions(action_ids=[action_id])
        with nicegui.ui.dialog() as dialog, nicegui.ui.card():
            nicegui.ui.label(f"{action.action} (action #{action_id})")
            nicegui.ui.label(json.dumps(arguments, indent=4))
        return dialog

    def show_result(self, result: str) -> Dialog:
        with nicegui.ui.dialog() as dialog, nicegui.ui.card():
            nicegui.ui.label(result)

        return dialog

    def update_details(self, agent: Agent) -> None:
        selected_agent = self.get_selected_agent_id()
        if selected_agent != agent.agent_id:
            return
        self.agent_changed()

    def agent_changed(self) -> None:
        self.fill_main()
        self.fill_right_drawer()

    async def _setup_agent_dialog(self) -> None:
        llms = ["chatgpt-3.5-turbo", "gpt-4", "llama", "etc."]

        def enable_ok_button() -> None:
            if 0 < len(text_area.value):
                button_ok.enable()
            else:
                button_ok.disable()

        with nicegui.ui.dialog() as dialog, nicegui.ui.card():
            heading = nicegui.ui.label("Set up agent")
            heading.classes("text-xl")

            text_area = nicegui.ui.textarea(placeholder="Task", label="Enter the agent's task", on_change=enable_ok_button)
            text_area.classes("w-full")

            with nicegui.ui.row():
                with nicegui.ui.column():
                    read_facts_global = nicegui.ui.checkbox("Read global facts", value=True)
                    read_actions_global = nicegui.ui.checkbox("Read global actions", value=True)

                with nicegui.ui.column():
                    write_facts_local = nicegui.ui.checkbox("Write local facts", value=True)
                    write_actions_local = nicegui.ui.checkbox("Write local actions", value=True)

            with nicegui.ui.row():
                with nicegui.ui.column():
                    llm_thought = nicegui.ui.select(llms, label="Thought inference", value=llms[0])
                    llm_action = nicegui.ui.select(llms, label="Action generation", value=llms[0])
                    llm_parameter = nicegui.ui.select(llms, label="Parameter extraction", value=llms[0])

                with nicegui.ui.column():
                    llm_result = nicegui.ui.select(llms, label="Result naturalization", value=llms[0])
                    llm_fact = nicegui.ui.select(llms, label="Fact composition", value=llms[0])
                    llm_summary = nicegui.ui.select(llms, label="Progress summarization", value=llms[0])

            nicegui.ui.separator()

            confirm_actions = nicegui.ui.checkbox("Requires confirmation", value=True)
            action_attempts = nicegui.ui.number(value=3)

            with nicegui.ui.row().classes("justify-around full-width flex-none"):
                button_ok = nicegui.ui.button("OK", color="primary", on_click=lambda: dialog.submit("done"))
                button_ok.disable()
                nicegui.ui.button("Cancel", color="secondary", on_click=dialog.close)

        result = await dialog
        if result is None:
            return

        arguments = AgentArguments(
            task=text_area.value,
            read_facts_global=read_facts_global.value,
            read_actions_global=read_actions_global.value,
            write_facts_local=write_facts_local.value,
            write_actions_local=write_actions_local.value,
            confirm_actions=confirm_actions.value,
            action_attempts=action_attempts.value,
            llm_thought=llm_thought.value,
            llm_action=llm_action.value,
            llm_parameter=llm_parameter.value,
            llm_result=llm_result.value,
            llm_fact=llm_fact.value,
            llm_summary=llm_summary.value,
        )

        agent = self.view_callbacks.create_agent(arguments)
        self._update_agents_table(initialize_paused=False)
        self.select_agent(agent.agent_id)

    def update_memory_buttons(self, buttons: list[Button], enable: bool) -> None:
        if enable:
            for each_button in buttons:
                each_button.enable()
        else:

            for each_button in buttons:
                each_button.disable()

    def select_agent(self, agent_id: str) -> None:
        self.agents_table.selected.clear()
        for each_row in self.agents_table.rows:
            if each_row["agent_id"] == agent_id:
                self.agents_table.selected.append(each_row)
                self.agent_changed()
                break

    def update_selected_actions(self, selected_action_rows: list[dict[str, any]], buttons: list[Button]) -> None:
        self.selected_action_ids.clear()
        for each_action in selected_action_rows:
            self.selected_action_ids.append(each_action["id"])
        self.update_memory_buttons(buttons, 0 < len(selected_action_rows))

    def update_selected_facts(self, selected_fact_rows: list[dict[str, any]], buttons: list[Button | None]) -> None:
        self.selected_fact_ids.clear()
        for each_fact in selected_fact_rows:
            self.selected_fact_ids.append(each_fact["id"])
        self.update_memory_buttons([each_button for each_button in buttons if each_button is not None], 0 < len(selected_fact_rows))

    def _action_to_row(self, action: Action) -> dict[str, str]:
        return {"id": action.storage_id, "action": action.content}

    def _fact_to_row(self, fact: Fact) -> dict[str, str]:
        return {"id": fact.storage_id, "fact": fact.content}

    def _delete_content_element(self,
                                content_element: ContentElement,
                                memory_table: nicegui.ui.table) -> None:
        for each_row in memory_table.rows:
            if each_row["id"] == content_element.storage_id:
                to_remove = each_row
                break
        else:
            raise ValueError(f"Could not find row with id {content_element.storage_id}")

        memory_table.remove_rows(to_remove)

    def delete_facts(self, facts: list[Fact]) -> None:
        for each_fact in facts:
            if each_fact.storage_id.startswith("global:"):
                memory_table = self.global_facts_table

            elif each_fact.storage_id.startswith("local_"):
                selected_agent_id = self.get_selected_agent_id()
                if not each_fact.storage_id.startswith(f"local_{selected_agent_id}"):
                    continue
                memory_table = self.local_facts_table

            else:
                raise ValueError(f"Unknown storage id: {each_fact.storage_id}")

            self._delete_content_element(each_fact, memory_table)

    def delete_actions(self, actions: list[Action]) -> None:
        for each_action in actions:
            if each_action.storage_id.startswith("global:"):
                memory_table = self.global_actions_table

            elif each_action.storage_id.startswith("local_"):
                selected_agent_id = self.get_selected_agent_id()
                if not each_action.storage_id.startswith(f"local_{selected_agent_id}"):
                    continue
                memory_table = self.local_actions_table

            else:
                raise ValueError(f"Unknown storage id: {each_action.storage_id}")

            self._delete_content_element(each_action, memory_table)

    def _upsert_content_element(self,
                                content_element: ContentElement,
                                element_to_row: Callable[[CONTENT_ELEMENT], dict[str, str]],
                                memory_table: nicegui.ui.table) -> None:

        new_row = element_to_row(content_element)
        for each_row in memory_table.rows:
            if each_row["id"] == content_element.storage_id:
                each_row.update(new_row)
                break
        else:
            memory_table.add_rows(new_row)

    def upsert_facts(self, facts: list[Fact]) -> None:
        for each_fact in facts:
            if each_fact.storage_id.startswith("global:"):
                memory_table = self.global_facts_table

            elif each_fact.storage_id.startswith("local_"):
                selected_agent_id = self.get_selected_agent_id()
                if not each_fact.storage_id.startswith(f"local_{selected_agent_id}"):
                    continue
                memory_table = self.local_facts_table

            else:
                raise ValueError(f"Unknown storage id: {each_fact.storage_id}")

            self._upsert_content_element(each_fact, self._fact_to_row, memory_table)

    def upsert_actions(self, actions: list[Action]) -> None:
        for each_action in actions:
            if each_action.storage_id.startswith("global:"):
                memory_table = self.global_actions_table

            elif each_action.storage_id.startswith("local_"):
                selected_agent_id = self.get_selected_agent_id()
                if not each_action.storage_id.startswith(f"local_{selected_agent_id}"):
                    continue
                memory_table = self.local_actions_table

            else:
                raise ValueError(f"Unknown storage id: {each_action.storage_id}")

            self._upsert_content_element(each_action, self._action_to_row, memory_table)

    def upsert_agent(self, agent: Agent) -> None:
        new_row = self._agent_to_row(agent)
        for each_row in self.agents_table.rows:
            if each_row["agent_id"] == agent.agent_id:
                each_row.update(new_row)
                break
        else:
            self.agents_table.add_rows(new_row)

    def remove_agent(self, agent: Agent) -> None:
        to_remove = None
        for each_row in self.agents_table.rows:
            if each_row["agent_id"] == agent.agent_id:
                to_remove = each_row
                break
        else:
            raise ValueError(f"Could not find row with id {agent.agent_id}")
        self.agents_table.remove_rows(each_row)

        if len(self.agents_table.rows) >= 1:
            first_agent_row = self.agents_table.rows[0]
            self.select_agent(first_agent_row["agent_id"])

    def memory_tables(self, agent_id: str, is_local: bool) -> tuple[Table, Table]:
        if is_local:
            facts = self.view_callbacks.get_facts(agent_id=agent_id)
            actions = self.view_callbacks.get_actions(agent_id=agent_id)
        else:
            facts = self.view_callbacks.get_facts()
            actions = self.view_callbacks.get_actions()

        with nicegui.ui.column() as column:
            column.classes("flex flex-col full-height full-width")

            with nicegui.ui.row() as row:
                row.classes("flex flex-1 flex-row full-height full-width")

                move_button, delete_button = None, None
                with nicegui.ui.scroll_area() as actions_scroll_area:
                    actions_scroll_area.classes("flex-1 full-height")

                    columns = [
                        {"name": "action", "label": "Action", "field": "action", "required": True, "align": "left", "type": "text"},
                        {"name": "id", "label": "ID", "field": "id", "required": True, "align": "left", "type": "text"}
                    ]
                    rows = [self._action_to_row(each_action) for each_action in actions]
                    # details (remove?, persist?)
                    actions_table = nicegui.ui.table(columns=columns, rows=rows, row_key="action", selection="multiple")
                    actions_table.on("selection", lambda: self.update_selected_actions(actions_table.selected, [move_button, delete_button]))
                    actions_table.style('background-color: #ebf1fa')

                with nicegui.ui.scroll_area() as facts_scroll_area:
                    facts_scroll_area.classes("flex-1 full-height")

                    columns = [
                        {"name": "fact", "label": "Fact", "field": "fact", "required": True, "align": "left", "type": "text"},
                        {"name": "id", "label": "ID", "field": "id", "required": True, "align": "left", "type": "text"}
                    ]
                    rows = [self._fact_to_row(each_fact) for each_fact in facts]
                    # details (remove?, persist?)
                    facts_table = nicegui.ui.table(columns=columns, rows=rows, row_key="id", selection="multiple")
                    facts_table.on("selection", lambda: self.update_selected_facts(facts_table.selected, [move_button, delete_button]))
                    facts_table.style('background-color: #ebf1fa')

            with nicegui.ui.row() as button_row:
                button_row.classes("flex-none justify-around full-width")
                move_button = nicegui.ui.button("Globalize" if is_local else "Localize")
                move_button.disable()

                delete_button = nicegui.ui.button("Delete")
                delete_button.disable()

        return actions_table, facts_table
