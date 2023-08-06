# coding=utf-8
import datetime

import nicegui
from nicegui.elements.tabs import Tab


def page_layout():
    with nicegui.ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between'):
        nicegui.ui.button(text="agents", on_click=lambda: left_drawer.toggle(), icon='arrow_left').props('flat color=white')
        nicegui.ui.label("Details").style('font-size: 20px')
        nicegui.ui.button(text="memory", on_click=lambda: right_drawer.toggle(), icon='arrow_right').props('flat color=white')

    with nicegui.ui.row().style("width: 100%; position: absolute; left: 0; top: 0; bottom: 0; padding: 20px").classes("flex-col"):  # main page
        with nicegui.ui.column().style("width: 100%").classes('items-center justify-center'):
            nicegui.ui.label("Develop a new anti cancer drug.").classes("text-2xl")
            nicegui.ui.label(
                "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, "
                "sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor "
                "sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, "
                "sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor "
                "sit amet. [This is the progress report.]"
            )

        # grow dynamically
        with nicegui.ui.scroll_area().style('background-color: #f0f4fa').classes("grow") as protocol:
            for i in range(1, 51):
                with nicegui.ui.row().classes("justify-between flex items-center"):
                    nicegui.ui.label(f"natural thought {i}").classes("grow m-3 p-3 bg-blue-300 rounded-lg")
                    nicegui.ui.button("details").classes("mx-5")
                with nicegui.ui.row().classes("justify-between flex items-center"):
                    nicegui.ui.label(f"natural result {i}").classes("grow m-3 p-3 bg-yellow-200 rounded-lg")
                    nicegui.ui.button("details").classes("mx-5")
                nicegui.ui.separator().classes("my-5")
            # protocol.scroll_to(percent=100)

        with nicegui.ui.row().style('background-color: #f0f4fa; width: 100%').classes('justify-around'):
            nicegui.ui.button("Pause")
            nicegui.ui.button("Cancel")

    with nicegui.ui.left_drawer(top_corner=False, bottom_corner=False).style('background-color: #d7e3f4').classes("flex flex-col items-center") as left_drawer:
        nicegui.ui.button("New task")
        nicegui.ui.separator().classes("my-5")
        columns = [
            {"name": "id", "label": "ID", "field": "id", "required": True, "align": "left", "type": "number"},
            {"name": "task", "label": "Task", "field": "name", "required": True, "align": "left", "type": "text"},
            {"name": "status", "label": "Status", "field": "status", "required": True, "align": "left", "type": "text"},
        ]
        rows = [
            {"id": 1, "name": "task", "status": "finished", "color": "positive"},
            {"id": 2, "name": "task", "status": "pending", "color": "warning"},
            {"id": 3, "name": "task", "status": "working", "color": "info"},
            {"id": 4, "name": "task", "status": "paused", "color": "accent"},
            {"id": 5, "name": "task", "status": "cancelled", "color": "negative"},
        ]
        nicegui.ui.table(columns=columns, rows=rows, row_key="agent_no").classes("w-full")

    with nicegui.ui.right_drawer(top_corner=False, bottom_corner=False).style('background-color: #ebf1fa').props(":width=\"500\"") as right_drawer:
        with nicegui.ui.tabs() as tabs:
            local_memory = nicegui.ui.tab("local", "Local (ID 3)")
            global_memory = nicegui.ui.tab("global", "Global")

        with nicegui.ui.tab_panels(tabs, value=local_memory):
            with nicegui.ui.tab_panel(local_memory).classes("flex") as tab_local:
                # memory_table()
                # nicegui.ui.element("div").style("width: 100%; height: 100px; background-color: #ff0000").classes("grow")
                nicegui.ui.element("div").style("width: 100%; background-color: #ff0000").classes("grow")

            with nicegui.ui.tab_panel(global_memory):
                memory_table()

    with nicegui.ui.footer().style('background-color: #3874c8'):
        nicegui.ui.label("Status updates from agents, incl. agent number")


def memory_table() -> None:
    with nicegui.ui.row().classes("justify-between"):
        with nicegui.ui.scroll_area().style("width: 45%"):
            columns = [
                {"name": "fact", "label": "Fact", "field": "fact", "required": True, "align": "left", "type": "text"}
            ]
            rows = [
                {"fact": f"fact {i}"} for i in range(1, 51)
            ]
            # details (remove?, persist?)
            nicegui.ui.table(columns=columns, rows=rows, row_key="fact")

        with nicegui.ui.scroll_area().style("width: 45%"):
            columns = [
                {"name": "action", "label": "Action", "field": "action", "required": True, "align": "left", "type": "text"}
            ]
            rows = [
                {"action": f"action {i}"} for i in range(1, 51)
            ]
            # details (remove?, persist?)
            nicegui.ui.table(columns=columns, rows=rows, row_key="action")


def main() -> None:
    """
    with nicegui.ui.row():  # main page
        with nicegui.ui.column():
            with nicegui.ui.header():
                nicegui.ui.label("Agent list")
            nicegui.ui.button("create new agent", on_click=lambda: nicegui.ui.show_dialog("create new agent"))

        with nicegui.ui.column():
            with nicegui.ui.header():
                nicegui.ui.label("Agent details")
            nicegui.ui.label("agent details")

        with nicegui.ui.column():
            with nicegui.ui.header():
                nicegui.ui.label("Agent memory")
            nicegui.ui.label("memory")
    """

    page_layout()

    nicegui.ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    main()
