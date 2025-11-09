"""Decorators for equipment control methods."""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any, cast

from pyomnilogic_local.util import OmniEquipmentNotReadyError

_LOGGER = logging.getLogger(__name__)


def control_method[F: Callable[..., Any]](func: F) -> F:
    """Check readiness and mark state as dirty.

    This decorator ensures equipment is ready before executing control methods and
    automatically marks telemetry as dirty after execution. It replaces the common
    pattern of checking is_ready and using @dirties_state() separately.

    The decorator:
    1. Checks if equipment is ready (via is_ready property)
    2. Raises OmniEquipmentNotReadyError with descriptive message if not ready
    3. Executes the control method
    4. Marks telemetry as dirty

    Raises:
        OmniEquipmentNotReadyError: If equipment is not ready to accept commands

    Example:
        @control_method
        async def turn_on(self) -> None:
            await self._api.async_set_equipment(...)
    """
    # Import here to avoid circular dependency

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # Check if equipment is ready
        if not self.is_ready:
            # Generate descriptive error message from function name
            action = func.__name__.replace("_", " ")
            msg = f"Cannot {action}: equipment is not ready to accept commands"
            raise OmniEquipmentNotReadyError(msg)

        # Execute the original function
        result = await func(self, *args, **kwargs)

        # Mark telemetry as dirty
        if hasattr(self, "_omni"):
            self._omni._telemetry_dirty = True
        else:
            _LOGGER.warning("%s does not have _omni reference, cannot mark state as dirty", self.__class__.__name__)

        return result

    return cast("F", wrapper)
