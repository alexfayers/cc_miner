"""Storage turtle."""

from ..turtle import Turtle
from ..turtle.types import Direction
from overrides import overrides


class StorageTurtle(Turtle):
    """A turtle to handle mass storage."""

    async def deposit(self, direction: Direction) -> None:
        """Deposit all items in the current inventory into the chest.

        Args:
            direction (Direction): The direction of the chest.
        """
        pass

    @overrides
    async def start(self) -> None:
        """Main turtle function."""
        chest = self.peripheral_find("chest")
        print(chest)
