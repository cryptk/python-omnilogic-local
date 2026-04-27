"""API module for interacting with Hayward OmniLogic pool controllers.

This module provides the OmniLogicAPI class, which allows for local
control and monitoring of Hayward OmniLogic and OmniHub pool controllers
over a local network connection via the UDP XML API.
"""

from __future__ import annotations

from .api import OmniLogicAPI
from .exceptions import (
    OmniCommandError,
    OmniConnectionError,
    OmniFragmentationError,
    OmniLogicError,
    OmniMessageFormatError,
    OmniProtocolError,
    OmniTimeoutError,
    OmniValidationError,
)
from .message import OmniLogicMessage
from .protocol import OmniLogicProtocol

__all__ = [
    "OmniCommandError",
    "OmniConnectionError",
    "OmniFragmentationError",
    "OmniLogicAPI",
    "OmniLogicError",
    "OmniLogicMessage",
    "OmniLogicProtocol",
    "OmniMessageFormatError",
    "OmniProtocolError",
    "OmniTimeoutError",
    "OmniValidationError",
]
