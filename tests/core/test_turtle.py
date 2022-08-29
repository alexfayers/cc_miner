"""Tests for the `turtle` module."""
import pytest

from cc_miner.core.turtle import Turtle
from cc_miner.core.turtle.types import Bearing


@pytest.mark.asyncio
async def test_turtle_movement_forward(turtle: Turtle) -> None:
    """Test the turtle forward movement."""
    await turtle.forward()

    assert turtle.position.location.z == -1
    assert turtle.position.bearing == Bearing.NORTH


@pytest.mark.asyncio
async def test_turtle_movement_back(turtle: Turtle) -> None:
    """Test the turtle back movement."""
    await turtle.back()

    assert turtle.position.location.z == 1
    assert turtle.position.bearing == Bearing.NORTH


@pytest.mark.asyncio
async def test_turtle_movement_up(turtle: Turtle) -> None:
    """Test the turtle up movement."""
    await turtle.up()

    assert turtle.position.location.y == 1
    assert turtle.position.bearing == Bearing.NORTH


@pytest.mark.asyncio
async def test_turtle_movement_down(turtle: Turtle) -> None:
    """Test the turtle down movement."""
    await turtle.down()

    assert turtle.position.location.y == -1
    assert turtle.position.bearing == Bearing.NORTH
