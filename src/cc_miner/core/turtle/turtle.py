"""Representation of a CC turtle."""

import logging
from typing import Any, Dict, List, cast

from overrides import EnforceOverrides, overrides
from websockets.server import WebSocketServerProtocol

from ..._helper import SuccessLogger
from ...socket.types import CommandMessage, CommandResponse
from .exceptions import (
    CommandException,
    HaltException,
    InteractionException,
    InventoryException,
    MovementException,
)
from .types import Bearing, Direction, InventorySlotInfo, Location, Position

logger = cast(SuccessLogger, logging.getLogger(__name__))


FUEL_LIMIT = 20000


class Turtle(EnforceOverrides):
    """A representation of, and connection to, a turtle."""

    uid: int
    """The unique id of the turtle."""
    socket: WebSocketServerProtocol
    """The websocket connection to the turtle."""
    name: str = ""
    """The name of the turtle."""
    _position: Position
    """The (internal) current position of the turtle."""
    _logger: SuccessLogger
    """The logger for the class."""
    _check_fuel = True
    """If true, will check for fuel requirements before moving."""
    _home_location = Location(x=0, y=0, z=0)
    """The location that the `Turtle` will move to on completion."""
    _slot_range = range(1, 17)  # 1-16
    """The range of slots that can be used to store items."""
    _latest_command: str = ""
    """The latest command that the turtle has attempted to execute."""
    _latest_fuel: int = 0
    """The latest fuel level of the turtle."""
    _steps_from_home: int = 0
    """The amount of blocks away from home the turtle is."""
    _bad_blocks: List[str] = ["cobble", "dirt", "gravel"]
    """The list of block types to discard during mining."""
    _fuel_blocks: List[str] = ["coal"]
    """The list of block/item types to use for fuel."""

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
        self._logger = cast(SuccessLogger, logging.getLogger(f"{__name__}.{self.uid}"))

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

        self._latest_command = f"{command} (PENDING)"

        self._logger.debug("Sending command: %s", command)
        await self.socket.send(CommandMessage(command=command).json())
        res_raw = await self.socket.recv()
        self._logger.debug("Received response: %s", res_raw)
        res = CommandResponse.parse_raw(res_raw)
        if res.status is True:
            self._latest_command = f"{command} (SUCCESS)"
            self._logger.info("Command successful")
        else:
            self._latest_command = f"{command} (FAILURE)"
            self._logger.error("Command failed")
        return res

    async def check_fuel(self) -> None:
        """Check if the turtle has enough fuel to move."""
        fuel = await self.get_fuel()
        self._latest_fuel = fuel
        steps_to_get_back = await self.move_to_location(
            self._home_location, cost_calculation=True
        )
        self._steps_from_home = steps_to_get_back

        if steps_to_get_back >= fuel:
            self._logger.warning(
                "Won't have enough fuel to get back if we continue - stopping current process and returning!"
            )
            self._check_fuel = False
            await self.move_to_location(self._home_location)
            self._logger.warning(f"Stopped at {self.position.location}")
            raise HaltException("Returned before ran out of fuel.")

    async def move(self, direction: Direction) -> None:
        """Move the turtle a step in a direction.

        Args:
            direction (Direction): The direction to move.

        Raises:
            MovementException: If validation fails.
        """
        if self._check_fuel:
            await self.check_fuel()

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
            if self.position.bearing == Bearing.NORTH:
                self.position.location.z += position_change
            elif self.position.bearing == Bearing.SOUTH:
                self.position.location.z -= position_change

            elif self.position.bearing == Bearing.WEST:
                self.position.location.x += position_change
            elif self.position.bearing == Bearing.EAST:
                self.position.location.x -= position_change

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

        self._logger.debug("New position: %s", self.position)

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

    async def get_fuel(self) -> int:
        """Get the amount of fuel remaining in the turtle.

        Returns:
            int: The amount of fuel left.
        """
        res = await self._command("return turtle.getFuelLevel()")
        if res.status:
            return cast(int, res.data)
        else:
            raise CommandException("Failed to get fuel level.")

    async def dig_if_block(self, direction: Direction) -> None:
        """Dig a block if there's something there."""
        if direction == Direction.BACK:
            raise MovementException("Can't dig backwards.")

        data = await self.inspect(direction)
        self._logger.debug(data)
        tags = data.get("tags", {})
        if any(
            tags.get(item, False) is True
            for item in ["minecraft:mineable/pickaxe", "minecraft:mineable/shovel"]
        ):
            self._logger.debug("Block is mineable")
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

        if not cost_calculation:
            while self.position.bearing != Bearing.NORTH:
                await self.turn_right()

        return movement_cost

    async def inventory_dump(self, search: str, direction: Direction) -> None:
        """Drop any items that match a specific search string.

        Args:
            search (str): The item to search for.
            direction (Direction): The direction to search in.
        """
        try:
            await self.inventory_select(search)
        except InventoryException:
            self._logger.debug("Didn't drop %s", search)
            raise InventoryException("No items to drop.")

        # found item
        try:
            await self.drop_item(direction)
        except InteractionException:
            self._logger.debug("Couldn't drop %s", search)
            raise InventoryException("Failed to drop.")

        self._logger.info("Dropped %s", search)

    async def inventory_select(self, search: str) -> None:
        """Select an item from the turtle's inventory.

        Args:
            search (str): The search string.

        Raises:
            InventoryException: If the search item could not be found.
        """
        for slot in self._slot_range:
            res = await self._command(f"return turtle.getItemDetail({slot})")
            if res.data is None:
                # slot is empty
                continue

            details = InventorySlotInfo(**res.data)

            if search in details.name:
                self._logger.info(
                    f"Found {details.count} '{details.name}' in slot {slot} "
                    f"which matches search '{search}'"
                )
                await self._command(f"return turtle.select({slot})")
                return
        raise InventoryException("Could not find item.")

    async def place_block(self, direction: Direction) -> None:
        """Place the currently selected block in a direction.

        Args:
            direction (Direction): The direction to place the block.

        Raises:
            CommandException: If the direction was not valid.
        """
        if direction == Direction.FORWARD:
            self._logger.info("Placing in front")
            res = await self._command("return turtle.place()")
        elif direction == Direction.DOWN:
            self._logger.info("Placing below")
            res = await self._command("return turtle.placeDown()")
        elif direction == Direction.UP:
            self._logger.info("Placing above")
            res = await self._command("return turtle.placeUp()")
        else:
            raise CommandException("Bad direction.")

        if not res.status:
            raise InteractionException("Failed to place block.")

    async def drop_item(self, direction: Direction) -> None:
        """Drop the currently selected item in a direction.

        Args:
            direction (Direction): The direction to drop the item.

        Raises:
            CommandException: If the direction was not valid.
        """
        if direction == Direction.FORWARD:
            self._logger.info("Dropping in front")
            res = await self._command("return turtle.drop()")
        elif direction == Direction.DOWN:
            self._logger.info("Dropping below")
            res = await self._command("return turtle.dropDown()")
        elif direction == Direction.UP:
            self._logger.info("Dropping above")
            res = await self._command("return turtle.dropUp()")
        else:
            raise CommandException("Bad direction.")

        if not res.status:
            raise InteractionException("Failed to drop item.")

    async def refuel(self, target_fuel_level: int) -> None:
        """Refuel the turtle until the fuel level is above the threshold or the fuel sources run out.

        Args:
            target_fuel_level (int): The target fuel level.

        Raises:
            InventoryException: If the turtle has no fuel sources remaining.
            ValueError: If the target fuel level is not between 0 and 100.
        """
        if 0 < target_fuel_level < FUEL_LIMIT:
            raise ValueError(f"Target fuel level must be between 0 and {FUEL_LIMIT}.")

        for fuel_type in self._fuel_blocks:
            while True:
                try:
                    await self.inventory_select(fuel_type)
                except InventoryException:
                    self._logger.debug("No more %s", fuel_type)
                    break

                await self._command("return turtle.refuel()")

                fuel = await self.get_fuel()

                if fuel > target_fuel_level or fuel >= FUEL_LIMIT:
                    self._logger.info(
                        "Fuel level is above the threshold of %s.", target_fuel_level
                    )
                    return
        # double check fuel
        fuel = await self.get_fuel()

        if fuel > target_fuel_level or fuel >= FUEL_LIMIT:
            self._logger.info(
                "Fuel level is above the threshold of %s.", target_fuel_level
            )
            return

        raise InventoryException("Not enough fuel.")

    async def get_status(self) -> str:
        """Create a status update string."""
        status_string = f"""
            Position:        {self.position.location}
            Fuel:            {self._latest_fuel}
            Latest Command:  {self._latest_command}
            Blocks from Home: {self._steps_from_home}
        """

        status_string_clean = ""

        for line in status_string.splitlines():
            status_string_clean += line.strip() + "\n"

        return status_string_clean

    async def _process_complete(self) -> None:
        """Called on completion of processing."""
        self._check_fuel = False
        self._logger.success("Processing complete, returning home.")
        await self.move_to_location(self._home_location)

    async def start(self) -> None:
        """The main turtle process.

        Must be overridden in subclasses.
        """
        raise NotImplementedError("Turtle.start() not implemented.")


class QuarryTurtle(Turtle):
    """A turtle that can mine a quarry."""

    @overrides
    async def start(self) -> None:
        """The main turtle process."""
        # width of the quarry
        xz_size = 8
        # height of the quarry
        y_size = 10
        # check if enough fuel before mining
        prerun_fuel_check: bool = False

        if prerun_fuel_check:
            required_fuel: int = (
                xz_size * xz_size * y_size + xz_size * 2 + y_size
            ) // 80 + 1

            await self.refuel(required_fuel)

            current_fuel = await self.get_fuel()
            if current_fuel < required_fuel:
                raise HaltException(
                    f"Not enough fuel to complete trip. Need {required_fuel - current_fuel} more."
                )

        for _ in range(y_size + 1):
            for row_number in range(xz_size):
                for _ in range(xz_size - 1):
                    await self.dig_move(Direction.FORWARD)
                # turn to next row
                if row_number < (xz_size - 1):
                    if row_number % 2 == 0:
                        await self.turn_right()
                        await self.dig_move(Direction.FORWARD)
                        await self.turn_right()
                    else:
                        await self.turn_left()
                        await self.dig_move(Direction.FORWARD)
                        await self.turn_left()
            if xz_size % 2 == 0:
                await self.turn_right()
            else:
                await self.turn_left()

            await self.dig_move(Direction.DOWN)

        await self._process_complete()


class StripTurtle(Turtle):
    """A turtle that can mine a stripmine."""

    branch_spacing: int = 3
    """blocks to leave between each branch"""
    branch_length: int = 47
    """number of blocks to mine in each branch"""
    branch_pair_count: int = 8
    """total number of pairs of branches"""
    prerun_fuel_check: bool = True
    """check if enough fuel before mining"""
    do_place_torches: bool = True
    """whether to place torches in the stripmine"""
    torch_light: int = 12
    """amount of blocks that torch light travels"""
    current_light_level: int = 0
    """current light level on the turtle"""

    async def place_torch(self) -> None:
        """Try to place a torch above the turtle."""
        try:
            await self.inventory_select("torch")
        except InventoryException:
            self._logger.error("Ran out of torches.")
            raise
        else:
            await self.place_block(Direction.UP)

    @overrides
    async def get_status(self) -> str:
        """Create a status update string."""
        output = await super().get_status()
        output += f"Light Level:     {self.current_light_level}\n"
        return output

    async def falling_block_check(self) -> None:
        """Check if any falling blocks are in front of the turtle and mine until there isn't.

        If there are block above the turtle, they get auto destroyed (like falling on a torch).
        """
        falling_blocks = ["gravel", "sand"]

        while True:
            data = await self.inspect(Direction.FORWARD)
            name = data.get("name ", "")
            print(name)
            if any(
                falling_block in name for falling_block in falling_blocks
            ):
                self._logger.debug("Block is falling block, mining it.")
                await self.dig(Direction.FORWARD)
            else:
                self._logger.debug("not falling block.")
                break

    @overrides
    async def start(self) -> None:
        """The main turtle process."""
        if self.prerun_fuel_check:
            required_fuel: int = (
                (
                    self.branch_spacing + 1
                )  # spacing between branches, plus 1 for the connection between branches
                + (
                    self.branch_length * 4 + 1
                )  # length of mining each branch and going back to main
            ) * self.branch_pair_count

            try:
                await self.refuel(required_fuel)
            except (InventoryException, ValueError):
                pass

            current_fuel = await self.get_fuel()
            if current_fuel < required_fuel:
                raise HaltException(
                    f"Not enough fuel to complete trip. Need {required_fuel - current_fuel} more."
                )

        for _ in range(self.branch_pair_count):
            # continue main branch
            for _ in range(self.branch_spacing + 1):
                await self.dig_move(Direction.FORWARD)
                await self.dig(Direction.UP)

            # update home location current point on main branch
            self._home_location = self.position.location

            # mine left branch
            await self.turn_left()
            for _ in range(2):
                for _ in range(self.branch_length):
                    await self.dig_move(Direction.FORWARD)
                    await self.dig(Direction.UP)

                # go back to main branch
                await self.turn_right()
                await self.turn_right()

                # dump inventory of trash
                for bad_block in self._bad_blocks:
                    did_drop: bool = True
                    while did_drop:
                        self._logger.info(f"Dumping {bad_block} blocks.")
                        try:
                            await self.inventory_dump(bad_block, Direction.UP)
                        except InventoryException:
                            did_drop = False

                # start lighting and heading back
                first_torch = True
                self.current_light_level = self.torch_light
                for branch_position in range(self.branch_length):
                    # place torches if necessary
                    target_light: int = 0 if first_torch else -(self.torch_light + 1)

                    if (
                        self.do_place_torches
                        and self.current_light_level <= target_light
                    ):
                        if first_torch:
                            first_torch = False

                        try:
                            await self.place_torch()
                        except InventoryException:
                            # place failed
                            self.do_place_torches = False
                        else:
                            # place success
                            self.current_light_level = self.torch_light

                    # we don't need to dig move because we already mined the blocks
                    await self.move(Direction.FORWARD)
                    self.current_light_level -= (
                        1  # decrease light level because we moved
                    )

                    # at end of branch if there's not enough light, slap a torch down
                    if (
                        branch_position == (self.branch_length - 2)
                        and self.do_place_torches
                        and self.current_light_level <= -1
                    ):
                        try:
                            await self.place_torch()
                        except InventoryException:
                            # place failed
                            self.do_place_torches = False
                        else:
                            # place success
                            self.current_light_level = self.torch_light

            # face forward again to prepare for next branch pair
            await self.turn_right()


class TestTurtle(StripTurtle):
    """A turtle to test out features."""

    @overrides
    async def start(self) -> None:
        """The main turtle process."""
        await self.falling_block_check()
