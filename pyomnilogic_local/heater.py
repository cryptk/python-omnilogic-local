from __future__ import annotations

from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.collections import EquipmentDict
from pyomnilogic_local.decorators import control_method
from pyomnilogic_local.heater_equip import HeaterEquipment
from pyomnilogic_local.models.mspconfig import MSPVirtualHeater
from pyomnilogic_local.models.telemetry import TelemetryVirtualHeater
from pyomnilogic_local.util import OmniEquipmentNotInitializedError

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic
    from pyomnilogic_local.omnitypes import HeaterMode


class Heater(OmniEquipment[MSPVirtualHeater, TelemetryVirtualHeater]):
    """Represents a heater system in the OmniLogic system.

    A heater maintains water temperature by heating pool or spa water to a
    configured set point. The OmniLogic system supports various heater types:
    - Gas heaters (natural gas or propane)
    - Heat pumps (electric, energy efficient)
    - Solar heaters (passive solar collection)
    - Hybrid systems (combination of multiple heater types)

    The Heater class is actually a "virtual heater" that can manage one or more
    physical heater equipment units. It provides temperature control, mode
    selection, and monitoring of heater operation.

    Attributes:
        mspconfig: Configuration data for this heater from MSP XML
        telemetry: Real-time operational data and state
        heater_equipment: Collection of physical heater units (HeaterEquipment)

    Properties (Configuration):
        max_temp: Maximum settable temperature (Fahrenheit)
        min_temp: Minimum settable temperature (Fahrenheit)

    Properties (Telemetry):
        mode: Current heater mode (OFF, HEAT, AUTO, etc.)
        current_set_point: Current target temperature (Fahrenheit)
        solar_set_point: Solar heater target temperature (Fahrenheit)
        enabled: Whether heater is enabled
        silent_mode: Silent mode setting (reduced noise operation)
        why_on: Reason code for heater being on
        is_on: True if heater is enabled

    Control Methods:
        turn_on(): Enable the heater
        turn_off(): Disable the heater
        set_temperature(temp): Set target temperature (Fahrenheit)
        set_solar_temperature(temp): Set solar target temperature (Fahrenheit)

    Example:
        >>> pool = omni.backyard.bow["Pool"]
        >>> heater = pool.heater
        >>>
        >>> # Check current state
        >>> print(f"Heater enabled: {heater.is_on}")
        >>> print(f"Current set point: {heater.current_set_point}°F")
        >>> print(f"Mode: {heater.mode}")
        >>>
        >>> # Control heater
        >>> await heater.turn_on()
        >>> await heater.set_temperature(85)  # Set to 85°F
        >>>
        >>> # For systems with solar heaters
        >>> if heater.solar_set_point > 0:
        ...     await heater.set_solar_temperature(90)
        >>>
        >>> await heater.turn_off()
        >>>
        >>> # Access physical heater equipment
        >>> for equip in heater.heater_equipment:
        ...     print(f"Heater: {equip.name}, Type: {equip.equip_type}")

    Important - Temperature Units:
        ALL temperature values in the OmniLogic API are in Fahrenheit, regardless
        of the display units configured in the system. This is an internal API
        requirement and cannot be changed.

        - All temperature properties return Fahrenheit values
        - All temperature parameters must be provided in Fahrenheit
        - Use system.units to determine display preference (not API units)
        - If your application uses Celsius, convert before calling these methods

        Example conversion:
            >>> # If working in Celsius
            >>> celsius_target = 29
            >>> fahrenheit_target = (celsius_target * 9/5) + 32
            >>> await heater.set_temperature(int(fahrenheit_target))

    Note:
        - Temperature range is enforced (min_temp to max_temp)
        - Multiple physical heaters may be grouped under one virtual heater
        - Solar heaters have separate set points from gas/heat pump heaters
        - Heater may not turn on immediately if water temp is already at set point
    """

    mspconfig: MSPVirtualHeater
    telemetry: TelemetryVirtualHeater
    heater_equipment: EquipmentDict[HeaterEquipment] = EquipmentDict()

    def __init__(self, omni: OmniLogic, mspconfig: MSPVirtualHeater, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    def _update_equipment(self, mspconfig: MSPVirtualHeater, telemetry: Telemetry | None) -> None:
        """Update both the configuration and telemetry data for the equipment."""
        if telemetry is None:
            return
        self._update_heater_equipment(mspconfig, telemetry)

    def _update_heater_equipment(self, mspconfig: MSPVirtualHeater, telemetry: Telemetry) -> None:
        """Update the heater equipment based on the MSP configuration."""
        if mspconfig.heater_equipment is None:
            self.heater_equipment = EquipmentDict()
            return

        self.heater_equipment = EquipmentDict([HeaterEquipment(self._omni, equip, telemetry) for equip in mspconfig.heater_equipment])

    @property
    def max_temp(self) -> int:
        """Returns the maximum settable temperature.

        Note: Temperature is always in Fahrenheit internally.
        Use the system.units property to determine if conversion to Celsius is needed for display.
        """
        return self.mspconfig.max_temp

    @property
    def min_temp(self) -> int:
        """Returns the minimum settable temperature.

        Note: Temperature is always in Fahrenheit internally.
        Use the system.units property to determine if conversion to Celsius is needed for display.
        """
        return self.mspconfig.min_temp

    @property
    def mode(self) -> HeaterMode | int:
        """Returns the current heater mode from telemetry."""
        return self.telemetry.mode

    @property
    def current_set_point(self) -> int:
        """Returns the current set point from telemetry.

        Note: Temperature is always in Fahrenheit internally.
        Use the system.units property to determine if conversion to Celsius is needed for display.
        """
        return self.telemetry.current_set_point

    @property
    def solar_set_point(self) -> int:
        """Returns the solar set point from telemetry.

        Note: Temperature is always in Fahrenheit internally.
        Use the system.units property to determine if conversion to Celsius is needed for display.
        """
        return self.telemetry.solar_set_point

    @property
    def enabled(self) -> bool:
        """Returns whether the heater is enabled from telemetry."""
        return self.telemetry.enabled

    @property
    def silent_mode(self) -> int:
        """Returns the silent mode setting from telemetry."""
        return self.telemetry.silent_mode

    @property
    def why_on(self) -> int:
        """Returns the reason why the heater is on from telemetry."""
        return self.telemetry.why_on

    @property
    def is_on(self) -> bool:
        """Returns whether the heater is currently enabled (from telemetry)."""
        return self.telemetry.enabled

    @control_method
    async def turn_on(self) -> None:
        """Turn the heater on (enables it).

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            OmniEquipmentNotReadyError: If the equipment is not ready to accept commands.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Cannot turn on heater: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)
        await self._api.async_set_heater_enable(self.bow_id, self.system_id, True)

    @control_method
    async def turn_off(self) -> None:
        """Turn the heater off (disables it).

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            OmniEquipmentNotReadyError: If the equipment is not ready to accept commands.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Cannot turn off heater: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)
        await self._api.async_set_heater_enable(self.bow_id, self.system_id, False)

    @control_method
    async def set_temperature(self, temperature: int) -> None:
        """Set the target temperature for the heater.

        Args:
            temperature: The target temperature to set in Fahrenheit.
                        Must be between min_temp and max_temp.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            OmniEquipmentNotReadyError: If the equipment is not ready to accept commands.
            ValueError: If temperature is outside the valid range.

        Note:
            Temperature must be provided in Fahrenheit as that is what the OmniLogic
            system uses internally. The system.units setting only affects display,
            not the API. If your application uses Celsius, you must convert to
            Fahrenheit before calling this method.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Cannot set heater temperature: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)

        if temperature < self.min_temp or temperature > self.max_temp:
            msg = f"Temperature {temperature}°F is outside valid range [{self.min_temp}°F, {self.max_temp}°F]"
            raise ValueError(msg)

        # Always use Fahrenheit as that's what the OmniLogic system uses internally
        await self._api.async_set_heater(self.bow_id, self.system_id, temperature)

    @control_method
    async def set_solar_temperature(self, temperature: int) -> None:
        """Set the solar heater set point.

        Args:
            temperature: The target solar temperature to set in Fahrenheit.
                        Must be between min_temp and max_temp.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            OmniEquipmentNotReadyError: If the equipment is not ready to accept commands.
            ValueError: If temperature is outside the valid range.

        Note:
            Temperature must be provided in Fahrenheit as that is what the OmniLogic
            system uses internally. The system.units setting only affects display,
            not the API. If your application uses Celsius, you must convert to
            Fahrenheit before calling this method.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Cannot set solar heater temperature: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)

        if temperature < self.min_temp or temperature > self.max_temp:
            msg = f"Temperature {temperature}°F is outside valid range [{self.min_temp}°F, {self.max_temp}°F]"
            raise ValueError(msg)

        # Always use Fahrenheit as that's what the OmniLogic system uses internally
        await self._api.async_set_solar_heater(self.bow_id, self.system_id, temperature)
