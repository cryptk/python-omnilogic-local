"""API module for interacting with Hayward OmniLogic pool controllers.

This module provides the OmniLogicAPI class, which allows for local
control and monitoring of Hayward OmniLogic and OmniHub pool controllers
over a local network connection via the UDP XML API.
"""

from __future__ import annotations

from .api import OmniLogicAPI

__all__ = [
    "OmniLogicAPI",
]
