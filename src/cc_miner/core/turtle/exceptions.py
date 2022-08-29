"""`Turtle` related exceptions."""


class TurtleException(Exception):
    """An error to do with a `Turtle`."""


class MovementException(Exception):
    """An error to do with a `Turtle` movement."""


class CommandException(Exception):
    """An error to do with a command that was sent to a `Turtle`."""


class HaltException(Exception):
    """Called when a `Turtle` halts itself (e.g. if there isn't enough fuel etc.)."""
