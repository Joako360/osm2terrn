"""
Refactored menu system using dataclasses, MenuOption class, decoupled actions,
separated rendering, and semantic internal IDs.
"""
from __future__ import annotations

from typing import Optional, Any, Dict
from enum import Enum

from osm2terrn.cli.components import MenuOption, MenuRenderer
from osm2terrn.cli.commands import dlcity, exit_program, export, load


class MainMenuAction(Enum):
    """Enumeration of available menu actions."""
    DOWNLOAD_CITY = "download_city"
    LOAD_IMPORT = "load_import"
    EXPORT = "export"
    EXIT = "exit"
    CLEAR = "clear"


class Menu:
    """
    Enhanced menu system with semantic IDs, dataclasses, and separated rendering.
    """

    def __init__(
        self,
        title: str,
        options: list[MenuOption],
        renderer: Optional[MenuRenderer] = None
    ):
        """
        Initialize the menu.

        Args:
            title: Menu title
            options: List of menu options
            renderer: Menu renderer instance (created if None)
        """
        self.title = title
        self.options = options
        self.renderer = renderer or MenuRenderer()

        # Create lookup dictionaries for efficient access
        self._key_to_option: Dict[str, MenuOption] = {
            option.display_key: option for option in options
        }
        self._action_to_option: Dict[MainMenuAction, MenuOption] = {
            option.action_id: option for option in options
        }

    def get_option_by_key(self, key: str) -> Optional[MenuOption]:
        """Get menu option by display key."""
        return self._key_to_option.get(key)

    def get_option_by_action(self, action: MainMenuAction) -> Optional[MenuOption]:
        """Get menu option by action ID."""
        return self._action_to_option.get(action)

    def show(self) -> None:
        """Display the menu."""
        self.renderer.render_menu(self.title, self.options)

    def run_once(self) -> Optional[MainMenuAction]:
        """
        Run the menu once and return the selected action.
        Does not loop - just processes one selection.

        Returns:
            Selected MainMenuAction, or None if invalid selection
        """
        self.show()
        choice = self.renderer.get_user_input("Choose an option:")

        option = self.get_option_by_key(choice)
        if option:
            try:
                option.execute()
                return option.action_id
            except Exception as e:
                self.renderer.render_error(f"Error executing option: {e}")
                return None
        else:
            self.renderer.render_error(f"'{choice}' is not a valid option")
            return None

    def run(self) -> None:
        """Run the menu in a loop until exit or valid action."""
        while True:
            result = self.run_once()
            if result == MainMenuAction.EXIT:
                break
            elif result is None:
                # Invalid selection, continue loop
                self.renderer.get_user_input("Press enter to continue...")

    def execute_action(self, action: MainMenuAction) -> Any:
        """
        Execute a specific action by ID without showing the menu.

        Args:
            action: Action to execute

        Returns:
            Result of the action execution

        Raises:
            ValueError: If action not found or disabled
        """
        option = self.get_option_by_action(action)
        if not option:
            raise ValueError(f"Action {action.value} not found in menu")
        return option.execute()


# Create main menu options with semantic IDs
main_menu_options = [
    MenuOption(
        action_id=MainMenuAction.DOWNLOAD_CITY,
        display_key="1",
        label="Download City",
        action=dlcity,
        description="Download OSM data for a city",
        icon="🏙️"
    ),
    MenuOption(
        action_id=MainMenuAction.LOAD_IMPORT,
        display_key="2",
        label="Load/Import",
        action=load,
        description="Load or import existing data",
        icon="📁"
    ),
    MenuOption(
        action_id=MainMenuAction.EXPORT,
        display_key="3",
        label="Export",
        action=export,
        description="Export processed data",
        icon="💾"
    ),
    MenuOption(
        action_id=MainMenuAction.EXIT,
        display_key="4",
        label="Exit",
        action=exit_program,
        description="Exit the application",
        icon="🚪"
    ),
]

# Create main menu instance
mainmenu = Menu("Main Menu", main_menu_options)
