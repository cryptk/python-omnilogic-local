from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPHeaterEquip
from pyomnilogic_local.models.telemetry import Telemetry, TelemetryHeater
from pyomnilogic_local.omnitypes import HeaterState, HeaterType

if TYPE_CHECKING:
    from pyomnilogic_local.omnilogic import OmniLogic


class HeaterEquipment(OmniEquipment[MSPHeaterEquip, TelemetryHeater]):
    """
    Represents a heater equipment in the OmniLogic system.

    This is the physical heater equipment (gas, heat pump, solar, etc.) that is
    controlled by a VirtualHeater. A VirtualHeater can have one or more HeaterEquipment
    instances associated with it.

    Note: Temperature is always in Fahrenheit internally.
    """

    mspconfig: MSPHeaterEquip
    telemetry: TelemetryHeater

    def __init__(self, omni: "OmniLogic", mspconfig: MSPHeaterEquip, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    @property
    def heater_type(self) -> HeaterType:
        """Returns the type of heater (GAS, HEAT_PUMP, SOLAR, etc.)."""
        return self.mspconfig.heater_type

    @property
    def min_filter_speed(self) -> int:
        """Returns the minimum filter speed required for heater operation."""
        return self.mspconfig.min_filter_speed

    @property
    def sensor_id(self) -> int:
        """Returns the system ID of the sensor associated with this heater."""
        return self.mspconfig.sensor_id

    @property
    def supports_cooling(self) -> bool | None:
        """Returns whether the heater supports cooling mode, if available."""
        return self.mspconfig.supports_cooling

    @property
    def state(self) -> HeaterState | int:
        """Returns the current state of the heater equipment (OFF, ON, or PAUSE)."""
        return self.telemetry.state

    @property
    def current_temp(self) -> int:
        """
        Returns the current temperature reading from telemetry.

        Note: Temperature is always in Fahrenheit internally.
        Use the system.units property to determine if conversion to Celsius is needed for display.
        """
        return self.telemetry.temp

    @property
    def enabled(self) -> bool:
        """Returns whether the heater equipment is enabled from telemetry."""
        return self.telemetry.enabled

    @property
    def priority(self) -> int:
        """Returns the priority of this heater equipment."""
        return self.telemetry.priority

    @property
    def maintain_for(self) -> int:
        """Returns the maintain_for value from telemetry."""
        return self.telemetry.maintain_for

    @property
    def is_on(self) -> bool:
        """Returns whether the heater equipment is currently on."""
        return self.state == HeaterState.ON
