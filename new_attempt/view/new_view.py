# coding=utf-8
from nicegui import ui


# coding=utf-8
class View:
    def __init__(self) -> None:
        self.header = None
        self.left_drawer = None
        self.main = None
        self.right_drawer = None
        self.footer = None

    @staticmethod
    def modify_page() -> None:
        ui.query('#c0').classes("h-screen")
        ui.query('#c1').classes("h-full")
        ui.query('#c2').classes("h-full")
        ui.query('#c3').classes("h-full")

    def create_header(self) -> ui.header:
        with ui.header() as header:
            pass
        return header

    def create_left_drawer(self) -> ui.drawer:
        with ui.left_drawer() as left_drawer:
            pass
        return left_drawer

    def create_main(self) -> ui.element:
        with ui.row() as row:
            pass
        return row

    def create_right_drawer(self) -> ui.drawer:
        with ui.right_drawer() as right_drawer:
            pass
        return right_drawer

    def create_footer(self) -> ui.footer:
        with ui.footer() as footer:
            pass
        return footer

    def run(self) -> None:
        View.modify_page()
        self.header = self.create_header()
        self.left_drawer = self.create_left_drawer()
        self.main = self.create_main()
        self.right_drawer = self.create_right_drawer()
        self.footer = self.create_footer()
        pass

