# coding=utf-8
import json
from dataclasses import dataclass
from typing import Literal, Callable, TypedDict

import nicegui
from nicegui.elements.button import Button
from nicegui.elements.dialog import Dialog
from nicegui.elements.table import Table


class AgentRow(TypedDict):
    id: str
    task: str
    status: Literal["finished", "pending", "working", "paused"]


@dataclass
class FactView:
    fact: str
    fact_id: str


@dataclass
class ActionView:
    action: str
    action_id: str


@dataclass
class StepView:
    thought: str
    action_id: str
    action_is_local: bool
    arguments: dict[str, any]
    result: str
    fact_id: str
    fact_is_local: bool


@dataclass
class AgentView:
    id: str
    task: str
    summary: str
    status: Literal["finished", "pending", "working", "paused"]
    steps: list[StepView]


@dataclass
class FactsView:
    facts: list[str]


@dataclass
class ActionsView:
    actions: list[str]


class View:
    def __init__(self,
                 add_agent_to_model:            Callable[[dict[str, any]], AgentRow],
                 get_agents_as_rows_from_model: Callable[[], list[AgentRow]],
                 get_agent_details_from_model:  Callable[[str], AgentView],
                 get_fact_from_model:           Callable[[str], str],
                 get_action_from_model:         Callable[[str], str],
                 get_local_facts:               Callable[[str], list[FactView]],
                 get_local_actions:             Callable[[str], list[ActionView]],
                 get_global_facts:              Callable[[], list[FactView]],
                 get_global_actions:            Callable[[], list[ActionView]],
                 ) -> None:

        self.selected_fact_ids = list[dict[str, any]]()
        self.selected_action_ids = list[dict[str, any]]()

        self.steps = list[StepView]()

        self.local_facts_table = None
        self.local_actions_table = None
        self.global_facts_table = None
        self.global_actions_table = None

        self.header = None
        self.left_drawer = None
        self.right_drawer = None
        self.main_section = None
        self.footer = None

        self.agents_table = None

        self.add_agent_to_model = add_agent_to_model
        self.get_agents_as_rows_from_model = get_agents_as_rows_from_model
        self.get_agent_details_from_model = get_agent_details_from_model
        self.get_fact_from_model = get_fact_from_model
        self.get_action_from_model = get_action_from_model
        self.get_local_facts = get_local_facts
        self.get_local_actions = get_local_actions
        self.get_global_facts = get_global_facts
        self.get_global_actions = get_global_actions

        self.run()

    def add_agent_rows(self, agent_rows: list[AgentRow]) -> None:
        new_rows = [each_row for each_row in agent_rows if each_row not in self.agents_table.rows]
        if len(new_rows) < 1:
            return

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
                {"name": "id", "label": "ID", "field": "id", "required": True, "align": "left", "type": "text"},
                {"name": "task", "label": "Task", "field": "task", "required": True, "align": "left", "type": "text"},
                {"name": "status", "label": "Status", "field": "status", "required": True, "align": "left", "type": "text"},
            ]
            with nicegui.ui.scroll_area() as scroll_area:
                scroll_area.classes("flex-1")
                rows = self.get_agents_as_rows_from_model()
                self.agents_table = nicegui.ui.table(columns=columns, rows=rows, row_key="id", selection="single", on_select=self.agent_changed)

            nicegui.ui.separator().classes("my-5")
            with nicegui.ui.row() as row:
                row.classes("justify-around full-width flex-none")
                nicegui.ui.button("New task", on_click=self.get_dialog)
                nicegui.ui.button("Pause all")

    def fill_footer(self) -> None:
        with self.footer:
            nicegui.ui.label("Status updates from agents, incl. agent number")

    def switched_memory_tab(self) -> None:
        print("switched tab")

    def fill_right_drawer(self) -> None:
        self.right_drawer.clear()
        agent_id = self.get_agent_id()

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

    def get_agent_id(self) -> str | None:
        if len(self.agents_table.selected) < 1:
            return None

        selected, = self.agents_table.selected
        agent_id = selected["id"]
        return agent_id

    def fill_main(self) -> None:
        self.main_section.clear()

        agent_id = self.get_agent_id()
        with self.main_section:
            if agent_id is None:
                message = nicegui.ui.label("no agent selected")
                message.classes("text-2xl flex-none")
                return

            agent_details = self.get_agent_details_from_model(agent_id)

            label_task = nicegui.ui.label(agent_details.task)
            label_task.classes("text-2xl flex-none")

            label_progress = nicegui.ui.label(f"{agent_details.summary} [This is the progress report.]")
            label_progress.classes("flex-none")

            with nicegui.ui.scroll_area() as scroll_area:
                scroll_area.style('background-color: #f0f4fa')
                scroll_area.classes("flex-1")

                for each_step in agent_details.steps:
                    with nicegui.ui.row() as action_row:
                        action_row.classes("justify-between flex items-center")
                        label_thought = nicegui.ui.label(each_step.thought)
                        label_thought.classes("flex-1 m-3 p-3 bg-blue-300 rounded-lg")
                        action_dialog = self.show_action(each_step.action_id, each_step.arguments)
                        action_button = nicegui.ui.button("show action", on_click=action_dialog.open)
                        action_button.classes("mx-5")

                    with nicegui.ui.row() as fact_row:
                        fact_row.classes("justify-between flex items-center")
                        each_fact = self.get_fact_from_model(each_step.fact_id)
                        label_fact = nicegui.ui.label(f"{each_fact} (fact #{each_step.fact_id})")
                        label_fact.classes("flex-1 m-3 p-3 bg-green-300 rounded-lg")
                        result_dialog = self.show_result(each_step.result)
                        result_button = nicegui.ui.button("show result", on_click=result_dialog.open)
                        result_button.classes("mx-5")

                    nicegui.ui.separator().classes("my-2")

            with nicegui.ui.row().classes('justify-around flex-none full-width'):
                nicegui.ui.button("Pause")
                nicegui.ui.button("Cancel")

    def show_action(self, action_id: str, arguments: dict[str, any]) -> Dialog:
        action = self.get_action_from_model(action_id)
        with nicegui.ui.dialog() as dialog, nicegui.ui.card():
            nicegui.ui.label(f"{action} (action #{action_id})")
            nicegui.ui.label(json.dumps(arguments, indent=4))
        return dialog

    def show_result(self, result: str) -> Dialog:
        with nicegui.ui.dialog() as dialog, nicegui.ui.card():
            nicegui.ui.label(result)

        return dialog

    def agent_changed(self) -> None:
        self.fill_main()
        self.fill_right_drawer()

    async def get_dialog(self) -> None:
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

            with nicegui.ui.row().classes("justify-around full-width flex-none"):
                button_ok = nicegui.ui.button("OK", color="primary", on_click=lambda: dialog.submit("done"))
                button_ok.disable()
                nicegui.ui.button("Cancel", color="secondary", on_click=dialog.close)

        result = await dialog
        if result is not None:
            setup = {
                "task": text_area.value,
                "read_facts_global": read_facts_global.value,
                "read_actions_global": read_actions_global.value,
                "write_facts_local": write_facts_local.value,
                "write_actions_local": write_actions_local.value,

                "confirm_actions": confirm_actions.value,

                "llm_thought": llm_thought.value,
                "llm_action": llm_action.value,
                "llm_parameter": llm_parameter.value,
                "llm_result": llm_result.value,
                "llm_fact": llm_fact.value,
                "llm_summary": llm_summary.value,
            }

            agent_view = self.add_agent_to_model(setup)
            self.add_agent_rows([agent_view])

    def update_memory_buttons(self, buttons: list[Button], enable: bool) -> None:
        if enable:
            for each_button in buttons:
                each_button.enable()
        else:

            for each_button in buttons:
                each_button.disable()

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

    def memory_tables(self, agent_id: str, is_local: bool) -> tuple[Table, Table]:
        if is_local:
            facts = self.get_local_facts(agent_id)
            actions = self.get_local_actions(agent_id)

        else:
            facts = self.get_global_facts()
            actions = self.get_global_actions()

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
                    rows = [
                        {"id": each_action.action_id, "action": each_action.action} for each_action in actions
                    ]
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
                    rows = [
                        {"id": each_fact.fact_id, "fact": each_fact.fact} for each_fact in facts
                    ]
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
