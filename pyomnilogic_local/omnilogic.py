import logging

from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.backyard import Backyard
from pyomnilogic_local.models import MSPConfig, Telemetry
from pyomnilogic_local.system import System

_LOGGER = logging.getLogger(__name__)


class OmniLogic:
    poll_mspconfig: bool = True
    poll_telemetry: bool = True

    mspconfig: MSPConfig
    telemetry: Telemetry

    system: System
    backyard: Backyard

    def __init__(self, host: str, port: int = 10444) -> None:
        self.host = host
        self.port = port

        self._api = OmniLogicAPI(host, port)

    async def refresh(self) -> None:
        """Refresh the data from the OmniLogic controller."""
        if self.poll_mspconfig:
            self.mspconfig = await self._api.async_get_mspconfig()
        if self.poll_telemetry:
            self.telemetry = await self._api.async_get_telemetry()

        self._update_equipment()

    async def refresh_mspconfig(self) -> None:
        """Refresh only the MSPConfig data from the OmniLogic controller."""
        self.mspconfig = await self._api.async_get_mspconfig()
        self._update_equipment()

    async def refresh_telemetry(self) -> None:
        """Refresh only the Telemetry data from the OmniLogic controller."""
        self.telemetry = await self._api.async_get_telemetry()
        self._update_equipment()

    def _update_equipment(self) -> None:
        """Update equipment objects based on the latest MSPConfig and Telemetry data."""

        if not hasattr(self, "mspconfig") or self.mspconfig is None:
            _LOGGER.debug("No MSPConfig data available; skipping equipment update")
            return

        try:
            self.system.update_config(self.mspconfig.system)
        except AttributeError:
            self.system = System(self.mspconfig.system)

        try:
            self.backyard.update(self.mspconfig.backyard, self.telemetry)
        except AttributeError:
            self.backyard = Backyard(self._api, self.mspconfig.backyard, self.telemetry)
