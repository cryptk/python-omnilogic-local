import logging
from typing import TYPE_CHECKING

from pyomnilogic_local.collections import EquipmentDict
from pyomnilogic_local.models.mspconfig import MSPBackyard
from pyomnilogic_local.models.telemetry import Telemetry, TelemetryBackyard
from pyomnilogic_local.omnitypes import BackyardState

from ._base import OmniEquipment
from .bow import Bow
from .colorlogiclight import ColorLogicLight
from .relay import Relay
from .sensor import Sensor

if TYPE_CHECKING:
    from pyomnilogic_local.omnilogic import OmniLogic

_LOGGER = logging.getLogger(__name__)


class Backyard(OmniEquipment[MSPBackyard, TelemetryBackyard]):
    """Represents the backyard equipment in the OmniLogic system."""

    mspconfig: MSPBackyard
    telemetry: TelemetryBackyard
    bow: EquipmentDict[Bow] = EquipmentDict()
    lights: EquipmentDict[ColorLogicLight] = EquipmentDict()
    relays: EquipmentDict[Relay] = EquipmentDict()
    sensors: EquipmentDict[Sensor] = EquipmentDict()

    def __init__(self, omni: "OmniLogic", mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    @property
    def status_version(self) -> int:
        """Telemetry status version number."""
        return self.telemetry.status_version

    @property
    def air_temp(self) -> int | None:
        """Current air temperature reading from the backyard sensor.

        Note: Temperature is in Fahrenheit. May be None if sensor is not available.
        """
        return self.telemetry.air_temp

    @property
    def state(self) -> BackyardState:
        """Current backyard state (OFF, ON, SERVICE_MODE, CONFIG_MODE, TIMED_SERVICE_MODE)."""
        return self.telemetry.state

    @property
    def config_checksum(self) -> int | None:
        """Configuration checksum value.

        Note: Only available when status_version >= 11. Returns None otherwise.
        """
        return self.telemetry.config_checksum

    @property
    def msp_version(self) -> str | None:
        """MSP firmware version string.

        Note: Only available when status_version >= 11. Returns None otherwise.
        Example: "R0408000"
        """
        return self.telemetry.msp_version

    @property
    def is_service_mode(self) -> bool:
        """Check if the backyard is in any service mode.

        Returns:
            True if in SERVICE_MODE, CONFIG_MODE, or TIMED_SERVICE_MODE, False otherwise
        """
        return self.state in (
            BackyardState.SERVICE_MODE,
            BackyardState.CONFIG_MODE,
            BackyardState.TIMED_SERVICE_MODE,
        )

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

        self.bow = EquipmentDict([Bow(self._omni, bow, telemetry) for bow in mspconfig.bow])

    def _update_lights(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the lights based on the MSP configuration."""
        if mspconfig.colorlogic_light is None:
            self.lights = EquipmentDict()
            return

        self.lights = EquipmentDict([ColorLogicLight(self._omni, light, telemetry) for light in mspconfig.colorlogic_light])

    def _update_relays(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the relays based on the MSP configuration."""
        if mspconfig.relay is None:
            self.relays = EquipmentDict()
            return

        self.relays = EquipmentDict([Relay(self._omni, relay, telemetry) for relay in mspconfig.relay])

    def _update_sensors(self, mspconfig: MSPBackyard, telemetry: Telemetry) -> None:
        """Update the sensors based on the MSP configuration."""
        if mspconfig.sensor is None:
            self.sensors = EquipmentDict()
            return

        self.sensors = EquipmentDict([Sensor(self._omni, sensor, telemetry) for sensor in mspconfig.sensor])
