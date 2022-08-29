"""Websocket server class."""
import asyncio
import json
import websockets
import logging
from websockets.server import WebSocketServerProtocol


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

    async def error(self, websocket: WebSocketServerProtocol, message: str) -> None:
        """Send an error message to the client.

        Args:
            websocket (WebSocketServerProtocol): The websocket connection.
            message (str): The error message to send.
        """
        event = {
            "type": "error",
            "message": message,
        }
        await websocket.send(json.dumps(event))

    async def send(self, websocket: WebSocketServerProtocol, message: str) -> None:
        """Send a message to the client.

        Args:
            websocket (Any): The websocket connection.
            message (str): The message to send.
        """
        event = {
            "type": "message",
            "message": message,
        }
        await websocket.send(json.dumps(event))

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
            raise

        assert "type" in event, "No type in event"

        if event["type"] == "message":
            data = event["message"]
            await self.send(websocket, f"Got message: {data}")

    def start(self) -> None:
        """Start the server."""
        asyncio.get_event_loop().run_until_complete(
            websockets.serve(self.handler, self.host, self.port)  # type: ignore
        )
        asyncio.get_event_loop().run_forever()
