# coding=utf-8
from dataclasses import dataclass
from typing import Literal

import nicegui
from nicegui.elements.dialog import Dialog
from nicegui.elements.table import Table
from nicegui.page_layout import LeftDrawer, RightDrawer, Element, Header, Footer

# from new_attempt.agent import Agent


@dataclass
class AgentView:
    id: int
    task: str
    status: Literal["finished", "pending", "working", "paused"] = "working"


@dataclass
class StepView:
    thought: str
    result: str


@dataclass
class FactsView:
    facts: list[str]


@dataclass
class ActionsView:
    actions: list[str]


"""
def add_agent(properties: dict[str, any]) -> None:
    agent_id = len(AGENT_LIST)
    user_input = f"Task for agent {agent_id}"

    project_id = str(agent_id)
    agent_instance = Agent(project_id, user_input)

    agent_view = AgentView(agent_id, user_input)
    AGENT_LIST.append(agent_view)

    agent_instance.start()
    agent_instance.join()
"""


class View:
    def __init__(self):
        self.agent_rows = list()

        self.facts_local = list[FactsView]()
        self.facts_global = list[FactsView]()

        self.actions_local = list[ActionsView]()
        self.actions_global = list[ActionsView]()

        self.steps = list[StepView]()

        self.run()

    def run(self) -> None:
        self.setup_page()

        _ = self.get_main_agent_details()
        all_agents_drawer = self.get_all_agents_drawer()
        memory_drawer = self.get_memory_drawer()

        _ = self.add_header(all_agents_drawer, memory_drawer)
        _ = self.add_footer()

        nicegui.ui.run()

    def add_footer(self) -> Footer:
        with nicegui.ui.footer() as footer:
            nicegui.ui.label("Status updates from agents, incl. agent number")

        return footer

    def add_header(self, left_drawer: LeftDrawer, right_drawer: RightDrawer) -> Header:
        with nicegui.ui.header(elevated=True).classes('items-center justify-between') as header:
            nicegui.ui.button(text="agents", on_click=lambda: left_drawer.toggle(), icon='arrow_left').props('flat color=white')
            nicegui.ui.label("Details").style('font-size: 20px')
            nicegui.ui.button(text="memory", on_click=lambda: right_drawer.toggle(), icon='arrow_right').props('flat color=white')
        return header

    def get_memory_drawer(self) -> RightDrawer:
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

    def get_all_agents_drawer(self) -> LeftDrawer:
        with nicegui.ui.left_drawer(top_corner=False, bottom_corner=False).style('background-color: #d7e3f4').classes("flex flex-col h-full") as left_drawer:
            columns = [
                {"name": "id", "label": "ID", "field": "id", "required": True, "align": "left", "type": "number"},
                {"name": "task", "label": "Task", "field": "task", "required": True, "align": "left", "type": "text"},
                {"name": "status", "label": "Status", "field": "status", "required": True, "align": "left", "type": "text"},
            ]
            with nicegui.ui.scroll_area().classes("flex-1"):
                table = nicegui.ui.table(columns=columns, rows=self.agent_rows, row_key="agent_no")

            nicegui.ui.separator().classes("my-5")
            # nicegui.ui.button("New task", on_click=add_agent)

            # nicegui.ui.button("New task", on_click=t)
            nicegui.ui.button("New task", on_click=lambda: self.get_dialog(table))

            return left_drawer

    async def get_dialog(self, table: Table) -> Dialog:
        llms = ["chatgpt-3.5-turbo", "gpt-4", "llama", "etc."]

        def enable_ok_button() -> None:
            if 0 < len(text_area.value):
                button_ok.enable()
            else:
                button_ok.disable()

        with nicegui.ui.dialog() as dialog, nicegui.ui.card():
            nicegui.ui.label("Set up agent").classes("text-xl")
            text_area = nicegui.ui.textarea(placeholder="Request", label="Enter your request", on_change=enable_ok_button).classes("w-full")

            with nicegui.ui.row():
                with nicegui.ui.column():
                    read_facts_global = nicegui.ui.checkbox("Read global facts", value=True)
                    read_actions_global = nicegui.ui.checkbox("Read global actions", value=True)
                    nicegui.ui.separator()
                    confirm_actions = nicegui.ui.checkbox("Confirm actions", value=True).classes("w-full")

                with nicegui.ui.column():
                    write_facts_global = nicegui.ui.checkbox("Write global facts")
                    write_actions_global = nicegui.ui.checkbox("Write global actions")
                    write_facts_local = nicegui.ui.checkbox("Write local facts")
                    write_actions_local = nicegui.ui.checkbox("Write local actions")

            with nicegui.ui.row():
                with nicegui.ui.column():
                    llm_thought = nicegui.ui.select(llms, label="Thought inference", value=llms[0]).classes("w-full")
                    llm_action = nicegui.ui.select(llms, label="Action generation", value=llms[0]).classes("w-full")
                    llm_parameter = nicegui.ui.select(llms, label="Parameter extraction", value=llms[0]).classes("w-full")

                with nicegui.ui.column():
                    llm_result = nicegui.ui.select(llms, label="Result naturalization", value=llms[0]).classes("w-full")
                    llm_fact = nicegui.ui.select(llms, label="Fact composition", value=llms[0]).classes("w-full")
                    llm_summary = nicegui.ui.select(llms, label="Progress summarization", value=llms[0]).classes("w-full")

                with nicegui.ui.row().classes('justify-around w-full'):
                    button_ok = nicegui.ui.button("OK", color="primary", on_click=lambda: dialog.submit("done"))
                    button_ok.disable()
                    nicegui.ui.button("Cancel", color="secondary", on_click=dialog.close)

        result = await dialog
        if result is not None:
            setup = {
                "request": text_area.value,
                "facts_global": (read_facts_global.value, write_facts_global.value),
                "actions_global": (read_actions_global.value, write_actions_global.value),
                "facts_local": write_facts_local.value,
                "actions_local": write_actions_local.value,

                "confirm_actions": confirm_actions.value,

                "llm_thought": llm_thought.value,
                "llm_action": llm_action.value,
                "llm_parameter": llm_parameter.value,
                "llm_result": llm_result.value,
                "llm_fact": llm_fact.value,
                "llm_summary": llm_summary.value,
            }

            # print(result)
            agent_id = len(self.agent_rows)
            agent_view = {"id": agent_id, "task": setup["request"], "status": "working"}
            self.agent_rows.append(agent_view)
            table.update()

        return dialog

    def get_main_agent_details(self) -> Element:
        with nicegui.ui.row().classes("flex flex-col h-full") as main_section:
            nicegui.ui.label("Develop a new anti cancer drug.").classes("text-2xl flex-none")
            nicegui.ui.label(
                "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, "
                "sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor "
                "sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, "
                "sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor "
                "sit amet. [This is the progress report.]"
            ).classes("flex-none")

            # grow dynamically
            with nicegui.ui.scroll_area().style('background-color: #f0f4fa').classes("flex-1"):
                for i in range(1, 51):
                    with nicegui.ui.row().classes("justify-between flex items-center"):
                        nicegui.ui.label(f"natural thought {i}").classes("flex-1 m-3 p-3 bg-blue-300 rounded-lg")
                        nicegui.ui.button("details").classes("mx-5")
                    with nicegui.ui.row().classes("justify-between flex items-center"):
                        nicegui.ui.label(f"natural result {i}").classes("flex-1 m-3 p-3 bg-green-300 rounded-lg")
                        nicegui.ui.button("details").classes("mx-5")
                    nicegui.ui.separator().classes("my-2")

            with nicegui.ui.row().classes('justify-around flex-none w-full'):
                nicegui.ui.button("Pause")
                nicegui.ui.button("Cancel")

        return main_section

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


def main() -> None:
    # Initial data
    user_input = "Your request here"
    project_id = "Your project ID here"

    # agent_instance.start()
    # agent_instance.join()

    view = View()


if __name__ in {"__main__", "__mp_main__"}:
    main()
