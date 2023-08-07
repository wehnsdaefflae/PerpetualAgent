# coding=utf-8

import nicegui


def page_layout():
    nicegui.ui.query('#c0').classes("h-screen")
    nicegui.ui.query('#c1').classes("h-full")
    nicegui.ui.query('#c2').classes("h-full")
    nicegui.ui.query('#c3').classes("h-full")

    with nicegui.ui.header(elevated=True).classes('items-center justify-between'):
        nicegui.ui.button(text="agents", on_click=lambda: left_drawer.toggle(), icon='arrow_left').props('flat color=white')
        nicegui.ui.label("Details").style('font-size: 20px')
        nicegui.ui.button(text="memory", on_click=lambda: right_drawer.toggle(), icon='arrow_right').props('flat color=white')

    with nicegui.ui.row().classes("flex flex-col h-full"):  # main page
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
                    nicegui.ui.label(f"natural result {i}").classes("flex-1 m-3 p-3 bg-yellow-200 rounded-lg")
                    nicegui.ui.button("details").classes("mx-5")
                nicegui.ui.separator().classes("my-5")

        with nicegui.ui.row().style('background-color: #f0f4fa; width: 100%').classes('justify-around flex-none'):
            nicegui.ui.button("Pause")
            nicegui.ui.button("Cancel")

    with nicegui.ui.left_drawer(top_corner=False, bottom_corner=False).style('background-color: #d7e3f4').classes("flex flex-col h-full") as left_drawer:
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
            {"id": 6, "name": "task", "status": "finished", "color": "positive"},
            {"id": 7, "name": "task", "status": "pending", "color": "warning"},
            {"id": 8, "name": "task", "status": "working", "color": "info"},
            {"id": 9, "name": "task", "status": "paused", "color": "accent"},
            {"id": 10, "name": "task", "status": "cancelled", "color": "negative"},
            {"id": 11, "name": "task", "status": "finished", "color": "positive"},
            {"id": 12, "name": "task", "status": "pending", "color": "warning"},
            {"id": 13, "name": "task", "status": "working", "color": "info"},
            {"id": 14, "name": "task", "status": "paused", "color": "accent"},
            {"id": 15, "name": "task", "status": "cancelled", "color": "negative"},
            {"id": 16, "name": "task", "status": "finished", "color": "positive"},
            {"id": 17, "name": "task", "status": "pending", "color": "warning"},
            {"id": 18, "name": "task", "status": "working", "color": "info"},
            {"id": 19, "name": "task", "status": "paused", "color": "accent"},
            {"id": 20, "name": "task", "status": "cancelled", "color": "negative"},
        ]
        with nicegui.ui.scroll_area().classes("flex-1"):
            nicegui.ui.table(columns=columns, rows=rows, row_key="agent_no")
        nicegui.ui.separator().classes("my-5")
        nicegui.ui.button("New task").classes("flex-none")

    with nicegui.ui.right_drawer(top_corner=False, bottom_corner=False).style('background-color: #ebf1fa').props(":width=\"500\"").classes("flex flex-col h-full") as right_drawer:
        with nicegui.ui.tabs() as tabs:
            local_memory = nicegui.ui.tab("local", "Local (ID 3)")
            global_memory = nicegui.ui.tab("global", "Global")

        with nicegui.ui.tab_panels(tabs, value=local_memory).classes("flex-1"):
            with nicegui.ui.tab_panel(local_memory):
                memory_table()

            with nicegui.ui.tab_panel(global_memory):
                memory_table()

    with nicegui.ui.footer().style('background-color: #3874c8'):
        nicegui.ui.label("Status updates from agents, incl. agent number")


def memory_table() -> None:
    with nicegui.ui.row().classes("flex flex-row full-height"):
        with nicegui.ui.scroll_area().classes("flex-1 full-height"):
            columns = [
                {"name": "fact", "label": "Fact", "field": "fact", "required": True, "align": "left", "type": "text"}
            ]
            rows = [
                {"fact": f"fact {i}"} for i in range(1, 51)
            ]
            # details (remove?, persist?)
            nicegui.ui.table(columns=columns, rows=rows, row_key="fact")

        with nicegui.ui.scroll_area().classes("flex-1 full-height"):
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
