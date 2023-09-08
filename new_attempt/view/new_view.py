# coding=utf-8
from typing import Literal

from nicegui import ui

from new_attempt.model.agent.agent import Agent, Status
from new_attempt.model.agent.step_elements import Thought, Fact, Action, ActionArguments, ActionOutput, Summary, ActionWasSuccessful, IsFulfilled, ActionAttempt


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


    def _agent_details(self, agent: Agent) -> None:
        task_label = ui.markdown(f"**Task:** {agent.arguments.task}")
        task_label.classes("text-xl flex-none")

        progress_label = ui.markdown(f"**Progress summary:** {agent.summary}")
        progress_label.classes("flex-none")

        with ui.scroll_area() as self.main:
            self.main.classes("flex-1")

            with ui.column() as stream:
                stream.classes("flex flex-col full-width")

        with ui.row() as buttons:
            buttons.classes("flex-none justify-around full-width")
            pause_button = ui.button("pause", on_click=lambda: self._pause(agent))
            delete_button = ui.button("delete", on_click=lambda: self._delete_dialog(agent))

        self._render_history(stream, agent.history)


    def _update_main(self, source: Literal["stream", "fact", "action"] = "stream") -> None:
        # show agent details, fact details, or action details

        match source:
            case "stream":
                # ON agent selected
                # create agent step history in self.main
                agent: Agent = self.get_selected_agent()
                if agent is None:
                    ui.markdown("No agent selected")
                    return

                self._agent_details(agent)

            case "fact":
                # ON fact selected
                # create fact details in self.main
                fact: Fact = self.get_selected_fact()
                if fact is None:
                    ui.markdown("No fact selected")
                    return

                self._fact_details(fact)

            case "action":
                # ON action selected
                # create action details in self.main
                action: Action = self.get_selected_action()
                if action is None:
                    ui.markdown("No action selected")
                    return

                self._action_details(action)

            case _:
                raise Exception("Invalid source")

    def _update_stream(self, content: Status | Thought | list[Fact] | ActionAttempt | Action | ActionArguments | ActionOutput | ActionWasSuccessful | Fact | Summary | IsFulfilled) -> None:
        # get stream element
        # raise exception if no stream element

        # agent status change
        # agent thought update
        # agent relevant facts update
        # agent action attempt update
        # agent action update
        # agent action arguments update
        # agent action output update
        # agent fact (is_successful) update
        # agent summary (is_fulfilled) update

        if isinstance(content, Status):
            # update stream color, append status text
            pass

        elif isinstance(content, Thought):
            # add thought expansion
            pass

        elif isinstance(content, list) and all(isinstance(each, Fact) for each in content):
            # fact previews, click to open details, make navigable
            # https://github.com/zauberzeug/nicegui/tree/main/examples%2Fmodularization
            pass

        elif isinstance(content, ActionAttempt):
            pass
            # add attempt

        elif isinstance(content, Action):
            # add action
            pass

        elif isinstance(content, ActionArguments):
            # add arguments
            pass

        elif isinstance(content, ActionOutput):
            # add output
            pass

        elif isinstance(content, ActionWasSuccessful):
            pass
            # update action successful

        elif isinstance(content, Fact):
            # add new fact
            pass

        elif isinstance(content, Summary):
            # add summary
            pass

        elif isinstance(content, IsFulfilled):
            pass
            # update fulfilled

        else:
            raise Exception(f"Invalid element type {type(content)}")

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
