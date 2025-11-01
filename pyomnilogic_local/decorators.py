"""Decorators for equipment control methods."""

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar, cast

_LOGGER = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def dirties_state(mspconfig: bool = False, telemetry: bool = True) -> Callable[[F], F]:
    """Mark state as dirty after equipment control methods.

    This decorator marks the OmniLogic state (telemetry and/or mspconfig) as dirty
    after a control method executes, indicating that the cached state is likely
    out of sync with reality. Users can then call refresh() to update the state.

    Args:
        mspconfig: Whether to mark mspconfig as dirty (default: False)
        telemetry: Whether to mark telemetry as dirty (default: True)

    Example:
        @dirties_state(telemetry=True)
        async def turn_on(self) -> None:
            await self._api.async_set_equipment(...)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Execute the original function
            result = await func(self, *args, **kwargs)

            # Mark state as dirty
            if hasattr(self, "_omni"):
                if telemetry:
                    self._omni._telemetry_dirty = True  # pylint: disable=protected-access
                if mspconfig:
                    self._omni._mspconfig_dirty = True  # pylint: disable=protected-access
            else:
                _LOGGER.warning("%s does not have _omni reference, cannot mark state as dirty", self.__class__.__name__)

            return result

        return cast(F, wrapper)

    return decorator
