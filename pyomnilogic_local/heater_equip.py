from __future__ import annotations

from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPHeaterEquip
from pyomnilogic_local.models.telemetry import TelemetryHeater
from pyomnilogic_local.omnitypes import HeaterState

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic
    from pyomnilogic_local.omnitypes import HeaterType


class HeaterEquipment(OmniEquipment[MSPHeaterEquip, TelemetryHeater]):
    """Represents physical heater equipment in the OmniLogic system.

    HeaterEquipment represents an individual physical heating device (gas heater,
    heat pump, solar panel system, etc.). It is controlled by a parent VirtualHeater
    which can manage one or more physical heater units.

    The OmniLogic system uses a virtual/physical heater architecture:
    - VirtualHeater: User-facing heater control (turn_on, set_temperature, etc.)
    - HeaterEquipment: Individual physical heating devices managed by the virtual heater

    This architecture allows the system to coordinate multiple heating sources
    (e.g., solar + gas backup) under a single virtual heater interface.

    Heater Types:
        - GAS: Natural gas or propane heater (fast heating)
        - HEAT_PUMP: Electric heat pump (energy efficient)
        - SOLAR: Solar heating panels (free but weather-dependent)
        - HYBRID: Combination systems

    Attributes:
        mspconfig: Configuration data for this physical heater
        telemetry: Real-time operational state

    Properties (Configuration):
        heater_type: Type of heating unit (GAS, HEAT_PUMP, SOLAR)
        min_filter_speed: Minimum filter speed required for operation
        sensor_id: System ID of the temperature sensor
        supports_cooling: Whether this unit can cool

    Properties (Telemetry):
        state: Current heater state (OFF, ON, PAUSE)
        current_temp: Temperature reading from associated sensor (Fahrenheit)
        enabled: Whether heater is enabled
        priority: Heater priority for multi-heater systems
        maintain_for: Time to maintain current operation
        is_on: True if heater is currently running

    Example:
        >>> pool = omni.backyard.bow["Pool"]
        >>> heater = pool.heater
        >>>
        >>> # Access physical heater equipment
        >>> for equip in heater.heater_equipment:
        ...     print(f"Heater: {equip.name}")
        ...     print(f"Type: {equip.heater_type}")
        ...     print(f"State: {equip.state}")
        ...     print(f"Current temp: {equip.current_temp}°F")
        ...     print(f"Is on: {equip.is_on}")
        ...     print(f"Min filter speed: {equip.min_filter_speed}%")
        >>>
        >>> # Check for cooling support (heat pumps)
        >>> gas_heater = heater.heater_equipment["Gas Heater"]
        >>> if gas_heater.supports_cooling:
        ...     print("This unit can cool as well as heat")

    Important - Temperature Units:
        ALL temperature values are in Fahrenheit, regardless of system display
        settings. The system.units property only affects user interface display,
        not internal API values.

    Note:
        - HeaterEquipment is read-only (no direct control methods)
        - Control heaters through the parent VirtualHeater instance
        - Multiple heater equipment can work together (e.g., solar + gas)
        - Priority determines which heater runs first in multi-heater systems
        - Minimum filter speed must be met for safe heater operation
        - State transitions: OFF → ON → PAUSE (when conditions not met)
    """

    mspconfig: MSPHeaterEquip
    telemetry: TelemetryHeater

    def __init__(self, omni: OmniLogic, mspconfig: MSPHeaterEquip, telemetry: Telemetry) -> None:
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
        """Return the current temperature reading from telemetry.

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
