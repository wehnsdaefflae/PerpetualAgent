# coding=utf-8
from dataclasses import dataclass
from typing import Literal, Callable, TypedDict

import nicegui
from nicegui.elements.dialog import Dialog
from nicegui.page_layout import LeftDrawer, RightDrawer, Element, Header, Footer


class AgentRow(TypedDict):
    id: str
    task: str
    status: Literal["finished", "pending", "working", "paused"]


@dataclass
class StepView:
    thought: str
    action_id: str
    arguments: dict[str, any]
    result: str
    fact_id: str


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
                 add_agent_to_model: Callable[[dict[str, any]], AgentRow],
                 get_agents_as_rows_from_model: Callable[[], list[AgentRow]],
                 get_agent_details_from_model: Callable[[str], AgentView],
                 get_fact_from_model: Callable[[str], str]
                 ) -> None:
        self.facts_local = list[FactsView]()
        self.facts_global = list[FactsView]()

        self.actions_local = list[ActionsView]()
        self.actions_global = list[ActionsView]()

        self.steps = list[StepView]()

        self.left_drawer = None
        self.right_drawer = None
        self.main_section = None

        self.agents_table = None

        self.add_agent_to_model = add_agent_to_model
        self.get_agents_as_rows_from_model = get_agents_as_rows_from_model
        self.get_agent_details_from_model = get_agent_details_from_model
        self.get_fact_from_model = get_fact_from_model

        self.run()

    def add_agent_rows(self, agent_rows: list[AgentRow]) -> None:
        new_rows = [each_row for each_row in agent_rows if each_row not in self.agents_table.rows]
        if len(new_rows) < 1:
            return

        self.agents_table.add_rows(*new_rows)

    def run(self) -> None:
        self.setup_page()

        self.main_section = self.get_empty_main()
        self.left_drawer = self._get_all_agents_drawer()
        self.right_drawer = self._get_memory_drawer()

        _ = self._add_header(self.left_drawer, self.right_drawer)
        _ = self._add_footer()

        nicegui.ui.run()

    def _add_footer(self) -> Footer:
        with nicegui.ui.footer() as footer:
            nicegui.ui.label("Status updates from agents, incl. agent number")

        return footer

    def _add_header(self, left_drawer: LeftDrawer, right_drawer: RightDrawer) -> Header:
        with nicegui.ui.header(elevated=True).classes('items-center justify-between') as header:
            nicegui.ui.button(text="agents", on_click=lambda: left_drawer.toggle(), icon='arrow_left').props('flat color=white')
            nicegui.ui.label("Details").style('font-size: 20px')
            nicegui.ui.button(text="memory", on_click=lambda: right_drawer.toggle(), icon='arrow_right').props('flat color=white')
        return header

    def _get_memory_drawer(self) -> RightDrawer:
        with nicegui.ui.right_drawer(top_corner=False, bottom_corner=False, value=False).style('background-color: #ebf1fa').props(":width=\"500\"").classes(
                "flex flex-col h-full") as right_drawer:
            with nicegui.ui.tabs() as tabs:
                local_memory = nicegui.ui.tab("local", "Local (ID 3)")
                global_memory = nicegui.ui.tab("global", "Global")

            with nicegui.ui.tab_panels(tabs, value=local_memory).classes("flex-1"):
                with nicegui.ui.tab_panel(local_memory):
                    self.memory_table()

                with nicegui.ui.tab_panel(global_memory):
                    self.memory_table()

        return right_drawer

    def change_details_view(self) -> None:
        self.main_section.clear()
        if len(self.agents_table.selected) < 1:
            self.empty_main()
            return

        selected, = self.agents_table.selected
        agent_id = selected["id"]
        agent_details = self.get_agent_details_from_model(agent_id)

        with self.main_section:
            nicegui.ui.label(agent_details.task).classes("text-2xl flex-none")
            nicegui.ui.label(
                f"{agent_details.summary} [This is the progress report.]"
            ).classes("flex-none")

            # grow dynamically
            with nicegui.ui.scroll_area().style('background-color: #f0f4fa').classes("flex-1"):
                for each_step in agent_details.steps:
                    with nicegui.ui.row().classes("justify-between flex items-center"):
                        nicegui.ui.label(each_step.thought).classes("flex-1 m-3 p-3 bg-blue-300 rounded-lg").on("click", self.thought_details)
                        nicegui.ui.button("details", on_click=self.thought_details).classes("mx-5")

                    with nicegui.ui.row().classes("justify-between flex items-center"):
                        each_fact = self.get_fact_from_model(each_step.fact_id)
                        nicegui.ui.label(f"{each_fact} ({each_step.fact_id})").classes("flex-1 m-3 p-3 bg-green-300 rounded-lg").on("click", self.fact_details)
                        nicegui.ui.button("details", on_click=self.fact_details).classes("mx-5")

                    nicegui.ui.separator().classes("my-2")

            with nicegui.ui.row().classes('justify-around flex-none w-full'):
                nicegui.ui.button("Pause")
                nicegui.ui.button("Cancel")

    def thought_details(self) -> None:
        print("show action (action_id) and action arguments")

    def fact_details(self) -> None:
        print("show action result")

    def _get_all_agents_drawer(self) -> LeftDrawer:
        with nicegui.ui.left_drawer(top_corner=False, bottom_corner=False).style('background-color: #d7e3f4').classes("flex flex-col h-full") as left_drawer:
            columns = [
                {"name": "id", "label": "ID", "field": "id", "required": True, "align": "left", "type": "text"},
                {"name": "task", "label": "Task", "field": "task", "required": True, "align": "left", "type": "text"},
                {"name": "status", "label": "Status", "field": "status", "required": True, "align": "left", "type": "text"},
            ]
            with nicegui.ui.scroll_area().classes("flex-1"):
                rows = self.get_agents_as_rows_from_model()
                self.agents_table = nicegui.ui.table(columns=columns, rows=rows, row_key="id", selection="single", on_select=self.change_details_view)
                self.empty_main()

            nicegui.ui.separator().classes("my-5")
            nicegui.ui.button("New task", on_click=self.get_dialog)

            return left_drawer

    async def get_dialog(self) -> Dialog:
        llms = ["chatgpt-3.5-turbo", "gpt-4", "llama", "etc."]

        def enable_ok_button() -> None:
            if 0 < len(text_area.value):
                button_ok.enable()
            else:
                button_ok.disable()

        with nicegui.ui.dialog() as dialog, nicegui.ui.card():
            nicegui.ui.label("Set up agent").classes("text-xl")
            text_area = nicegui.ui.textarea(placeholder="Task", label="Enter the agent's task", on_change=enable_ok_button).classes("w-full")

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

            confirm_actions = nicegui.ui.checkbox("Confirm actions / start", value=True)

            with nicegui.ui.row().classes('justify-around w-full'):
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

        return dialog

    def get_empty_main(self) -> Element:
        with nicegui.ui.row().classes("flex flex-col h-full w-full") as main_section:
            nicegui.ui.label("no agent selected").classes("text-2xl flex-none")
        return main_section

    def empty_main(self) -> None:
        self.main_section.clear()
        with self.main_section:
            nicegui.ui.label("no agent selected").classes("text-2xl flex-none")

    def setup_page(self) -> None:
        nicegui.ui.query('#c0').classes("h-screen")
        nicegui.ui.query('#c1').classes("h-full")
        nicegui.ui.query('#c2').classes("h-full")
        nicegui.ui.query('#c3').classes("h-full")

    def memory_table(self) -> None:
        with nicegui.ui.row().classes("flex flex-row full-height"):
            with nicegui.ui.scroll_area().classes("flex-1 full-height"):
                columns = [
                    {"name": "fact", "label": "Fact", "field": "fact", "required": True, "align": "left", "type": "text"}
                ]
                rows = [
                    {"fact": f"fact {i}"} for i in range(1, 51)
                ]
                # details (remove?, persist?)
                nicegui.ui.table(columns=columns, rows=rows, row_key="fact").style('background-color: #ebf1fa')

            with nicegui.ui.scroll_area().classes("flex-1 full-height"):
                columns = [
                    {"name": "action", "label": "Action", "field": "action", "required": True, "align": "left", "type": "text"}
                ]
                rows = [
                    {"action": f"action {i}"} for i in range(1, 51)
                ]
                # details (remove?, persist?)
                nicegui.ui.table(columns=columns, rows=rows, row_key="action").style('background-color: #ebf1fa')
