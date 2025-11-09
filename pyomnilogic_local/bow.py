from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.chlorinator import Chlorinator
from pyomnilogic_local.collections import EquipmentDict
from pyomnilogic_local.colorlogiclight import ColorLogicLight
from pyomnilogic_local.csad import CSAD
from pyomnilogic_local.decorators import control_method
from pyomnilogic_local.filter import Filter
from pyomnilogic_local.heater import Heater
from pyomnilogic_local.models.mspconfig import MSPBoW
from pyomnilogic_local.models.telemetry import TelemetryBoW
from pyomnilogic_local.pump import Pump
from pyomnilogic_local.relay import Relay
from pyomnilogic_local.sensor import Sensor
from pyomnilogic_local.util import OmniEquipmentNotInitializedError

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic
    from pyomnilogic_local.omnitypes import BodyOfWaterType

_LOGGER = logging.getLogger(__name__)


class Bow(OmniEquipment[MSPBoW, TelemetryBoW]):
    """Represents a Body of Water (BoW) - pool or spa - in the OmniLogic system.

    A Body of Water (commonly abbreviated as BoW) is a pool or spa, along with
    all of its associated equipment. Each BoW contains:
    - Filtration pumps
    - Heating equipment
    - Chlorination/sanitization systems
    - Chemistry monitoring (CSAD)
    - Lighting
    - Auxiliary pumps (water features, etc.)
    - Relays (jets, blowers, etc.)
    - Sensors (water temperature, flow, etc.)

    The Bow class provides access to all equipment associated with a specific
    pool or spa, as well as water temperature monitoring and spillover control
    for pool/spa combination systems.

    Attributes:
        mspconfig: Configuration data for this body of water
        telemetry: Real-time operational data
        filters: Collection of filtration pumps
        heater: Virtual heater (if configured)
        relays: Collection of relays (jets, blowers, aux equipment)
        sensors: Collection of sensors (water temp, flow, etc.)
        lights: Collection of ColorLogic lights
        pumps: Collection of pumps (water features, etc.)
        chlorinator: Chlorinator system (if configured)
        csads: Collection of CSAD (chemistry) systems

    Properties (Configuration):
        equip_type: Body of water type (BOW_POOL or BOW_SPA)
        supports_spillover: Whether spillover is available

    Properties (Telemetry):
        water_temp: Current water temperature (Fahrenheit)
        flow: True if flow is detected, False otherwise

    Control Methods:
        set_spillover(speed): Set spillover pump speed (0-100%)
        turn_on_spillover(): Turn on spillover at maximum speed
        turn_off_spillover(): Turn off spillover

    Example:
        >>> omni = OmniLogic("192.168.1.100")
        >>> await omni.refresh()
        >>>
        >>> # Access pool
        >>> pool = omni.backyard.bow["Pool"]
        >>> print(f"Water temp: {pool.water_temp}°F")
        >>> print(f"Flow detected: {pool.flow > 0}")
        >>>
        >>> # Access pool equipment
        >>> if pool.heater:
        ...     await pool.heater.set_temperature(85)
        >>>
        >>> if pool.chlorinator:
        ...     print(f"Salt level: {pool.chlorinator.avg_salt_level} ppm")
        >>>
        >>> for filter in pool.filters:
        ...     print(f"Filter: {filter.name}, Speed: {filter.speed}%")
        >>>
        >>> for light in pool.lights:
        ...     await light.set_show(ColorLogicShow25.TROPICAL)
        >>>
        >>> # Spillover control (pool/spa combo systems)
        >>> if pool.supports_spillover:
        ...     await pool.turn_on_spillover()
        ...     await pool.set_spillover(75)  # 75% speed
        ...     await pool.turn_off_spillover()

    Pool vs Spa:
        Bodies of water can be either pools or spas, distinguished by the
        equip_type property:

        >>> if pool.equip_type == BodyOfWaterType.POOL:
        ...     print("This is a pool")
        >>> elif pool.equip_type == BodyOfWaterType.SPA:
        ...     print("This is a spa")

    Spillover Systems:
        Some installations have combined pool/spa systems with spillover
        capability that allows water to flow from spa to pool or vice versa:

        - supports_spillover indicates if the feature is available
        - Spillover is controlled by a dedicated pump
        - Speed range is 0-100% (0 turns spillover off)
        - Convenience methods simplify on/off operations

    Equipment Collections:
        Equipment is stored in EquipmentDict collections which allow access by:
        - Name (string): pool.filters["Main Filter"]
        - System ID (int): pool.filters[123]
        - Index (int): pool.filters[0]
        - Iteration: for filter in pool.filters: ...

    Note:
        - Water temperature returns -1 if sensor not available
        - Flow telemetry typically reads 255 or 1 for flow, 0 for no flow, we simplify to bool
        - Not all bodies of water have all equipment types
        - Some equipment (heater, chlorinator) may be None if not configured
        - Spillover operations raise ValueError if not supported
    """

    mspconfig: MSPBoW
    telemetry: TelemetryBoW
    filters: EquipmentDict[Filter] = EquipmentDict()
    heater: Heater | None = None
    relays: EquipmentDict[Relay] = EquipmentDict()
    sensors: EquipmentDict[Sensor] = EquipmentDict()
    lights: EquipmentDict[ColorLogicLight] = EquipmentDict()
    pumps: EquipmentDict[Pump] = EquipmentDict()
    chlorinator: Chlorinator | None = None
    csads: EquipmentDict[CSAD] = EquipmentDict()

    def __init__(self, omni: OmniLogic, mspconfig: MSPBoW, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    def __repr__(self) -> str:
        """Return a string representation of the Bow for debugging.

        Returns:
            A string showing the class name, system_id, name, type, and equipment counts.
        """
        parts = [f"system_id={self.system_id!r}", f"name={self.name!r}", f"type={self.equip_type!r}"]

        # Add equipment counts
        parts.append(f"filters={len(self.filters)}")
        parts.append(f"pumps={len(self.pumps)}")
        parts.append(f"lights={len(self.lights)}")
        parts.append(f"relays={len(self.relays)}")
        parts.append(f"sensors={len(self.sensors)}")

        # Add heater and chlorinator status (present or not)
        if self.heater is not None:
            parts.append("heater=True")
        if self.chlorinator is not None:
            parts.append("chlorinator=True")
        if len(self.csads) > 0:
            parts.append(f"csads={len(self.csads)}")

        return f"Bow({', '.join(parts)})"

    @property
    def equip_type(self) -> BodyOfWaterType | str:
        """The equipment type of the bow (POOL or SPA)."""
        return self.mspconfig.equip_type

    @property
    def supports_spillover(self) -> bool:
        """Whether this body of water supports spillover functionality."""
        return self.mspconfig.supports_spillover

    @property
    def water_temp(self) -> int:
        """Current water temperature reading from the bow sensor.

        Note: Temperature is in Fahrenheit. Returns -1 if sensor is not available.
        """
        return self.telemetry.water_temp

    @property
    def flow(self) -> bool:
        """Current flow sensor reading.

        Returns:
            bool: True if flow is present, False otherwise.
        """
        # Flow values:
        # 255 seems to indicate "assumed flow", for example, because a filter pump is on
        # 1 seems to indicate "certain flow", for example, when there is an actual flow sensor
        # 0 indicates no flow
        return self.telemetry.flow > 0

    # Control methods
    @control_method
    async def set_spillover(self, speed: int) -> None:
        """Set the spillover speed for this body of water.

        Spillover allows water to flow between pool and spa. This method sets
        the speed at which the spillover pump operates.

        Args:
            speed: Spillover speed value (0-100 percent). A value of 0 will turn spillover off.

        Raises:
            OmniEquipmentNotInitializedError: If system_id is None.
            ValueError: If spillover is not supported by this body of water.
        """
        if self.system_id is None:
            msg = "Bow system_id must be set"
            raise OmniEquipmentNotInitializedError(msg)

        if not self.supports_spillover:
            msg = f"Spillover is not supported by {self.name}"
            raise ValueError(msg)

        await self._api.async_set_spillover(
            pool_id=self.system_id,
            speed=speed,
        )

    @control_method
    async def turn_on_spillover(self) -> None:
        """Turn on spillover at maximum speed (100%).

        This is a convenience method that calls set_spillover(100).

        Raises:
            OmniEquipmentNotInitializedError: If system_id is None.
            ValueError: If spillover is not supported by this body of water.
        """
        await self.set_spillover(100)

    @control_method
    async def turn_off_spillover(self) -> None:
        """Turn off spillover.

        This is a convenience method that calls set_spillover(0).

        Raises:
            OmniEquipmentNotInitializedError: If system_id is None.
            ValueError: If spillover is not supported by this body of water.
        """
        await self.set_spillover(0)

    def _update_equipment(self, mspconfig: MSPBoW, telemetry: Telemetry | None) -> None:
        """Update both the configuration and telemetry data for the equipment."""
        if telemetry is None:
            _LOGGER.warning("No telemetry provided to update Bow equipment.")
            return
        self._update_chlorinators(mspconfig, telemetry)
        self._update_csads(mspconfig, telemetry)
        self._update_filters(mspconfig, telemetry)
        self._update_heater(mspconfig, telemetry)
        self._update_lights(mspconfig, telemetry)
        self._update_pumps(mspconfig, telemetry)
        self._update_relays(mspconfig, telemetry)
        self._update_sensors(mspconfig, telemetry)

    def _update_chlorinators(self, mspconfig: MSPBoW, telemetry: Telemetry) -> None:
        """Update the chlorinators based on the MSP configuration."""
        if mspconfig.chlorinator is None:
            self.chlorinator = None
            return

        self.chlorinator = Chlorinator(self._omni, mspconfig.chlorinator, telemetry)

    def _update_csads(self, mspconfig: MSPBoW, telemetry: Telemetry) -> None:
        """Update the CSADs based on the MSP configuration."""
        if mspconfig.csad is None:
            self.csads = EquipmentDict()
            return

        self.csads = EquipmentDict([CSAD(self._omni, csad, telemetry) for csad in mspconfig.csad])

    def _update_filters(self, mspconfig: MSPBoW, telemetry: Telemetry) -> None:
        """Update the filters based on the MSP configuration."""
        if mspconfig.filter is None:
            self.filters = EquipmentDict()
            return

        self.filters = EquipmentDict([Filter(self._omni, filter_, telemetry) for filter_ in mspconfig.filter])

    def _update_heater(self, mspconfig: MSPBoW, telemetry: Telemetry) -> None:
        """Update the heater based on the MSP configuration."""
        if mspconfig.heater is None:
            self.heater = None
            return

        self.heater = Heater(self._omni, mspconfig.heater, telemetry)

    def _update_lights(self, mspconfig: MSPBoW, telemetry: Telemetry) -> None:
        """Update the lights based on the MSP configuration."""
        if mspconfig.colorlogic_light is None:
            self.lights = EquipmentDict()
            return

        self.lights = EquipmentDict([ColorLogicLight(self._omni, light, telemetry) for light in mspconfig.colorlogic_light])

    def _update_pumps(self, mspconfig: MSPBoW, telemetry: Telemetry) -> None:
        """Update the pumps based on the MSP configuration."""
        if mspconfig.pump is None:
            self.pumps = EquipmentDict()
            return

        self.pumps = EquipmentDict([Pump(self._omni, pump, telemetry) for pump in mspconfig.pump])

    def _update_relays(self, mspconfig: MSPBoW, telemetry: Telemetry) -> None:
        """Update the relays based on the MSP configuration."""
        if mspconfig.relay is None:
            self.relays = EquipmentDict()
            return

        self.relays = EquipmentDict([Relay(self._omni, relay, telemetry) for relay in mspconfig.relay])

    def _update_sensors(self, mspconfig: MSPBoW, telemetry: Telemetry) -> None:
        """Update the sensors based on the MSP configuration."""
        if mspconfig.sensor is None:
            self.sensors = EquipmentDict()
            return

        self.sensors = EquipmentDict([Sensor(self._omni, sensor, telemetry) for sensor in mspconfig.sensor])
