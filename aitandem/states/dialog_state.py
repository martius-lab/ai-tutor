"""This file manages the state for the popup dialog component
It provides functionality to track whether the dialog is open or not
"""

import reflex as rx


class DialogState(rx.State):
    """Represents the state of a dialog component
    Attributes:
        opened (bool): Indicates whether the dialog is currently open
    """

    opened: bool = False

    @rx.event
    def set_opened(self, value: bool):
        """Updates the dialog state
        Args:
            value (bool): A flag indicating whether the dialog is open (True)
            or closed (False)
        This function sets the `opened` attribute to the given value
        """
        self.opened = value
