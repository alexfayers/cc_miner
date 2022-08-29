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
        self.position.bearing = Bearing(
            (self.position.bearing.value - 1) % len(Bearing)
        )
        self._logger.info("Turning left")
        await self._command("return turtle.turnLeft()")

    async def turn_right(self) -> None:
        """Turn the turtle right.

        Raises:
            MovementException: If the movement was not successful.
        """
        self.position.bearing = Bearing(
            (self.position.bearing.value + 1) % len(Bearing)
        )
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

    async def dig_if_block(self, direction: Direction) -> None:
        """Dig a block if there's something there."""
        if direction == Direction.BACK:
            raise MovementException("Can't dig backwards.")

        data = await self.inspect(direction)
        logger.debug(data)
        tags = data.get("tags", {})
        if any(
            tags.get(item, False) is True
            for item in ["minecraft:mineable/pickaxe", "minecraft:mineable/shovel"]
        ):
            logger.debug("Block is mineable")
            await self.dig(direction)

    async def dig_move(self, direction: Direction) -> None:
        """Move and dig if there's a block in the way."""
        await self.dig(direction)
        await self.move(direction)

    async def move_to_location(
        self, location: Location, cost_calculation: bool = False
    ) -> int:
        """Move the turtle to a location.

        Args:
            location (Location): The location to move to.
            cost_calculation (bool): If true, don't actually move.

        Returns:
            int: The number of blocks moved/that will be moved.
        """
        movement_cost: int = 0

        x_diff = location.x - self.position.location.x
        y_diff = location.y - self.position.location.y
        z_diff = location.z - self.position.location.z

        for _ in range(abs(y_diff)):
            if not cost_calculation:
                if y_diff > 0:
                    await self.dig_move(Direction.UP)
                else:
                    await self.dig_move(Direction.DOWN)
            movement_cost += 1

        # turn right until we're facing the right way
        # TODO: optimise by calculating the difference between the bearings
        if not cost_calculation:
            if x_diff > 0:
                while self.position.bearing != Bearing.EAST:
                    await self.turn_right()
            else:
                while self.position.bearing != Bearing.WEST:
                    await self.turn_right()

        for _ in range(abs(x_diff)):
            if not cost_calculation:
                await self.dig_move(Direction.FORWARD)
            movement_cost += 1

        if not cost_calculation:
            if z_diff > 0:
                while self.position.bearing != Bearing.SOUTH:
                    await self.turn_right()
            else:
                while self.position.bearing != Bearing.NORTH:
                    await self.turn_right()

        for _ in range(abs(z_diff)):
            if not cost_calculation:
                await self.dig_move(Direction.FORWARD)
            movement_cost += 1

        return movement_cost

    async def start(self) -> None:
        """The main turtle process."""
        steps = await self.move_to_location(
            Location(
                x=1,
                y=4,
                z=0,
            ),
            cost_calculation=True,
        )

        print(steps)

        # xz_size = 4
        # y_size = 10

        # for _ in range(y_size + 1):
        #     for row_number in range(xz_size):
        #         for _ in range(xz_size - 1):
        #             await self.dig_move(Direction.FORWARD)
        #         # turn to next row
        #         if row_number < (xz_size - 1):
        #             if row_number % 2 == 0:
        #                 await self.turn_right()
        #                 await self.dig_move(Direction.FORWARD)
        #                 await self.turn_right()
        #             else:
        #                 await self.turn_left()
        #                 await self.dig_move(Direction.FORWARD)
        #                 await self.turn_left()
        #     if xz_size % 2 == 0:
        #         await self.turn_right()
        #     else:
        #         await self.turn_left()

        #     await self.dig_move(Direction.DOWN)
