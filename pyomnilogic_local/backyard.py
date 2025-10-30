from pyomnilogic_local.api.api import OmniLogicAPI
from pyomnilogic_local.models.mspconfig import MSPBackyard
from pyomnilogic_local.models.telemetry import Telemetry, TelemetryBackyard

from ._base import OmniEquipment
from .bow import Bow
from .colorlogiclight import ColorLogicLight
from .relay import Relay
from .sensor import Sensor


class Backyard(OmniEquipment[MSPBackyard, TelemetryBackyard]):
    """Represents the backyard equipment in the OmniLogic system."""

    bow: list[Bow] = []
    lights: list[ColorLogicLight] = []
    relays: list[Relay] = []
    sensors: list[Sensor] = []

    def __init__(self, _api: OmniLogicAPI, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        super().__init__(_api, mspconfig, telemetry)

        self._update_bows(mspconfig, telemetry)
        self._update_relays(mspconfig, telemetry)
        self._update_sensors(mspconfig, telemetry)

    def _update_bows(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the bows based on the MSP configuration."""
        if mspconfig.bow is None:
            self.bow = []
            return

        self.bow = [Bow(self._api, bow, telemetry) for bow in mspconfig.bow]

    def _update_relays(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the relays based on the MSP configuration."""
        if mspconfig.relay is None:
            self.relays = []
            return

        self.relays = [Relay(self._api, relay, telemetry) for relay in mspconfig.relay]

    def _update_sensors(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the sensors based on the MSP configuration."""
        if mspconfig.sensor is None:
            self.sensors = []
            return

        self.sensors = [Sensor(self._api, sensor, telemetry) for sensor in mspconfig.sensor]
