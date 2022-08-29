"""Types for the `socket` module."""
from typing import Any, Union

from pydantic import BaseModel
from typing_extensions import Literal


class BaseMessage(BaseModel):
    """Base message from the `SocketServer`."""

    type: str


class DataMessage(BaseMessage):
    """A message containing readable data."""

    type = "data"
    message: str


class ErrorMessage(BaseMessage):
    """A message containing an error."""

    type = "error"
    message: str


class StatusMessage(BaseMessage):
    """A message containing the status of the server."""

    type = "status"
    status: Union[Literal["OK"], Literal["ERROR"]]
    data: Any = None


class RegisterMessage(BaseMessage):
    """A message containing the registration of a client."""

    type = "register"
    id: int


class CommandMessage(BaseMessage):
    """A message containing a command for a turtle."""

    type = "command"
    command: str
