import logging
from collections.abc import Awaitable, Callable
from typing import Any, Literal, TypeVar, cast, overload

from .filter_diagnostics import FilterDiagnostics
from .mspconfig import MSPConfig
from .telemetry import Telemetry

_LOGGER = logging.getLogger(__name__)


F = TypeVar("F", bound=Callable[..., Awaitable[str]])


def to_pydantic(
    pydantic_type: type[Telemetry | MSPConfig | FilterDiagnostics],
) -> Callable[..., Any]:
    def inner(func: F, *args: Any, **kwargs: Any) -> F:
        """Wrap an API function that returns XML and parse it into a Pydantic model"""

        @overload
        async def wrapper(*args: Any, raw: Literal[True], **kwargs: Any) -> str: ...

        @overload
        async def wrapper(*args: Any, raw: Literal[False], **kwargs: Any) -> Telemetry | MSPConfig | FilterDiagnostics: ...

        async def wrapper(*args: Any, raw: bool = False, **kwargs: Any) -> Telemetry | MSPConfig | FilterDiagnostics | str:
            resp_body = await func(*args, **kwargs)
            if raw:
                return resp_body
            return pydantic_type.load_xml(resp_body)

        return cast(F, wrapper)

    return inner
