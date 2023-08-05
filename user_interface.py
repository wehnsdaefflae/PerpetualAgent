# coding=utf-8
import nicegui


def page_layout():
    with nicegui.ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between'):
        nicegui.ui.button(text="agents", on_click=lambda: left_drawer.toggle(), icon='arrow_left').props('flat color=white')
        nicegui.ui.label("Details").style('font-size: 20px')
        nicegui.ui.button(text="memory", on_click=lambda: right_drawer.toggle(), icon='arrow_right').props('flat color=white')

    with nicegui.ui.row().style("width: 100%"):  # main page
        with nicegui.ui.column().style("width: 100%").classes('items-center justify-center'):
            nicegui.ui.label("Develop a new anti cancer drug.")
            nicegui.ui.label("[This is the progress report.]")

        with nicegui.ui.scroll_area().style('background-color: #f0f4fa; min-height: 70vh') as protocol:
            for i in range(50):
                with nicegui.ui.expansion(text=f"Step {i}", value=i == 49):
                    nicegui.ui.label(f"Action: stuff")
                    nicegui.ui.label(f"Result: stuff")
            # protocol.scroll_to(percent=100)

        with nicegui.ui.row().style('background-color: #f0f4fa'):
            nicegui.ui.button("Pause")
            nicegui.ui.button("Cancel")

    with nicegui.ui.left_drawer(top_corner=False, bottom_corner=False).style('background-color: #d7e3f4') as left_drawer:
        nicegui.ui.button("new agent")
        nicegui.ui.separator()
        [nicegui.ui.button(f"Agent {i}: finished", color="positive") for i in range(3)]
        [nicegui.ui.button(f"Agent {i}: working", color="info") for i in range(3)]
        [nicegui.ui.button(f"Agent {i}: paused", color="warning") for i in range(3)]

    with nicegui.ui.right_drawer(top_corner=False, bottom_corner=False).style('background-color: #ebf1fa') as right_drawer:
        nicegui.ui.label("local")
        [nicegui.ui.label(f"Fact {i}: show (approve?), remove") for i in range(3)]
        [nicegui.ui.label(f"Action {i}: show (approve?), remove") for i in range(3)]

        nicegui.ui.separator()

        nicegui.ui.label("global")
        [nicegui.ui.label(f"Fact {i}: show, remove") for i in range(3)]
        [nicegui.ui.label(f"Action {i}: show, remove") for i in range(3)]


    with nicegui.ui.footer().style('background-color: #3874c8'):
        nicegui.ui.label("Status update from agents, incl. agent number")


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
