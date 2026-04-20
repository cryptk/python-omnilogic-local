"""Mock API for simulation mode — loads data from a local JSON file instead of a live controller."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal, overload

from pyomnilogic_local.models.mspconfig import MSPConfig
from pyomnilogic_local.models.telemetry import Telemetry

_LOGGER = logging.getLogger(__name__)


class OmniLogicMockAPI:
    """Drop-in replacement for OmniLogicAPI that serves pre-recorded data from one or more JSON files.

    Each JSON file must contain the simulation data at the paths:
        - ``.data.telemetry``  — raw XML telemetry string
        - ``.data.msp_config`` — raw XML MSP config string

    When multiple files are provided the class maintains a round-robin pointer into the
    list.  Whether the pointer advances after each call is controlled by two attributes:

    - ``increment_on_mspconfig`` (default ``False``) — advance after ``async_get_mspconfig``
    - ``increment_on_telemetry`` (default ``True``)  — advance after ``async_get_telemetry``

    Any API call other than ``async_get_telemetry`` or ``async_get_mspconfig`` is silently
    absorbed and logged at INFO level; no network traffic is generated.
    """

    def __init__(self, filepath: str) -> None:
        """Load simulation data from *filepath*.

        Args:
            filepath: Comma-separated path(s) to JSON simulation data file(s).
                A single path with no commas is treated as a one-element list.

        Raises:
            FileNotFoundError: If any file does not exist.
            KeyError: If the expected JSON structure is not present in a file.
        """
        paths = filepath.split(",")

        self._sim_data: list[dict[str, Any]] = []
        for fp in paths:
            path = Path(fp)
            if not path.exists():
                msg = f"Simulation data file not found: {fp}"
                raise FileNotFoundError(msg)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["data"]["filepath"] = fp
            self._sim_data.append(data["data"])

        self._index = 0
        self.increment_on_mspconfig = False
        self.increment_on_telemetry = True

        _LOGGER.warning(
            "Running in simulation mode using data from %s. No API calls will be made to the OmniLogic controller.",
            paths,
        )

    @overload
    async def async_get_mspconfig(self, raw: Literal[True]) -> str: ...
    @overload
    async def async_get_mspconfig(self, raw: Literal[False]) -> MSPConfig: ...
    @overload
    async def async_get_mspconfig(self) -> MSPConfig: ...
    async def async_get_mspconfig(self, raw: bool = False) -> MSPConfig | str:
        """Return the pre-loaded MSP config from the current simulation file."""
        data = self._sim_data[self._index]
        if self.increment_on_mspconfig:
            _LOGGER.debug(
                "Advancing simulation file index from %s to %s, filepath: %s",
                self._index,
                (self._index + 1) % len(self._sim_data),
                data["filepath"],
            )
            self._index = (self._index + 1) % len(self._sim_data)
        if raw:
            return data["msp_config"]
        return MSPConfig.load_xml(data["msp_config"])

    @overload
    async def async_get_telemetry(self, raw: Literal[True]) -> str: ...
    @overload
    async def async_get_telemetry(self, raw: Literal[False]) -> Telemetry: ...
    @overload
    async def async_get_telemetry(self) -> Telemetry: ...
    async def async_get_telemetry(self, raw: bool = False) -> Telemetry | str:
        """Return the pre-loaded telemetry from the current simulation file."""
        data = self._sim_data[self._index]
        if self.increment_on_telemetry:
            _LOGGER.debug(
                "Advancing simulation file index from %s to %s, filepath: %s",
                self._index,
                (self._index + 1) % len(self._sim_data),
                data["filepath"],
            )
            self._index = (self._index + 1) % len(self._sim_data)
        if raw:
            return data["telemetry"]
        return Telemetry.load_xml(data["telemetry"])

    def __getattr__(self, name: str) -> Any:
        """Return a no-op async callable for any API method not explicitly implemented."""

        async def _noop(*args: Any, **kwargs: Any) -> None:
            _LOGGER.info(
                "Simulation mode: ignoring call to %s (args=%s, kwargs=%s)",
                name,
                args,
                kwargs,
            )

        return _noop
