"""Representation of a CC turtle."""

import json
import logging
from typing import Any, Dict

from websockets.server import WebSocketServerProtocol

from ...socket.types import CommandMessage, StatusMessage
from .exceptions import CommandException, MovementException
from .types import Bearing, Direction, Location, Position

logger = logging.getLogger(__name__)


class Turtle:
    """A representation of, and connection to, a turtle."""

    uid: int
    """The unique id of the turtle."""
    socket: WebSocketServerProtocol
    """The websocket connection to the turtle."""
    name: str = ""
    """The name of the turtle."""
    _position: Position
    """The (internal) current position of the turtle."""
    _logger: logging.Logger
    """The logger for the class."""

    def __init__(self, uid: int, socket: WebSocketServerProtocol) -> None:
        """Initialise a turtle representation.

        Args:
            uid (int): The unique id of the `Turtle`.
            socket (WebSocketServerProtocol): The websocket connection to the turtle.
        """
        self._position = Position(
            location=Location(x=0, y=0, z=0), bearing=Bearing.NORTH
        )
        self.uid = uid
        self.socket = socket
        self._logger = logging.getLogger(f"{__name__}.{self.uid}")

    def __repr__(self) -> str:
        """The string representation of the `Turtle` object."""
        return f"{self.__dict__}"

    async def _command(self, command: str) -> Any:
        """Send a command to the turtle.

        Args:
            command (str): The command to send to the turtle.

        Raises:
            CommandException: Raised if the command fails.

        Returns:
            Any: The result of the command. Type depends on what the command returns - check the docs!.
        """
        if "return" not in command:
            raise CommandException("Command must return a value.")

        self._logger.debug("Sending command: %s", command)
        await self.socket.send(CommandMessage(command=command).json())
        res_raw = await self.socket.recv()
        self._logger.debug("Received response: %s", res_raw)
        res = StatusMessage.parse_raw(res_raw)
        if res.status == "OK":
            self._logger.info("Command successful")
            return res.data
        elif res.status == "ERROR":
            raise CommandException(f"Command returned with {res.status}: {res.data}")
        else:
            raise CommandException(
                f"Command returned with unknown status: {res.status}"
            )

    async def _move_step(self, direction: Direction) -> None:
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
            position_change = 1
            horizontal_movement = True
        elif direction == Direction.UP:
            position_change = 1
        elif direction == Direction.DOWN:
            position_change = -1
        else:
            raise MovementException("Bad direction.")

        if horizontal_movement:
            # we're moving in the x or z plane
            if self.position.bearing in [Bearing.NORTH, Bearing.SOUTH]:
                self.position.location.z += position_change

            elif self.position.bearing in [Bearing.WEST, Bearing.EAST]:
                self.position.location.x += position_change

            else:
                raise MovementException("Bad bearing.")

            if direction == Direction.FORWARD:
                await self._command("return turtle.forward()")
            elif direction == Direction.BACK:
                await self._command("return turtle.back()")
        else:
            # we're moving in the y plane
            self.position.location.y += position_change

            if direction == Direction.UP:
                await self._command("return turtle.up()")
            elif direction == Direction.DOWN:
                await self._command("return turtle.down()")

    @property
    def position(self) -> Position:
        """The current position of the `Turtle`."""
        # TODO: use commands/gps to get position
        return self._position

    @position.setter
    def position(self, value: Position) -> None:
        self._position = value

    async def forward(self) -> None:
        """Move the turtle forwards.

        Raises:
            MovementException: If the movement was not successful.
        """
        self._logger.info("Moving forward")
        await self._move_step(Direction.FORWARD)

    async def back(self) -> None:
        """Move the turtle backwards.

        Raises:
            MovementException: If the movement was not successful.
        """
        self._logger.info("Moving back")
        await self._move_step(Direction.BACK)

    async def up(self) -> None:
        """Move the turtle upwards.

        Raises:
            MovementException: If the movement was not successful.
        """
        self._logger.info("Moving up")
        await self._move_step(Direction.UP)

    async def down(self) -> None:
        """Move the turtle downwards.

        Raises:
            MovementException: If the movement was not successful.
        """
        self._logger.info("Moving down")
        await self._move_step(Direction.DOWN)

    async def turn_left(self) -> None:
        """Turn the turtle left.

        Raises:
            MovementException: If the movement was not successful.
        """
        self._logger.info("Turning left")
        await self._command("return turtle.turnLeft()")

    async def turn_right(self) -> None:
        """Turn the turtle right.

        Raises:
            MovementException: If the movement was not successful.
        """
        self._logger.info("Turning right")
        await self._command("return turtle.turnRight()")

    async def dig(self) -> None:
        """Mine the block directly in front of the turtle.

        Raises:
            MovementException: If the movement was not successful.
        """
        self._logger.info("Digging")
        await self._command("return turtle.dig()")

    async def inspect(self) -> Dict[str, Any]:
        """Inspect the block directly in front of the turtle.

        Raises:
            MovementException: If the movement was not successful.

        Returns:
            Dict: The block metadata
        """
        self._logger.info("Inspecting")
        data: Dict[str, Any] = await self._command("return turtle.inspect()")
        return data

    async def start(self) -> None:
        """The main turtle process."""
        data = await self.inspect()
        logger.debug(data)
        if data.get("minecraft:mineable/pickaxe") is True:
            logger.debug("Block is mineable")
            await self.dig()

        await self.forward()
