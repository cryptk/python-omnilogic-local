from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.chlorinator import Chlorinator
from pyomnilogic_local.collections import EquipmentDict
from pyomnilogic_local.colorlogiclight import _LOGGER, ColorLogicLight
from pyomnilogic_local.csad import CSAD
from pyomnilogic_local.filter import Filter
from pyomnilogic_local.heater import Heater
from pyomnilogic_local.models.mspconfig import MSPBoW
from pyomnilogic_local.models.telemetry import Telemetry, TelemetryBoW
from pyomnilogic_local.omnitypes import BodyOfWaterType
from pyomnilogic_local.pump import Pump
from pyomnilogic_local.relay import Relay
from pyomnilogic_local.sensor import Sensor

if TYPE_CHECKING:
    from pyomnilogic_local.omnilogic import OmniLogic


class Bow(OmniEquipment[MSPBoW, TelemetryBoW]):
    """Represents a bow in the OmniLogic system."""

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

    def __init__(self, omni: "OmniLogic", mspconfig: MSPBoW, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

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
    def flow(self) -> int:
        """Current flow sensor reading.

        Returns:
            Flow value (255 typically indicates flow present, 0 indicates no flow)
        """
        return self.telemetry.flow

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
