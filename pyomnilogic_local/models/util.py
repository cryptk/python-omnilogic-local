from typing import Any

from pydantic.utils import GetterDict

from .const import XML_NS


class ParameterGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self._obj.find(f".//api:Parameter[@name='{key}']", XML_NS).text
        except AttributeError:
            return default
