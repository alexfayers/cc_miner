"""Tests for the `turtle` module."""
from cc_miner.core.turtle import Turtle
from cc_miner.core.turtle.types import Bearing


def test_turtle_movement_forward(turtle: Turtle) -> None:
    """Test the turtle forward movement."""
    turtle.forward()

    assert turtle.position.location.z == -1
    assert turtle.position.bearing == Bearing.NORTH


def test_turtle_movement_back(turtle: Turtle) -> None:
    """Test the turtle back movement."""
    turtle.back()

    assert turtle.position.location.z == 1
    assert turtle.position.bearing == Bearing.NORTH


def test_turtle_movement_up(turtle: Turtle) -> None:
    """Test the turtle up movement."""
    turtle.up()

    assert turtle.position.location.y == 1
    assert turtle.position.bearing == Bearing.NORTH


def test_turtle_movement_down(turtle: Turtle) -> None:
    """Test the turtle down movement."""
    turtle.down()

    assert turtle.position.location.y == -1
    assert turtle.position.bearing == Bearing.NORTH
