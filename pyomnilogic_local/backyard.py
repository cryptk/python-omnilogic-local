import logging

from pyomnilogic_local.api.api import OmniLogicAPI
from pyomnilogic_local.collections import EquipmentDict
from pyomnilogic_local.models.mspconfig import MSPBackyard
from pyomnilogic_local.models.telemetry import Telemetry, TelemetryBackyard

from ._base import OmniEquipment
from .bow import Bow
from .colorlogiclight import ColorLogicLight
from .relay import Relay
from .sensor import Sensor

_LOGGER = logging.getLogger(__name__)


class Backyard(OmniEquipment[MSPBackyard, TelemetryBackyard]):
    """Represents the backyard equipment in the OmniLogic system."""

    bow: EquipmentDict[Bow] = EquipmentDict()
    lights: EquipmentDict[ColorLogicLight] = EquipmentDict()
    relays: EquipmentDict[Relay] = EquipmentDict()
    sensors: EquipmentDict[Sensor] = EquipmentDict()

    def __init__(self, _api: OmniLogicAPI, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        super().__init__(_api, mspconfig, telemetry)

    def _update_equipment(self, mspconfig: MSPBackyard, telemetry: Telemetry | None) -> None:
        """Update both the configuration and telemetry data for the equipment."""
        if telemetry is None:
            _LOGGER.warning("No telemetry provided to update Backyard equipment.")
            return
        self._update_bows(mspconfig, telemetry)
        self._update_lights(mspconfig, telemetry)
        self._update_relays(mspconfig, telemetry)
        self._update_sensors(mspconfig, telemetry)

    def _update_bows(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the bows based on the MSP configuration."""
        if mspconfig.bow is None:
            self.bow = EquipmentDict()
            return

        self.bow = EquipmentDict([Bow(self._api, bow, telemetry) for bow in mspconfig.bow])

    def _update_lights(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the lights based on the MSP configuration."""
        if mspconfig.colorlogic_light is None:
            self.lights = EquipmentDict()
            return

        self.lights = EquipmentDict([ColorLogicLight(self._api, light, telemetry) for light in mspconfig.colorlogic_light])

    def _update_relays(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the relays based on the MSP configuration."""
        if mspconfig.relay is None:
            self.relays = EquipmentDict()
            return

        self.relays = EquipmentDict([Relay(self._api, relay, telemetry) for relay in mspconfig.relay])

    def _update_sensors(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the sensors based on the MSP configuration."""
        if mspconfig.sensor is None:
            self.sensors = EquipmentDict()
            return

        self.sensors = EquipmentDict([Sensor(self._api, sensor, telemetry) for sensor in mspconfig.sensor])
