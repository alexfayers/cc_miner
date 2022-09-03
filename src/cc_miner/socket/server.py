"""Websocket server class."""
import asyncio
import json
import logging
from os import system
from typing import Set, Type

import websockets
from pydantic import ValidationError
from websockets.server import WebSocketServerProtocol

from ..core.turtle import Turtle, StripTurtle
from .types import CommandResponse, DataMessage, ErrorMessage, RegisterMessage

logger = logging.getLogger(__name__)


class SocketServer:
    """A websocket server which communicates with turtles."""

    clients: Set[Turtle] = set()
    mining_type: Type[Turtle] = StripTurtle

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

    async def register(self, websocket: WebSocketServerProtocol, _id: int) -> None:
        """Register a websocket connection.

        Args:
            websocket (WebSocketServerProtocol): The websocket connection.
            _id (int): The unique id of the turtle.
        """
        turtle = self.mining_type(_id, websocket)
        self.clients.add(turtle)
        await self.send(websocket, "Registered")
        try:
            # main loop
            logger.info("Starting main loop for #%s", _id)
            await turtle.start()
        finally:
            logger.info("Stopping main loop for #%s", _id)
            self.clients.remove(turtle)
            try:
                await self.send(websocket, "Deregistered")
            except Exception as e:
                logger.error("Error deregistering #%s: %s", _id, e)

    async def handler(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """The handler for the server.

        Handles the websocket connection before a connection is properly established.

        Args:
            websocket (WebSocketServerProtocol): The websocket connection.
            path (str): The path to the websocket.
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

        for potential_type in [
            DataMessage,
            ErrorMessage,
            CommandResponse,
            RegisterMessage,
        ]:
            try:
                event = potential_type.parse_obj(event)
            except ValidationError:
                continue
            else:
                break
        else:
            raise await self.error(websocket, f"Could not parse: {event}")

        if type(event) is RegisterMessage:
            logger.info("Got new registration from #%s", event.id)
            await self.register(websocket, event.id)
        else:
            raise await self.error(websocket, f"Unexpected event type: {event.json()}")

    async def output_statuses(self) -> None:
        """Output the status of all active turtles."""
        logging.getLogger("cc_miner").setLevel(logging.WARNING)
        while True:
            system("clear")  # clear the screen
            if self.clients:
                print(f"{len(self.clients)} active turtles:\n\n")
                for turtle in self.clients:
                    output = await turtle.get_status()
                    print(f"Turtle #{turtle.uid}:\n{output}\n\n")
            else:
                print("No active turtles...")
            await asyncio.sleep(0.1)

    def start(self) -> None:
        """Start the server."""
        asyncio.get_event_loop().run_until_complete(
            websockets.serve(self.handler, self.host, self.port)  # type: ignore
        )

        asyncio.get_event_loop().run_until_complete(self.output_statuses())

        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            logger.info("Stopping server")
            asyncio.get_event_loop().stop()
            asyncio.get_event_loop().run_forever()
            asyncio.get_event_loop().close()
