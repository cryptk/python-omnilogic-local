import asyncio
import logging
import time

from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.backyard import Backyard
from pyomnilogic_local.models import MSPConfig, Telemetry
from pyomnilogic_local.system import System

_LOGGER = logging.getLogger(__name__)


class OmniLogic:
    mspconfig: MSPConfig
    telemetry: Telemetry

    system: System
    backyard: Backyard

    _mspconfig_last_updated: float = 0.0
    _telemetry_last_updated: float = 0.0
    _mspconfig_dirty: bool = True
    _telemetry_dirty: bool = True
    _refresh_lock: asyncio.Lock

    def __init__(self, host: str, port: int = 10444) -> None:
        self.host = host
        self.port = port

        self._api = OmniLogicAPI(host, port)
        self._refresh_lock = asyncio.Lock()

    async def refresh(
        self,
        *,
        mspconfig: bool = True,
        telemetry: bool = True,
        if_dirty: bool = True,
        if_older_than: float = 10.0,
        force: bool = False,
    ) -> None:
        """Refresh the data from the OmniLogic controller.

        Args:
            mspconfig: Whether to refresh MSPConfig data (if conditions are met)
            telemetry: Whether to refresh Telemetry data (if conditions are met)
            if_dirty: Only refresh if the data has been marked dirty
            if_older_than: Only refresh if data is older than this many seconds
            force: Force refresh regardless of dirty flag or age
        """
        async with self._refresh_lock:
            current_time = time.time()

            # Determine if mspconfig needs updating
            update_mspconfig = False
            if mspconfig:
                if force:
                    update_mspconfig = True
                elif if_dirty and self._mspconfig_dirty:
                    update_mspconfig = True
                elif (current_time - self._mspconfig_last_updated) > if_older_than:
                    update_mspconfig = True

            # Determine if telemetry needs updating
            update_telemetry = False
            if telemetry:
                if force:
                    update_telemetry = True
                elif if_dirty and self._telemetry_dirty:
                    update_telemetry = True
                elif (current_time - self._telemetry_last_updated) > if_older_than:
                    update_telemetry = True

            # Perform the updates
            if update_mspconfig:
                self.mspconfig = await self._api.async_get_mspconfig()
                self._mspconfig_last_updated = time.time()
                self._mspconfig_dirty = False

            if update_telemetry:
                self.telemetry = await self._api.async_get_telemetry()
                self._telemetry_last_updated = time.time()
                self._telemetry_dirty = False

            if update_mspconfig or update_telemetry:
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
            self.backyard = Backyard(self, self.mspconfig.backyard, self.telemetry)

        # No need for _set_omni_reference anymore - it's passed in __init__!
