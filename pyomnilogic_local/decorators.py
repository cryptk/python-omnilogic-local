"""Decorators for automatic state management in pyomnilogic_local."""

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar, cast

_LOGGER = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def auto_refresh(
    update_mspconfig: bool = False,
    update_telemetry: bool = True,
    delay: float = 1.25,
) -> Callable[[F], F]:
    """Decorator to automatically refresh OmniLogic state after method execution.

    This decorator will:
    1. Execute the decorated method
    2. Wait for the specified delay (to allow controller to update)
    3. Refresh telemetry/mspconfig if they're older than the post-delay time

    The decorator is lock-safe: if multiple decorated methods are called concurrently,
    only one refresh will occur thanks to the update_if_older_than mechanism.

    Args:
        update_mspconfig: Whether to refresh MSPConfig after method execution
        update_telemetry: Whether to refresh Telemetry after method execution
        delay: Time in seconds to wait after method completes before refreshing

    Usage:
        @auto_refresh()  # Default: telemetry only, 0.25s delay
        async def turn_on(self, auto_refresh: bool | None = None):
            ...

        @auto_refresh(update_mspconfig=True, delay=0.5)
        async def configure(self, auto_refresh: bool | None = None):
            ...

    The decorated method can accept an optional `auto_refresh` parameter:
    - If None (default): Uses the OmniLogic instance's auto_refresh_enabled setting
    - If True: Forces auto-refresh regardless of instance setting
    - If False: Disables auto-refresh for this call
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract the 'auto_refresh' parameter if provided
            auto_refresh_param = kwargs.pop("auto_refresh", None)

            # First arg should be 'self' (equipment instance)
            if not args:
                raise RuntimeError("@auto_refresh decorator requires a method with 'self' parameter")

            self_obj = args[0]

            # Get the OmniLogic instance
            # Equipment classes should have _omni attribute pointing to parent OmniLogic
            if hasattr(self_obj, "_omni") and self_obj._omni is not None:  # pylint: disable=protected-access
                omni = self_obj._omni  # pylint: disable=protected-access
            elif hasattr(self_obj, "auto_refresh_enabled"):
                # This IS the OmniLogic instance
                omni = self_obj
            else:
                raise RuntimeError("@auto_refresh decorator requires equipment to have '_omni' attribute or be used on OmniLogic methods")

            # Determine if we should auto-refresh
            should_refresh = auto_refresh_param if auto_refresh_param is not None else omni.auto_refresh_enabled

            # Execute the original method
            result = await func(*args, **kwargs)

            # Perform auto-refresh if enabled
            if should_refresh:
                # Wait for the controller to process the change
                await asyncio.sleep(delay)

                # Calculate the target time (after delay)
                target_time = time.time()

                # Update only if data is older than target time
                await omni.update_if_older_than(
                    telemetry_min_time=target_time if update_telemetry else None,
                    mspconfig_min_time=target_time if update_mspconfig else None,
                )

            return result

        return cast(F, wrapper)

    return decorator
