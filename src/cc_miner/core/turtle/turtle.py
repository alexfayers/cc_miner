"""Representation of a CC turtle."""

import logging
from typing import Any, Dict, cast

from websockets.server import WebSocketServerProtocol

from ...socket.types import CommandMessage, CommandResponse
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

    async def _command(self, command: str) -> CommandResponse:
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
        res = CommandResponse.parse_raw(res_raw)
        if res.status is True:
            self._logger.info("Command successful")
        else:
            self._logger.error("Command failed")
        return res

    async def move(self, direction: Direction) -> None:
        """Move the turtle a step in a direction.

        Args:
            direction (Direction): The direction to move.

        Raises:
            MovementException: If validation fails.
        """
        position_change: int = 0
        horizontal_movement: bool = False

        if direction == Direction.FORWARD:
            self._logger.info("Moving forward")
            position_change = -1
            horizontal_movement = True
        elif direction == Direction.BACK:
            self._logger.info("Moving back")
            position_change = 1
            horizontal_movement = True
        elif direction == Direction.UP:
            self._logger.info("Moving up")
            position_change = 1
        elif direction == Direction.DOWN:
            self._logger.info("Moving down")
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

    async def dig(self, direction: Direction) -> None:
        """Mine the block directly in front of the turtle.

        Args:
            direction (Direction): The direction to mine.

        Raises:
            MovementException: If the movement was not successful.
        """
        if direction == Direction.FORWARD:
            self._logger.info("Digging in front")
            await self._command("return turtle.dig()")
        elif direction == Direction.DOWN:
            self._logger.info("Digging below")
            await self._command("return turtle.digDown()")
        elif direction == Direction.UP:
            self._logger.info("Digging above")
            await self._command("return turtle.digUp()")
        else:
            raise CommandException("Bad direction.")

    async def inspect(self, direction: Direction) -> Dict[str, Any]:
        """Inspect the block directly in front of the turtle.

        Args:
            direction (Direction): The direction to mine.

        Raises:
            MovementException: If the movement was not successful.

        Returns:
            Dict: The block metadata
        """
        if direction == Direction.FORWARD:
            self._logger.info("Inspecting in front")
            res = await self._command("return turtle.inspect()")
        elif direction == Direction.DOWN:
            self._logger.info("Inspecting below")
            res = await self._command("return turtle.inspectDown()")
        elif direction == Direction.UP:
            self._logger.info("Inspecting above")
            res = await self._command("return turtle.inspectUp()")
        else:
            raise CommandException("Bad direction.")

        if res.status:
            return cast(Dict[str, Any], res.data)
        else:
            return {}

    async def step(self) -> None:
        """A single step of the mining process."""
        check_directions = [Direction.FORWARD, Direction.UP]

        for direction in check_directions:
            data = await self.inspect(direction)
            logger.debug(data)
            if data.get("tags", {}).get("minecraft:mineable/pickaxe", False) is True:
                logger.debug("Block is mineable")
                await self.dig(direction)

        await self.move(Direction.FORWARD)

    async def start(self) -> None:
        """The main turtle process."""
        for _ in range(16):
            await self.step()
