from rich.align import Align
from rich.box import HEAVY_EDGE
from rich.text import Text
from textual.app import App
from textual.layouts.dock import DockLayout
from textual.widgets import Static
from textual import events

from rich.panel import Panel
from os import get_terminal_size as termsize

from .settings_options import menu
from ..ui.widgets import (
    Button,
    RaceHUD,
    Screen,
    UpdateRaceHUD,
    ResetHUD,
    ButtonSelect,
    ButtonClicked,
)
from ..utils import Parser, HELP_BANNER, HELP_MESSAGE


def percent(part, total):
    return int(part * total / 100)


welcome_message = """
┬ ┬┌─┐┬  ┌─┐┌─┐┌┬┐┌─┐  ┌┬┐┌─┐  ┌┬┐┌─┐┬─┐┌┬┐┌┬┐┬ ┬┌─┐┌─┐┬─┐  ┬
│││├┤ │  │  │ ││││├┤    │ │ │   │ ├┤ ├┬┘│││ │ └┬┘├─┘├┤ ├┬┘  │
└┴┘└─┘┴─┘└─┘└─┘┴ ┴└─┘   ┴ └─┘   ┴ └─┘┴└─┴ ┴ ┴  ┴ ┴  └─┘┴└─  o
"""


class TermTyper(App):
    async def on_load(self) -> None:
        self.parser = Parser()
        self.current_space = "main_menu"
        self.x, self.y = termsize()

        # FOR MAIN MENU
        self.banner = Static(
            Panel(
                Align.center(
                    Text(welcome_message, style="bold blue"), vertical="middle"
                ),
                style="black",
                border_style="magenta",
                box=HEAVY_EDGE,
            )
        )
        self.bt_typing_space = Button(
            label="Start Typing !".center(30),
            name="bt_typing_space",
        )
        self.bt_settings = Button(label="Settings".center(30), name="bt_settings")
        self.bt_quit = Button(label="Quit".center(30), name="bt_quit")

        self.current_button_index = 0
        self.bt_typing_space.select()
        self.buttons = [self.bt_typing_space, self.bt_settings, self.bt_quit]

        # FOR SETTINGS
        self.menus = list(menu.keys())
        self.current_menu_index = 0

        # TYING SCREEN
        self.typing_screen = Screen()

    async def on_mount(self) -> None:
        await self.load_main_menu()

    async def clear_screen(self) -> None:
        """
        Removes all the widgets and clears the window
        """

        if isinstance(self.view.layout, DockLayout):
            self.view.layout.docks.clear()
        self.view.widgets.clear()

    async def load_help_menu(self):
        await self.clear_screen()
        await self.view.dock(HELP_BANNER, size=percent(25, self.y))
        await self.view.dock(HELP_MESSAGE)
        self.current_space = "help_menu"

    async def load_main_menu(self) -> None:
        """
        Renders the Main Menu
        """

        await self.clear_screen()
        await self.view.dock(self.banner, size=percent(30, self.y))
        await self.view.dock(
            self.bt_typing_space,
            self.bt_settings,
            self.bt_quit,
            size=percent(25, self.y),
        )
        self.current_space = "main_menu"

    async def load_settings(self):
        """
        Renders the Settings
        """

        await self.clear_screen()

        self.current_menu = self.menus[self.current_menu_index]
        await self.view.dock(
            Static(
                Panel(
                    Align.center(
                        Text(menu[self.current_menu].ascii_art, style="bold blue"),
                        vertical="middle",
                    ),
                    style="black",
                    border_style="bold magenta",
                    title="Press ctrl+h for help",
                    title_align="right",
                    subtitle_align="right",
                )
            ),
            size=percent(20, self.y),
        )

        item_count = len(menu[self.current_menu].items)
        grid = await self.view.dock_grid(gutter=(1, 1))
        grid.add_column("desc", fraction=2)
        grid.add_column("value")
        grid.add_row("row", repeat=item_count)

        count = item_count + 1
        grid.add_areas(**{f"item{i}": f"desc,row{i}" for i in range(1, count)})
        grid.add_areas(**{f"val{i}": f"value,row{i}" for i in range(1, count)})

        grid.place(
            **{
                f"item{i}": Static(
                    Panel(
                        Align.left(
                            menu[self.current_menu].items[i - 1].description,
                            vertical="middle",
                        )
                    )
                )
                for i in range(1, count)
            }
        )
        grid.place(
            **{
                f"val{i}": menu[self.current_menu].items[i - 1].widget
                for i in range(1, count)
            }
        )

        self.current_space = "settings"

    async def load_typing_space(self) -> None:
        """
        Renders the Typing Space
        """

        self.race_hud = RaceHUD()
        await self.typing_screen._refresh_settings()
        await self.clear_screen()

        self.current_space = "typing_space"
        await self.view.dock(self.race_hud, size=percent(30, self.y))
        await self.view.dock(self.typing_screen)

    async def on_resize(self, _: events.Resize) -> None:
        """
        Re renders the screen when the terminal is resized
        """
        # Update the x and y variables with the new terminal size
        self.x, self.y = termsize()
        await eval(f"self.load_{self.current_space}()")

    async def on_key(self, event: events.Key) -> None:
        if self.current_space == "help_menu":
            if event.key in ["ctrl+h", "escape"]:
                await self.load_settings()

        elif self.current_space == "main_menu":
            match event.key:
                case "j" | "down":
                    self.current_button_index = (self.current_button_index + 1) % 3

                case "k" | "up":
                    self.current_button_index = (self.current_button_index - 1 + 3) % 3

                case "enter":
                    button = self.buttons[self.current_button_index]
                    await button.emit(ButtonClicked(button))

                case _:
                    return

            button = self.buttons[self.current_button_index]
            await button.emit(ButtonSelect(button))

        elif self.current_space == "settings":
            match event.key:
                case "ctrl+h":
                    await self.load_help_menu()

                case "ctrl+i":
                    self.current_menu_index = (self.current_menu_index + 1) % len(menu)
                    await self.load_settings()

                case "shift+tab":
                    self.current_menu_index = (
                        self.current_menu_index + len(menu) - 1
                    ) % len(menu)
                    await self.load_settings()

                case "j" | "down":
                    menu[self.current_menu].select_next_setting()

                case "k" | "up":
                    menu[self.current_menu].select_prev_setting()

                case "h" | "left":
                    menu[self.current_menu].select_prev_setting_option()

                case "l" | "right":
                    menu[self.current_menu].select_next_setting_option()

                case "escape":
                    await self.load_main_menu()

        elif self.current_space == "typing_space":
            if event.key == "escape":
                await self.typing_screen.reset_screen()
                await self.load_main_menu()
                return

            await self.typing_screen.key_add(event.key)

    async def handle_reset_hud(self, _: ResetHUD) -> None:
        self.race_hud.reset()

    async def handle_update_race_hud(self, event: UpdateRaceHUD) -> None:
        self.race_hud.update(event.completed, event.speed, event.accuracy)

    async def handle_button_select(self, event: ButtonSelect):
        for button in self.buttons:
            if button.name != getattr(event.sender, "name"):
                button.deselect()
            else:
                button.select()

            button.refresh()

    async def handle_button_clicked(self, e: events.Click):
        if getattr(e.sender, "name") == "bt_quit":
            await self.action_quit()
        elif getattr(e.sender, "name") == "bt_settings":
            await self.load_settings()
        elif getattr(e.sender, "name") == "bt_typing_space":
            await self.load_typing_space()
