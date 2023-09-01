# coding=utf-8
from typing import Literal

from nicegui import ui


# coding=utf-8
class View:
    def __init__(self) -> None:
        self.header = None

        self.left_drawer = None
        self.agent_table = None

        self.main = None

        self.right_drawer = None

        self.footer = None

        self._run()

    @staticmethod
    def modify_page() -> None:
        ui.query('#c0').classes("h-screen")
        ui.query('#c1').classes("h-full")
        ui.query('#c2').classes("h-full")
        ui.query('#c3').classes("h-full")

    def _create_header(self) -> ui.header:
        if self.header is not None:
            raise Exception("Header already created.")

        with ui.header(elevated=True) as header:
            header.classes("items-center justify-between")

        self._update_header()
        return header

    def _create_agent_table(self) -> ui.table:
        if self.agent_table is not None:
            raise Exception("Agent table already created.")

        columns = [
            {"name": "agent_id", "label": "ID", "field": "agent_id", "required": True, "align": "left", "type": "text"},
            {"name": "status", "label": "Status", "field": "status", "required": True, "align": "left", "type": "text"},
            {"name": "task", "label": "Task", "field": "task", "required": True, "align": "left", "type": "text"},
        ]

        def show_stream_selected_agent() -> None:
            # todo
            print("show stream of selected agent")

        with ui.scroll_area() as scroll_area:
            agent_table = ui.table(
                columns=columns, rows=list(), row_key="agent_id", selection="single", on_select=show_stream_selected_agent
            )
            scroll_area.classes("flex-1")
            agent_table.on("click", show_stream_selected_agent)

        return agent_table

    def _create_left_drawer(self) -> ui.left_drawer:
        if self.left_drawer is not None:
            raise Exception("Left drawer already created.")

        with ui.left_drawer(top_corner=False, bottom_corner=False) as left_drawer:
            left_drawer.style('background-color: #d7e3f4')
            left_drawer.classes("flex flex-col h-full")

            self.agent_table = self._create_agent_table()

        self._update_left_drawer()
        return left_drawer

    def _create_main(self) -> ui.element:
        if self.main is not None:
            raise Exception("Main already created.")

        with ui.row() as row:
            row.classes("flex flex-col h-full w-full")

        self._update_main()
        return row

    def _create_right_drawer(self) -> ui.right_drawer:
        if self.right_drawer is not None:
            raise Exception("Right drawer already created.")

        with ui.right_drawer(top_corner=False, bottom_corner=False, value=False) as right_drawer:
            right_drawer.style('background-color: #ebf1fa')
            right_drawer.props(":width=\"500\"")
            right_drawer.classes("flex flex-col h-full")

        self._update_right_drawer()
        return right_drawer

    def _create_footer(self) -> ui.footer:
        if self.footer is not None:
            raise Exception("Footer already created.")

        def debug_pause() -> None:
            print("debug pause")

        with ui.footer() as footer:
            ui.button("debug", on_click=debug_pause)

        self._update_footer()
        return footer

    def _run(self) -> None:
        View.modify_page()

        self.header = self._create_header()
        self.left_drawer = self._create_left_drawer()
        self.main = self._create_main()
        self.right_drawer = self._create_right_drawer()
        self.footer = self._create_footer()

    def _update_header(self) -> None:
        with self.header:
            ui.button(text="agents", on_click=self.left_drawer.toggle, icon="arrow_left")
            main_heading = ui.label("Details")
            main_heading.style("font-size: 20px")
            ui.button(text="memory", on_click=self.right_drawer.toggle, icon="arrow_right")

    def _update_agent_table(self) -> None:
        # update on
        #   agent creation
        #   agent deletion
        #   agent status change
        pass

    def _update_left_drawer(self) -> None:
        self._update_agent_table()

    def _update_main(self, source: Literal["agent_table", "fact_table", "action_table"] = "agent_table") -> None:
        # update on
        #   agent click
        #   fact click
        #   action click

        # show agent details, fact details, or action details

        match source:
            case "agent_table":
                pass
                # show stream of selected agent
                # WHENEVER
                # agent status change
                # agent thought update
                # agent relevant facts update
                # agent action attempt update
                # agent action update
                # agent action arguments update
                # agent action output update
                # agent fact (is_successful) update
                # agent summary (is_fulfilled) update

            case "fact_table":
                pass
                # show fact details
                # WHENEVER
                # fact selected

            case "action_table":
                pass
                # show action details
                # WHENEVER
                # action selected

            case _:
                raise Exception("Invalid source")

    def _update_right_drawer(self) -> None:
        # update on
        #   agent selection
        #   new fact
        #   fact deletion
        #   new action
        #   action deletion
        pass

    def _update_footer(self) -> None:
        # update on
        #   any llm call
        pass
