"""Types for the `socket` module."""
from pydantic import BaseModel


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
    message: str
