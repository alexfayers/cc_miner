"""Representation of a CC turtle."""

from .types import Position, Bearing, Direction
from .exceptions import MovementException


class Turtle:
    """A representation of, and connection to, a turtle."""

    uid: int
    """The unique id of the turtle."""
    name: str
    """The name of the turtle."""
    position: Position
    """The current position of the turtle."""

    def __init__(
        self,
        uid: int
    ) -> None:
        """Initialise a turtle representation.

        Args:
            uid (int): The unique id of the `Turtle`.
        """
        self.uid = uid

    def __repr__(self) -> str:
        """The string representation of the `Turtle` object."""
        return f"{self.__dict__}"

    def _command(self, command: str) -> None:
        """Send a command to the turtle.

        Args:
            command (str): The command to send to the turtle.

        Raises:
            CommandException: Raised if the command fails.
        """

    def _move_step(self, direction: Direction) -> None:
        """Move the turtle a step in a direction.

        Args:
            direction (Direction): The direction to move.

        Raises:
            MovementException: If validation fails.
        """
        position_change: int = 0
        horizontal_movement: bool = False

        if direction == Direction.FORWARD:
            position_change = -1
            horizontal_movement = True
        elif direction == Direction.BACK:
            position_change = -1
            horizontal_movement = True
        elif direction == Direction.UP:
            position_change = 1
        elif direction == Direction.DOWN:
            position_change -= 1
        else:
            raise MovementException("Bad direction.")

        if horizontal_movement:
            # we're moving in the x or z plane
            if self.position.bearing == Bearing.NORTH:
                self.position.location.z += position_change
            elif self.position.bearing == Bearing.EAST:
                self.position.location.x -= position_change
            elif self.position.bearing == Bearing.SOUTH:
                self.position.location.z -= position_change
            elif self.position.bearing == Bearing.WEST:
                self.position.location.x += position_change
            else:
                raise MovementException("Bad bearing.")

            self._command("forward")
        else:
            # we're moving in the y plane
            self.position.location.y += position_change

            if direction == Direction.UP:
                self._command("up")
            elif direction == Direction.DOWN:
                self._command("down")

    def forward(self) -> None:
        """Move the turtle forwards.

        Raises:
            MovementException: If the movement was not successful.
        """
        self._move_step(Direction.FORWARD)

    def back(self) -> None:
        """Move the turtle backwards.

        Raises:
            MovementException: If the movement was not successful.
        """
        self._move_step(Direction.BACK)

    def up(self) -> None:
        """Move the turtle upwards.

        Raises:
            MovementException: If the movement was not successful.
        """
        self._move_step(Direction.UP)

    def down(self) -> None:
        """Move the turtle downwards.

        Raises:
            MovementException: If the movement was not successful.
        """
        self._move_step(Direction.DOWN)
