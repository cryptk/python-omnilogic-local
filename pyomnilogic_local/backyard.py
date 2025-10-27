from pyomnilogic_local.models.mspconfig import MSPBackyard
from pyomnilogic_local.models.telemetry import Telemetry

from ._base import OmniEquipment
from .bow import Bow
from .colorlogiclight import ColorLogicLight
from .relay import Relay
from .sensor import Sensor


class Backyard(OmniEquipment):
    """Represents the backyard equipment in the OmniLogic system."""

    bow: list[Bow] = []
    lights: list[ColorLogicLight] = []
    relays: list[Relay] = []
    sensors: list[Sensor] = []

    def __init__(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        super().__init__(mspconfig, telemetry)

        self._update_bows(mspconfig, telemetry)
        self._update_relays(mspconfig, telemetry)
        self._update_sensors(mspconfig, telemetry)

    def _update_bows(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the bows based on the MSP configuration."""
        if mspconfig.bow is None:
            self.bow = []
            return

        self.bow = [Bow(bow, telemetry) for bow in mspconfig.bow]

    def _update_relays(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the relays based on the MSP configuration."""
        if mspconfig.relay is None:
            self.relays = []
            return

        self.relays = [Relay(relay, telemetry) for relay in mspconfig.relay]

    def _update_sensors(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the sensors, bows, lights, and relays based on the MSP configuration."""
        if mspconfig.sensor is None:
            self.sensors = []
            return

        self.sensors = [Sensor(sensor, telemetry) for sensor in mspconfig.sensor]
