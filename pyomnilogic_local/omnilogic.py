import asyncio
import logging
import time

from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.backyard import Backyard
from pyomnilogic_local.models import MSPConfig, Telemetry
from pyomnilogic_local.system import System

_LOGGER = logging.getLogger(__name__)


class OmniLogic:
    auto_refresh_enabled: bool = True

    mspconfig: MSPConfig
    telemetry: Telemetry

    system: System
    backyard: Backyard

    _mspconfig_last_updated: float = 0.0
    _telemetry_last_updated: float = 0.0
    _refresh_lock: asyncio.Lock

    def __init__(self, host: str, port: int = 10444) -> None:
        self.host = host
        self.port = port

        self._api = OmniLogicAPI(host, port)
        self._refresh_lock = asyncio.Lock()

    async def refresh(self, update_mspconfig: bool = True, update_telemetry: bool = True) -> None:
        """Refresh the data from the OmniLogic controller.

        Args:
            update_mspconfig: Whether to fetch and update MSPConfig data
            update_telemetry: Whether to fetch and update Telemetry data
        """
        if update_mspconfig:
            self.mspconfig = await self._api.async_get_mspconfig()
            self._mspconfig_last_updated = time.time()
        if update_telemetry:
            self.telemetry = await self._api.async_get_telemetry()
            self._telemetry_last_updated = time.time()

        self._update_equipment()

    # async def refresh_mspconfig(self) -> None:
    #     """Refresh only the MSPConfig data from the OmniLogic controller."""
    #     self.mspconfig = await self._api.async_get_mspconfig()
    #     self._mspconfig_last_updated = time.time()
    #     self._update_equipment()

    # async def refresh_telemetry(self) -> None:
    #     """Refresh only the Telemetry data from the OmniLogic controller."""
    #     self.telemetry = await self._api.async_get_telemetry()
    #     self._telemetry_last_updated = time.time()
    #     self._update_equipment()

    async def update_if_older_than(
        self,
        telemetry_min_time: float | None = None,
        mspconfig_min_time: float | None = None,
    ) -> None:
        """Update telemetry/mspconfig only if older than specified timestamp.

        This method uses a lock to ensure only one refresh happens at a time.
        If another thread/task already updated the data to be newer than required,
        this method will skip the update.

        Args:
            telemetry_min_time: Update telemetry if last updated before this timestamp
            mspconfig_min_time: Update mspconfig if last updated before this timestamp
        """
        async with self._refresh_lock:
            needs_telemetry = telemetry_min_time and self._telemetry_last_updated < telemetry_min_time
            needs_mspconfig = mspconfig_min_time and self._mspconfig_last_updated < mspconfig_min_time

            if needs_telemetry or needs_mspconfig:
                await self.refresh(
                    update_mspconfig=bool(needs_mspconfig),
                    update_telemetry=bool(needs_telemetry),
                )

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
