from collections.abc import Awaitable, Callable
import logging
from typing import Any, Literal, TypeVar, cast, overload

from pydantic.utils import GetterDict

from .const import XML_NS
from .filter_diagnostics import FilterDiagnostics
from .mspconfig import MSPConfig
from .telemetry import Telemetry

_LOGGER = logging.getLogger(__name__)


class ParameterGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self._obj.find(f".//api:Parameter[@name='{key}']", XML_NS).text
        except AttributeError:
            return default


F = TypeVar("F", bound=Callable[..., Awaitable[str]])
TPydanticTypes = Telemetry | MSPConfig | FilterDiagnostics


def to_pydantic(pydantic_type: type[TPydanticTypes]) -> Callable[..., Any]:
    def inner(func: F, *args: Any, **kwargs: Any) -> F:
        """Wrap an API function that returns XML and parse it into a Pydantic model"""

        @overload
        async def wrapper(*args: Any, raw: Literal[True], **kwargs: Any) -> str:
            ...

        @overload
        async def wrapper(*args: Any, raw: Literal[False], **kwargs: Any) -> TPydanticTypes:
            ...

        async def wrapper(*args: Any, raw: bool = False, **kwargs: Any) -> TPydanticTypes | str:
            resp_body = await func(*args, **kwargs)
            if raw:
                return resp_body
            return pydantic_type.load_xml(resp_body)

        return cast(F, wrapper)

    return inner
