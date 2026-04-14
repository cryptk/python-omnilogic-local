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
    """Drop-in replacement for OmniLogicAPI that serves pre-recorded data from a JSON file.

    The JSON file must contain the simulation data at the paths:
        - ``.data.telemetry``  — raw XML telemetry string
        - ``.data.msp_config`` — raw XML MSP config string

    Any API call other than ``async_get_telemetry`` or ``async_get_mspconfig`` is silently
    absorbed and logged at INFO level; no network traffic is generated.
    """

    def __init__(self, filepath: str) -> None:
        """Load simulation data from *filepath*.

        Args:
            filepath: Path to the JSON simulation data file.

        Raises:
            FileNotFoundError: If the file does not exist at *filepath*.
            KeyError: If the expected JSON structure is not present in the file.
        """
        path = Path(filepath)
        if not path.exists():
            msg = f"Simulation data file not found: {filepath}"
            raise FileNotFoundError(msg)

        data = json.loads(path.read_text(encoding="utf-8"))
        sim_data: dict[str, Any] = data["data"]

        self._mspconfig = sim_data["msp_config"]
        self._telemetry = sim_data["telemetry"]

        _LOGGER.warning(
            "Running in simulation mode using data from '%s'. No API calls will be made to the OmniLogic controller.",
            filepath,
        )

    @overload
    async def async_get_mspconfig(self, raw: Literal[True]) -> str: ...
    @overload
    async def async_get_mspconfig(self, raw: Literal[False]) -> MSPConfig: ...
    @overload
    async def async_get_mspconfig(self) -> MSPConfig: ...
    async def async_get_mspconfig(self, raw: bool = False) -> MSPConfig | str:
        """Return the pre-loaded MSP config from the simulation file."""
        if raw:
            return self._mspconfig
        return MSPConfig.load_xml(self._mspconfig)

    @overload
    async def async_get_telemetry(self, raw: Literal[True]) -> str: ...
    @overload
    async def async_get_telemetry(self, raw: Literal[False]) -> Telemetry: ...
    @overload
    async def async_get_telemetry(self) -> Telemetry: ...
    async def async_get_telemetry(self, raw: bool = False) -> Telemetry | str:
        """Return the pre-loaded telemetry from the simulation file."""
        if raw:
            return self._telemetry
        return Telemetry.load_xml(self._telemetry)

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
