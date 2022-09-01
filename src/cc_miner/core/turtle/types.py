"""`Turtle` related types."""
from enum import IntEnum

from pydantic import BaseModel, Field


class Location(BaseModel):
    """The current position of a turtle."""

    x: int = Field(..., description="The x coordinate of the turtle.")
    y: int = Field(..., description="The y coordinate of the turtle.")
    z: int = Field(..., description="The z coordinate of the turtle.")


class Bearing(IntEnum):
    """The current bearing of a turtle."""

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


class Position(BaseModel):
    """The current position of a turtle."""

    location: Location = Field(..., description="The location of the turtle.")
    bearing: Bearing = Field(..., description="The bearing of the turtle.")


class Direction(IntEnum):
    """The direction to move the turtle."""

    FORWARD = 0
    BACK = 1
    UP = 2
    DOWN = 3


class InventorySlotInfo(BaseModel):
    """The information about a block within a turtle's inventory."""

    name: str = Field(..., description="The name of the block.")
    count: int = Field(..., description="The number of blocks in the slot.")