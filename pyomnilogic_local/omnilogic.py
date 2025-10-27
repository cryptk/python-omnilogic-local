import logging

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.backyard import Backyard
from pyomnilogic_local.models import MSPConfig, Telemetry
from pyomnilogic_local.omnitypes import OmniType
from pyomnilogic_local.system import System

_LOGGER = logging.getLogger(__name__)


class OmniLogic:
    poll_mspconfig: bool = True
    poll_telemetry: bool = True

    mspconfig: MSPConfig
    telemetry: Telemetry

    system: System
    backyard: Backyard

    equipment: dict[int, OmniEquipment] = {}

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

        _LOGGER.debug("Updating ColorLogic Light equipment data")

        if not hasattr(self, "mspconfig") or self.mspconfig is None:
            _LOGGER.debug("No MSPConfig data available; skipping equipment update")
            return

        for _, equipment_mspconfig in self.mspconfig:
            if equipment_mspconfig.omni_type == OmniType.SYSTEM:
                self.system = System(equipment_mspconfig)
            if equipment_mspconfig.omni_type == OmniType.BACKYARD:
                self.backyard = Backyard(equipment_mspconfig, self.telemetry)
