"""Decorators for equipment control methods."""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any, cast, overload

from pyomnilogic_local.util import OmniEquipmentNotReadyError

_LOGGER = logging.getLogger(__name__)


@overload
def control_method[FUNC: Callable[..., Any]](func: FUNC, *, check_ready: bool = ...) -> FUNC: ...
@overload
def control_method[FUNC: Callable[..., Any]](func: None = ..., *, check_ready: bool = ...) -> Callable[[FUNC], FUNC]: ...
def control_method[FUNC: Callable[..., Any]](func: FUNC | None = None, *, check_ready: bool = True) -> FUNC | Callable[[FUNC], FUNC]:
    """Check readiness and mark state as dirty.

    This decorator ensures equipment is ready before executing control methods and
    automatically marks telemetry as dirty after execution. It replaces the common
    pattern of checking is_ready and using @dirties_state() separately.

    The decorator:
    1. Optionally checks if equipment is ready (via is_ready property)
    2. Raises OmniEquipmentNotReadyError with descriptive message if not ready
    3. Executes the control method
    4. Marks telemetry as dirty

    Args:
        func: The function being decorated. Supplied automatically when used without parentheses.
        check_ready: If False, skip the is_ready check and execute unconditionally.
            Defaults to True.

    Raises:
        OmniEquipmentNotReadyError: If equipment is not ready to accept commands

    Example:
        @control_method
        async def turn_on(self) -> None:
            await self._api.async_set_equipment(...)

        @control_method(check_ready=False)
        async def turn_off(self) -> None:
            await self._api.async_set_equipment(...)
    """

    def decorator(f: FUNC) -> FUNC:
        @functools.wraps(f)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Check if equipment is ready
            if check_ready and not self.is_ready:
                # Generate descriptive error message from function name
                action = f.__name__.replace("_", " ")
                msg = f"Cannot {action}: equipment is not ready to accept commands"
                raise OmniEquipmentNotReadyError(msg)

            # Execute the original function
            result = await f(self, *args, **kwargs)

            # Mark telemetry as dirty
            if hasattr(self, "_omni"):
                self._omni._telemetry_dirty = True
            else:
                _LOGGER.warning("%s does not have _omni reference, cannot mark state as dirty", self.__class__.__name__)

            return result

        return cast("FUNC", wrapper)

    if func is not None:
        # Used as @control_method without parentheses
        return decorator(func)

    # Used as @control_method(...) with parentheses
    return decorator
