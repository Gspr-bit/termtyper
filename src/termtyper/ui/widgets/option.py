from typing import Callable
from rich.box import HEAVY
from rich.console import RenderableType
from textual import events
from textual.widget import Widget
from rich.align import Align
from rich.text import Span, Text
from rich.panel import Panel

from ...utils import Parser


class Option(Widget):
    """
    A widget to show options in horizontal fashion
    with the selected option with a colored background
    """

    def __init__(
        self, name: str, options: list[str], callback: Callable = lambda: None
    ) -> None:
        super().__init__()
        self.name = name
        self.options = [i.strip() for i in options]
        self.cursor = self.options.index(Parser().get_data(self.name))
        self.callback = callback
        self.selected = False
        self._set_option_string()

    def highlight(self) -> None:
        self.selected = True
        self.refresh()

    def lowlight(self) -> None:
        self.selected = False
        self.refresh()

    def _set_option_string(self) -> None:
        """
        Sets the renderable for viewing
        """

        m = max(len(i) for i in self.options) + 4  # 4 for nice padding
        self.options_string = "|".join(i.center(m) for i in self.options)
        self.positions = [
            [i, i + m - 2] for i in range(1, len(self.options_string), m + 1)
        ]

    def update(self) -> None:
        Parser().set_data(self.name, self.options[self.cursor])

        if self.callback:
            self.callback()

        self.refresh()

    def select_next_option(self) -> None:
        self.cursor = (self.cursor + 1) % len(self.options)
        self.update()

    def select_prev_option(self) -> None:
        self.cursor = (self.cursor - 1 + len(self.options)) % len(self.options)
        self.update()

    async def on_mouse_scroll_down(self, _: events.MouseScrollDown) -> None:
        self.select_next_option()

    async def on_mouse_scroll_up(self, _: events.MouseScrollUp) -> None:
        self.select_prev_option()

    def render(self) -> RenderableType:
        return Panel(
            Align.center(
                Text(
                    self.options_string,
                    spans=[
                        Span(
                            self.positions[self.cursor][0],
                            self.positions[self.cursor][1],
                            "reverse green",
                        )
                    ],
                ),
                vertical="middle",
            ),
            border_style="magenta" if self.selected else "white",
            box=HEAVY,
        )


if __name__ == "__main__":
    from textual.app import App

    class MyApp(App):
        async def on_mount(self):
            await self.view.dock(
                Option("test", ["Linux", "MacPriceyOS", "YourPCRanIntoAnError"])
            )

    MyApp.run()
