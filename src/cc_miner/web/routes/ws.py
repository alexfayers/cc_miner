"""Websocket routes."""
from simple_websocket import Server

from .. import sock


@sock.route("/echo")
def echo(ws: Server) -> None:
    """Handle echo websocket.

    Args:
        ws (Server): The websocket connection.
    """
    while True:
        data = ws.receive()
        ws.send(data * 2)
