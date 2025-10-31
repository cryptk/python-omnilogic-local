from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.collections import EquipmentDict
from pyomnilogic_local.decorators import dirties_state
from pyomnilogic_local.heater_equip import HeaterEquipment
from pyomnilogic_local.models.mspconfig import MSPVirtualHeater
from pyomnilogic_local.models.telemetry import Telemetry, TelemetryVirtualHeater
from pyomnilogic_local.omnitypes import HeaterMode
from pyomnilogic_local.util import OmniEquipmentNotInitializedError

if TYPE_CHECKING:
    from pyomnilogic_local.omnilogic import OmniLogic


class Heater(OmniEquipment[MSPVirtualHeater, TelemetryVirtualHeater]):
    """
    Represents a heater in the OmniLogic system.

    Note: Temperature is always in Fahrenheit internally, so all temperature
    properties and methods use Fahrenheit. Use the omni.system.units property to
    determine if conversion to Celsius should be performed for display.
    """

    heater_equipment: EquipmentDict[HeaterEquipment] = EquipmentDict()

    def __init__(self, omni: "OmniLogic", mspconfig: MSPVirtualHeater, telemetry: Telemetry) -> None:
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
        """
        Returns the maximum settable temperature.

        Note: Temperature is always in Fahrenheit internally.
        Use the system.units property to determine if conversion to Celsius is needed for display.
        """
        return self.mspconfig.max_temp

    @property
    def min_temp(self) -> int:
        """
        Returns the minimum settable temperature.

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
        """
        Returns the current set point from telemetry.

        Note: Temperature is always in Fahrenheit internally.
        Use the system.units property to determine if conversion to Celsius is needed for display.
        """
        return self.telemetry.current_set_point

    @property
    def solar_set_point(self) -> int:
        """
        Returns the solar set point from telemetry.

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

    @dirties_state()
    async def turn_on(self) -> None:
        """
        Turns the heater on (enables it).

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            raise OmniEquipmentNotInitializedError("Cannot turn on heater: bow_id or system_id is None")
        await self._api.async_set_heater_enable(self.bow_id, self.system_id, True)

    @dirties_state()
    async def turn_off(self) -> None:
        """
        Turns the heater off (disables it).

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            raise OmniEquipmentNotInitializedError("Cannot turn off heater: bow_id or system_id is None")
        await self._api.async_set_heater_enable(self.bow_id, self.system_id, False)

    @dirties_state()
    async def set_temperature(self, temperature: int) -> None:
        """
        Sets the target temperature for the heater.

        Args:
            temperature: The target temperature to set in Fahrenheit.
                        Must be between min_temp and max_temp.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            ValueError: If temperature is outside the valid range.

        Note:
            Temperature must be provided in Fahrenheit as that is what the OmniLogic
            system uses internally. The system.units setting only affects display,
            not the API. If your application uses Celsius, you must convert to
            Fahrenheit before calling this method.
        """
        if self.bow_id is None or self.system_id is None:
            raise OmniEquipmentNotInitializedError("Cannot set heater temperature: bow_id or system_id is None")

        if temperature < self.min_temp or temperature > self.max_temp:
            raise ValueError(f"Temperature {temperature}°F is outside valid range [{self.min_temp}°F, {self.max_temp}°F]")

        # Always use Fahrenheit as that's what the OmniLogic system uses internally
        await self._api.async_set_heater(self.bow_id, self.system_id, temperature)

    @dirties_state()
    async def set_solar_temperature(self, temperature: int) -> None:
        """
        Sets the solar heater set point.

        Args:
            temperature: The target solar temperature to set in Fahrenheit.
                        Must be between min_temp and max_temp.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            ValueError: If temperature is outside the valid range.

        Note:
            Temperature must be provided in Fahrenheit as that is what the OmniLogic
            system uses internally. The system.units setting only affects display,
            not the API. If your application uses Celsius, you must convert to
            Fahrenheit before calling this method.
        """
        if self.bow_id is None or self.system_id is None:
            raise OmniEquipmentNotInitializedError("Cannot set solar heater temperature: bow_id or system_id is None")

        if temperature < self.min_temp or temperature > self.max_temp:
            raise ValueError(f"Temperature {temperature}°F is outside valid range [{self.min_temp}°F, {self.max_temp}°F]")

        # Always use Fahrenheit as that's what the OmniLogic system uses internally
        await self._api.async_set_solar_heater(self.bow_id, self.system_id, temperature)
