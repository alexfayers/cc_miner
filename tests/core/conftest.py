"""Pytest test configuration."""
from typing import Any, cast

import pytest
from websockets.server import WebSocketServerProtocol

from cc_miner.core.turtle import Turtle
from cc_miner.socket.types import CommandResponse


class FakeSocket:
    """Fake socket, for tests."""

    async def send(self, *args: Any, **kwargs: Any) -> None:
        """Fake send method."""

    async def recv(self, *args: Any, **kwargs: Any) -> str:
        """Fake recv method."""
        return CommandResponse(status="OK").json()


@pytest.fixture(scope="function")
def turtle() -> Turtle:
    """Pytest fixture for a `Turtle`."""
    return Turtle(1, cast(WebSocketServerProtocol, FakeSocket()))
