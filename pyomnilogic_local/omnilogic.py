from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.api.constants import DEFAULT_RESPONSE_TIMEOUT
from pyomnilogic_local.backyard import Backyard
from pyomnilogic_local.collections import EquipmentDict
from pyomnilogic_local.groups import Group
from pyomnilogic_local.schedule import Schedule
from pyomnilogic_local.system import System

if TYPE_CHECKING:
    from pyomnilogic_local._base import OmniEquipment
    from pyomnilogic_local.bow import Bow
    from pyomnilogic_local.chlorinator import Chlorinator
    from pyomnilogic_local.chlorinator_equip import ChlorinatorEquipment
    from pyomnilogic_local.colorlogiclight import ColorLogicLight
    from pyomnilogic_local.csad import CSAD
    from pyomnilogic_local.csad_equip import CSADEquipment
    from pyomnilogic_local.filter import Filter
    from pyomnilogic_local.heater import Heater
    from pyomnilogic_local.heater_equip import HeaterEquipment
    from pyomnilogic_local.models import MSPConfig, Telemetry
    from pyomnilogic_local.pump import Pump
    from pyomnilogic_local.relay import Relay
    from pyomnilogic_local.sensor import Sensor


_LOGGER = logging.getLogger(__name__)


class OmniLogic:
    mspconfig: MSPConfig
    telemetry: Telemetry

    system: System
    backyard: Backyard
    groups: EquipmentDict[Group]
    schedules: EquipmentDict[Schedule]

    _mspconfig_last_updated: float = 0.0
    _telemetry_last_updated: float = 0.0
    _mspconfig_checksum: int = 0
    _telemetry_dirty: bool = True
    _refresh_lock: asyncio.Lock
    # This is the minimum supported MSP version for full functionality
    # we just string match the value from the start of the string
    _min_mspversion: str = "R05"
    _warned_mspversion: bool = False

    def __init__(self, host: str, port: int = 10444, timeout: float = DEFAULT_RESPONSE_TIMEOUT) -> None:
        self.host = host
        self.port = port

        self._api = OmniLogicAPI(host, port, timeout)
        self._refresh_lock = asyncio.Lock()

    def __repr__(self) -> str:
        """Return a string representation of the OmniLogic instance for debugging.

        Returns:
            A string showing host, port, and counts of various equipment types.
        """
        # Only show equipment counts if backyard has been initialized
        if hasattr(self, "backyard"):
            bow_count = len(self.backyard.bow)
            light_count = len(self.all_lights)
            relay_count = len(self.all_relays)
            pump_count = len(self.all_pumps)
            filter_count = len(self.all_filters)

            return (
                f"OmniLogic(host={self.host!r}, port={self.port}, "
                f"bows={bow_count}, lights={light_count}, relays={relay_count}, "
                f"pumps={pump_count}, filters={filter_count})"
            )
        return f"OmniLogic(host={self.host!r}, port={self.port}, not_initialized=True)"

    async def refresh(
        self,
        *,
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

            # Determine if telemetry needs updating
            update_telemetry = False
            if force or (if_dirty and self._telemetry_dirty) or ((current_time - self._telemetry_last_updated) > if_older_than):
                update_telemetry = True

            # Update telemetry if needed
            if update_telemetry:
                self.telemetry = await self._api.async_get_telemetry()
                self._telemetry_last_updated = time.time()
                self._telemetry_dirty = False

            # Determine if MSPConfig needs updating
            update_mspconfig = False
            if force:
                update_mspconfig = True
            if self.telemetry.backyard.config_checksum != self._mspconfig_checksum:
                update_mspconfig = True

            if (
                self.telemetry.backyard.msp_version is not None
                and not self._warned_mspversion
                and not self.telemetry.backyard.msp_version.startswith(self._min_mspversion)
            ):
                _LOGGER.warning(
                    "Detected OmniLogic MSP version %s, which is below the minimum supported version %s. "
                    "Some features may not work correctly. Please consider updating your OmniLogic controller firmware.",
                    self.telemetry.backyard.msp_version,
                    self._min_mspversion,
                )
                self._warned_mspversion = True

            # Update MSPConfig if needed
            if update_mspconfig:
                self.mspconfig = await self._api.async_get_mspconfig()
                self._mspconfig_last_updated = time.time()
                self._mspconfig_checksum = self.telemetry.backyard.config_checksum

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

        # Update groups
        if self.mspconfig.groups is None:
            self.groups = EquipmentDict()
        else:
            self.groups = EquipmentDict([Group(self, group_, self.telemetry) for group_ in self.mspconfig.groups])

        # Update schedules
        if self.mspconfig.schedules is None:
            self.schedules = EquipmentDict()
        else:
            self.schedules = EquipmentDict([Schedule(self, schedule_, self.telemetry) for schedule_ in self.mspconfig.schedules])

    # Equipment discovery properties
    @property
    def all_lights(self) -> EquipmentDict[ColorLogicLight]:
        """Returns all ColorLogicLight instances across all bows in the backyard."""
        lights: list[ColorLogicLight] = []
        # Lights at backyard level
        lights.extend(self.backyard.lights.values())
        # Lights in each bow
        for bow in self.backyard.bow.values():
            lights.extend(bow.lights.values())
        return EquipmentDict(lights)

    @property
    def all_relays(self) -> EquipmentDict[Relay]:
        """Returns all Relay instances across all bows in the backyard."""
        relays: list[Relay] = []
        # Relays at backyard level
        relays.extend(self.backyard.relays.values())
        # Relays in each bow
        for bow in self.backyard.bow.values():
            relays.extend(bow.relays.values())
        return EquipmentDict(relays)

    @property
    def all_pumps(self) -> EquipmentDict[Pump]:
        """Returns all Pump instances across all bows in the backyard."""
        pumps: list[Pump] = []
        for bow in self.backyard.bow.values():
            pumps.extend(bow.pumps.values())
        return EquipmentDict(pumps)

    @property
    def all_filters(self) -> EquipmentDict[Filter]:
        """Returns all Filter instances across all bows in the backyard."""
        filters: list[Filter] = []
        for bow in self.backyard.bow.values():
            filters.extend(bow.filters.values())
        return EquipmentDict(filters)

    @property
    def all_sensors(self) -> EquipmentDict[Sensor]:
        """Returns all Sensor instances across all bows in the backyard."""
        sensors: list[Sensor] = []
        # Sensors at backyard level
        sensors.extend(self.backyard.sensors.values())
        # Sensors in each bow
        for bow in self.backyard.bow.values():
            sensors.extend(bow.sensors.values())
        return EquipmentDict(sensors)

    @property
    def all_heaters(self) -> EquipmentDict[Heater]:
        """Returns all Heater (VirtualHeater) instances across all bows in the backyard."""
        heaters = [bow.heater for bow in self.backyard.bow.values() if bow.heater is not None]
        return EquipmentDict(heaters)

    @property
    def all_heater_equipment(self) -> EquipmentDict[HeaterEquipment]:
        """Returns all HeaterEquipment instances across all heaters in the backyard."""
        heater_equipment: list[HeaterEquipment] = []
        for heater in self.all_heaters.values():
            heater_equipment.extend(heater.heater_equipment.values())
        return EquipmentDict(heater_equipment)

    @property
    def all_chlorinators(self) -> EquipmentDict[Chlorinator]:
        """Returns all Chlorinator instances across all bows in the backyard."""
        chlorinators = [bow.chlorinator for bow in self.backyard.bow.values() if bow.chlorinator is not None]
        return EquipmentDict(chlorinators)

    @property
    def all_chlorinator_equipment(self) -> EquipmentDict[ChlorinatorEquipment]:
        """Returns all ChlorinatorEquipment instances across all chlorinators in the backyard."""
        chlorinator_equipment: list[ChlorinatorEquipment] = []
        for chlorinator in self.all_chlorinators.values():
            chlorinator_equipment.extend(chlorinator.chlorinator_equipment.values())
        return EquipmentDict(chlorinator_equipment)

    @property
    def all_csad_equipment(self) -> EquipmentDict[CSADEquipment]:
        """Returns all CSADEquipment instances across all CSADs in the backyard."""
        csad_equipment: list[CSADEquipment] = []
        for csad in self.all_csads.values():
            csad_equipment.extend(csad.csad_equipment.values())
        return EquipmentDict(csad_equipment)

    @property
    def all_csads(self) -> EquipmentDict[CSAD]:
        """Returns all CSAD instances across all bows in the backyard."""
        csads: list[CSAD] = []
        for bow in self.backyard.bow.values():
            csads.extend(bow.csads.values())
        return EquipmentDict(csads)

    @property
    def all_bows(self) -> EquipmentDict[Bow]:
        """Returns all Bow instances across all bows in the backyard."""
        # Bows are stored directly in backyard as EquipmentDict already
        return self.backyard.bow

    # Equipment search methods
    def get_equipment_by_name(self, name: str) -> OmniEquipment[Any, Any] | None:
        """Find equipment by name across all equipment types.

        Args:
            name: The name of the equipment to find

        Returns:
            The first equipment with matching name, or None if not found
        """
        # Search all equipment types
        all_equipment: list[OmniEquipment[Any, Any]] = []
        all_equipment.extend([self.backyard])
        all_equipment.extend(self.all_lights.values())
        all_equipment.extend(self.all_relays.values())
        all_equipment.extend(self.all_pumps.values())
        all_equipment.extend(self.all_filters.values())
        all_equipment.extend(self.all_sensors.values())
        all_equipment.extend(self.all_heaters.values())
        all_equipment.extend(self.all_heater_equipment.values())
        all_equipment.extend(self.all_chlorinators.values())
        all_equipment.extend(self.all_chlorinator_equipment.values())
        all_equipment.extend(self.all_csads.values())
        all_equipment.extend(self.all_csad_equipment.values())
        all_equipment.extend(self.all_bows.values())
        all_equipment.extend(self.groups.values())

        for equipment in all_equipment:
            if equipment.name == name:
                return equipment

        return None

    def get_equipment_by_id(self, system_id: int) -> OmniEquipment[Any, Any] | None:
        """Find equipment by system_id across all equipment types.

        Args:
            system_id: The system ID of the equipment to find

        Returns:
            The first equipment with matching system_id, or None if not found
        """
        # Search all equipment types
        all_equipment: list[OmniEquipment[Any, Any]] = []
        all_equipment.extend([self.backyard])
        all_equipment.extend(self.all_lights.values())
        all_equipment.extend(self.all_relays.values())
        all_equipment.extend(self.all_pumps.values())
        all_equipment.extend(self.all_filters.values())
        all_equipment.extend(self.all_sensors.values())
        all_equipment.extend(self.all_heaters.values())
        all_equipment.extend(self.all_heater_equipment.values())
        all_equipment.extend(self.all_chlorinators.values())
        all_equipment.extend(self.all_chlorinator_equipment.values())
        all_equipment.extend(self.all_csads.values())
        all_equipment.extend(self.all_csad_equipment.values())
        all_equipment.extend(self.all_bows.values())
        all_equipment.extend(self.groups.values())
        all_equipment.extend(self.schedules.values())

        for equipment in all_equipment:
            if equipment.system_id == system_id:
                return equipment

        return None
