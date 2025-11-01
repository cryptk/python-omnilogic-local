import asyncio
import logging
import time
from typing import Any

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.backyard import Backyard
from pyomnilogic_local.chlorinator import Chlorinator
from pyomnilogic_local.collections import EquipmentDict
from pyomnilogic_local.colorlogiclight import ColorLogicLight
from pyomnilogic_local.csad import CSAD
from pyomnilogic_local.filter import Filter
from pyomnilogic_local.heater import Heater
from pyomnilogic_local.heater_equip import HeaterEquipment
from pyomnilogic_local.models import MSPConfig, Telemetry
from pyomnilogic_local.pump import Pump
from pyomnilogic_local.relay import Relay
from pyomnilogic_local.sensor import Sensor
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
        heaters: list[Heater] = []
        for bow in self.backyard.bow.values():
            if bow.heater is not None:
                heaters.append(bow.heater)
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
        chlorinators: list[Chlorinator] = []
        for bow in self.backyard.bow.values():
            if bow.chlorinator is not None:
                chlorinators.append(bow.chlorinator)
        return EquipmentDict(chlorinators)

    @property
    def all_csads(self) -> EquipmentDict[CSAD]:
        """Returns all CSAD instances across all bows in the backyard."""
        csads: list[CSAD] = []
        for bow in self.backyard.bow.values():
            csads.extend(bow.csads.values())
        return EquipmentDict(csads)

    # Equipment search methods
    def get_equipment_by_name(self, name: str) -> OmniEquipment[Any, Any] | None:
        """
        Find equipment by name across all equipment types.

        Args:
            name: The name of the equipment to find

        Returns:
            The first equipment with matching name, or None if not found
        """
        # Search all equipment types
        all_equipment: list[OmniEquipment[Any, Any]] = []
        all_equipment.extend(self.all_lights.values())
        all_equipment.extend(self.all_relays.values())
        all_equipment.extend(self.all_pumps.values())
        all_equipment.extend(self.all_filters.values())
        all_equipment.extend(self.all_sensors.values())
        all_equipment.extend(self.all_heaters.values())
        all_equipment.extend(self.all_heater_equipment.values())
        all_equipment.extend(self.all_chlorinators.values())
        all_equipment.extend(self.all_csads.values())

        for equipment in all_equipment:
            if equipment.name == name:
                return equipment

        return None

    def get_equipment_by_id(self, system_id: int) -> OmniEquipment[Any, Any] | None:
        """
        Find equipment by system_id across all equipment types.

        Args:
            system_id: The system ID of the equipment to find

        Returns:
            The first equipment with matching system_id, or None if not found
        """
        # Search all equipment types
        all_equipment: list[OmniEquipment[Any, Any]] = []
        all_equipment.extend(self.all_lights.values())
        all_equipment.extend(self.all_relays.values())
        all_equipment.extend(self.all_pumps.values())
        all_equipment.extend(self.all_filters.values())
        all_equipment.extend(self.all_sensors.values())
        all_equipment.extend(self.all_heaters.values())
        all_equipment.extend(self.all_heater_equipment.values())
        all_equipment.extend(self.all_chlorinators.values())
        all_equipment.extend(self.all_csads.values())

        for equipment in all_equipment:
            if equipment.system_id == system_id:
                return equipment

        return None
