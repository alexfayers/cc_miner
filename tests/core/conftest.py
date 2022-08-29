"""Pytest test configuration."""
import pytest

from cc_miner.core.turtle import Turtle


@pytest.fixture(scope="function")
def turtle() -> Turtle:
    """Pytest fixture for a `Turtle`."""
    return Turtle(1)
