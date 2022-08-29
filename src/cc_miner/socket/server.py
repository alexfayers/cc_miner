"""Websocket server class."""
import asyncio
import json
import logging

import websockets
from pydantic import ValidationError
from websockets.server import WebSocketServerProtocol

from .types import DataMessage, ErrorMessage, StatusMessage

logger = logging.getLogger(__name__)


class SocketServer:
    """A websocket server which communicates with turtles."""

    def __init__(self, host: str, port: int) -> None:
        """Initialise the server.

        Args:
            host (str): The IP to listen on.
            port (int): The port to listen on.
        """
        self.host = host
        self.port = port

    async def error(
        self, websocket: WebSocketServerProtocol, message: str
    ) -> Exception:
        """Send an error message to the client.

        Args:
            websocket (WebSocketServerProtocol): The websocket connection.
            message (str): The error message to send.
        """
        event = ErrorMessage(message=message)
        await websocket.send(event.json())
        return Exception(message)

    async def send(self, websocket: WebSocketServerProtocol, message: str) -> None:
        """Send a message to the client.

        Args:
            websocket (Any): The websocket connection.
            message (str): The message to send.
        """
        event = DataMessage(message=message)
        await websocket.send(event.json())

    async def handler(self, websocket: WebSocketServerProtocol) -> None:
        """The handler for the server.

        Args:
            websocket (WebSocketServerProtocol): The websocket connection.
        """
        message = await websocket.recv()
        logger.debug("Got message: %s", message)

        try:
            event = json.loads(message)
        except json.JSONDecodeError:
            logger.error("Not a valid JSON message: %s", message)
            raise await self.error(websocket, "Invalid JSON message")

        if "type" not in event:
            logger.error("No type in message: %s", message)
            raise await self.error(websocket, "'type' key not in message")

        for potential_type in [DataMessage, ErrorMessage, StatusMessage]:
            try:
                event = potential_type.parse_obj(event)
            except ValidationError:
                continue
            else:
                break
        else:
            raise await self.error(websocket, f"Could not parse: {event}")

        if type(event) is DataMessage:
            data = event.message
            await self.send(websocket, f"Got message: {data}")
        elif type(event) is ErrorMessage:
            data = event.message
            await self.send(websocket, f"Got error: {data}")
        elif type(event) is StatusMessage:
            # handle status message
            logger.info("Got status message: %s", event.message)
            await self.send(websocket, f"Got status message: {event.message}")

    def start(self) -> None:
        """Start the server."""
        asyncio.get_event_loop().run_until_complete(
            websockets.serve(self.handler, self.host, self.port)  # type: ignore
        )
        asyncio.get_event_loop().run_forever()
