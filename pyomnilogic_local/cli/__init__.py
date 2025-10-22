"""CLI module for OmniLogic local control.

This module provides the command-line interface for controlling Hayward
OmniLogic and OmniHub pool controllers.
"""

from pyomnilogic_local.cli.utils import ensure_connection

__all__ = ["ensure_connection"]
