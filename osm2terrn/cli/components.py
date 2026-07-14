"""
Unified menu components that can be used across modules.
Separated to avoid circular imports.
"""
from dataclasses import dataclass
from typing import Callable, Optional, Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table


@dataclass
class MenuOption:
    """
    Represents a single menu option with semantic ID, display properties, and action.

    Attributes:
        action_id: Semantic identifier for the option (can be any Enum or string)
        display_key: Key shown to user (e.g., '1', '2', 'a', 'b')
        label: Human-readable description
        action: Callable to execute when selected (optional, None for options that don't have immediate actions)
        style: Rich style for the option text
        enabled: Whether this option is currently available
        description: Optional detailed description
        icon: Optional icon/emoji to display with the option
    """
    action_id: Any
    display_key: str
    label: str
    action: Optional[Callable[[], Any]] = None
    style: str = "cyan"
    enabled: bool = True
    description: Optional[str] = None
    icon: Optional[str] = None

    def get_display_text(self) -> str:
        """Get the formatted display text for this option."""
        icon_text = f"{self.icon} " if self.icon else ""
        if self.enabled:
            return f"[{self.style}]{self.display_key}.[/{self.style}] {icon_text}{self.label}"
        else:
            return f"[dim]{self.display_key}. {icon_text}{self.label}[/dim]"

    def execute(self) -> Any:
        """Execute the action associated with this option."""
        if not self.enabled:
            raise ValueError(f"Option {self.action_id} is disabled")
        if self.action:
            return self.action()
        return None


class MenuRenderer:
    """
    Handles rendering of menus using Rich components.
    Separated from menu logic for better modularity.
    Provides generic rendering methods for panels, tables, and user interaction.
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def render_panel(self, content: str, title: str, border_style: str = "magenta") -> None:
        """
        Render a generic panel with content.

        Args:
            content: Panel content text
            title: Panel title
            border_style: Rich style for panel border
        """
        self.console.print()
        panel = Panel(
            content,
            title=f"[bold {border_style}]{title}[/bold {border_style}]",
            border_style=border_style,
            expand=False,
        )
        self.console.print(panel)

    def render_table(self, title: str, columns: list[tuple], rows: list[tuple], 
                    header_style: str = "bold magenta") -> None:
        """
        Render a generic table.

        Args:
            title: Table title
            columns: List of tuples (column_name, style, width, justify)
                    e.g., [("Option", "cyan", 6, "center"), ("Name", "white", 50)]
            rows: List of tuples representing rows with style
                  e.g., [("1", "Item", style="green"), ...]
        """
        table = Table(title=title, show_header=True, header_style=header_style)
        
        for col_name, col_style, col_width, col_justify in columns:
            table.add_column(col_name, style=col_style, width=col_width, justify=col_justify)
        
        for row in rows:
            table.add_row(*row[:-1], style=row[-1] if len(row) > 1 else None)
        
        self.console.print(table)

    def render_menu(self, title: str, options: list[MenuOption], border_style: str = "magenta") -> None:
        """
        Render a menu with the given options.

        Args:
            title: Menu title
            options: List of menu options to display
            border_style: Rich style for panel border
        """
        # Create menu options text
        options_text = "\n".join([option.get_display_text() for option in options])
        self.render_panel(options_text, title, border_style)

    def render_error(self, message: str) -> None:
        """Render an error message."""
        error_text = Text(message, style="bold red")
        self.console.print(error_text)

    def render_info(self, message: str, style: str = "yellow") -> None:
        """Render an informational message."""
        info_text = Text(message, style=style)
        self.console.print(info_text)

    def render_warning(self, message: str) -> None:
        """Render a warning message."""
        self.console.print(f"[yellow]{message}[/yellow]")

    def get_user_input(self, prompt: str, style: str = "bold cyan") -> str:
        """Get user input with styled prompt."""
        return self.console.input(f"[{style}]{prompt}[/{style}] ").strip()
