from __future__ import annotations

from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.decorators import control_method
from pyomnilogic_local.models.mspconfig import MSPFilter
from pyomnilogic_local.models.telemetry import TelemetryFilter
from pyomnilogic_local.omnitypes import FilterSpeedPresets, FilterState, FilterType
from pyomnilogic_local.util import OmniEquipmentNotInitializedError

if TYPE_CHECKING:
    from pyomnilogic_local.omnitypes import FilterValvePosition, FilterWhyOn


class Filter(OmniEquipment[MSPFilter, TelemetryFilter]):
    """Represents a pool/spa filtration pump in the OmniLogic system.

    A filter (also known as a filtration pump) is responsible for circulating and
    filtering water through the pool or spa. Most filters support variable speed
    operation with configurable presets for energy efficiency.

    The Filter class provides control over pump speed, monitoring of operational
    state, and access to power consumption data. Filters can operate at:
    - Preset speeds (LOW, MEDIUM, HIGH) configured in the system
    - Custom speed percentages (0-100%)
    - Variable RPM (for compatible pumps)

    Attributes:
        mspconfig: Configuration data for this filter from MSP XML
        telemetry: Real-time operational data and state

    Properties (Configuration):
        equip_type: Equipment type identifier (e.g., FMT_VARIABLE_SPEED_PUMP)
        max_percent: Maximum speed as percentage (0-100)
        min_percent: Minimum speed as percentage (0-100)
        max_rpm: Maximum speed in RPM
        min_rpm: Minimum speed in RPM
        priming_enabled: Whether priming mode is enabled
        low_speed: Configured low speed preset value
        medium_speed: Configured medium speed preset value
        high_speed: Configured high speed preset value

    Properties (Telemetry):
        state: Current operational state (OFF, ON, PRIMING, etc.)
        speed: Current operating speed
        valve_position: Current valve position
        why_on: Reason code for pump being on
        reported_speed: Speed reported by pump
        power: Current power consumption in watts
        last_speed: Previous speed setting

    Properties (Computed):
        is_on: True if filter is currently running
        is_ready: True if filter can accept commands

    Control Methods:
        turn_on(): Turn on filter at last used speed
        turn_off(): Turn off filter
        run_preset_speed(speed): Run at LOW, MEDIUM, or HIGH preset
        set_speed(speed): Run at specific percentage (0-100)

    Example:
        >>> pool = omni.backyard.bow["Pool"]
        >>> filter = pool.filters["Main Filter"]
        >>>
        >>> # Check current state
        >>> print(f"Filter is {'on' if filter.is_on else 'off'}")
        >>> print(f"Speed: {filter.speed}%, Power: {filter.power}W")
        >>>
        >>> # Control filter
        >>> await filter.turn_on()  # Turn on at last speed
        >>> await filter.run_preset_speed(FilterSpeedPresets.LOW)
        >>> await filter.set_speed(75)  # Set to 75%
        >>> await filter.turn_off()

    Note:
        - Speed value of 0 will turn the filter off
        - The API automatically validates against min_percent/max_percent
        - Filter state may transition through PRIMING before reaching ON
        - Not all filters support all speed ranges (check min/max values)
    """

    mspconfig: MSPFilter
    telemetry: TelemetryFilter

    # Expose MSPConfig attributes
    @property
    def equip_type(self) -> FilterType:
        """The filter type (e.g., FMT_VARIABLE_SPEED_PUMP)."""
        return self.mspconfig.equip_type

    @property
    def max_percent(self) -> int:
        """Maximum pump speed percentage."""
        return self.mspconfig.max_percent

    @property
    def min_percent(self) -> int:
        """Minimum pump speed percentage."""
        return self.mspconfig.min_percent

    @property
    def max_rpm(self) -> int:
        """Maximum pump speed in RPM."""
        return self.mspconfig.max_rpm

    @property
    def min_rpm(self) -> int:
        """Minimum pump speed in RPM."""
        return self.mspconfig.min_rpm

    @property
    def priming_enabled(self) -> bool:
        """Whether priming is enabled for this filter."""
        return self.mspconfig.priming_enabled

    @property
    def low_speed(self) -> int:
        """Low speed preset value."""
        return self.mspconfig.low_speed

    @property
    def medium_speed(self) -> int:
        """Medium speed preset value."""
        return self.mspconfig.medium_speed

    @property
    def high_speed(self) -> int:
        """High speed preset value."""
        return self.mspconfig.high_speed

    # Expose Telemetry attributes
    @property
    def state(self) -> FilterState:
        """Current filter state."""
        return self.telemetry.state

    @property
    def speed(self) -> int:
        """Current filter speed."""
        return self.telemetry.speed

    @property
    def valve_position(self) -> FilterValvePosition:
        """Current valve position."""
        return self.telemetry.valve_position

    @property
    def why_on(self) -> FilterWhyOn:
        """Reason why the filter is on."""
        return self.telemetry.why_on

    @property
    def reported_speed(self) -> int:
        """Reported filter speed."""
        return self.telemetry.reported_speed

    @property
    def power(self) -> int:
        """Current power consumption."""
        return self.telemetry.power

    @property
    def last_speed(self) -> int:
        """Last speed setting."""
        return self.telemetry.last_speed

    # Computed properties
    @property
    def is_on(self) -> bool:
        """Check if the filter is currently on.

        Returns:
            True if filter state is ON (1), False otherwise
        """
        return self.state in (
            FilterState.ON,
            FilterState.PRIMING,
            FilterState.HEATER_EXTEND,
            FilterState.CSAD_EXTEND,
            FilterState.FILTER_FORCE_PRIMING,
            FilterState.FILTER_SUPERCHLORINATE,
        )

    @property
    def is_ready(self) -> bool:
        """Check if the filter is ready to receive commands.

        A filter is considered ready if:
        - The backyard is not in service/config mode (checked by parent class)
        - It's not in a transitional state like priming, waiting to turn off, or cooling down

        Returns:
            True if filter can accept commands, False otherwise
        """
        # First check if backyard is ready
        if not super().is_ready:
            return False

        # Then check filter-specific readiness to make sure it's in a state that can accept commands
        # SUSPEND indicates that the physical filter is being used for a different BoW (e.g.: spillover)
        # We need to consider the filter as ready in this state, otherwise we cannot control the
        # virtual filter to switch the physical filter back BoW
        # ref: https://github.com/cryptk/python-omnilogic-local/issues/100
        return self.state in (FilterState.OFF, FilterState.ON, FilterState.SUSPEND)

    # Control methods
    @control_method
    async def turn_on(self) -> None:
        """Turn the filter on.

        This will turn on the filter at its last used speed setting.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Filter bow_id and system_id must be set"
            raise OmniEquipmentNotInitializedError(msg)

        # If we are a Variable Speed filter, we want to try to turn on at the last speed setting
        # This matches the behavior of the OmniLogic phone app
        target_speed: int = 100
        match self.equip_type:
            case FilterType.VARIABLE_SPEED:
                if self.last_speed >= self.min_percent and self.last_speed <= self.max_percent:
                    target_speed = self.last_speed
            case FilterType.SINGLE_SPEED:
                target_speed = self.max_percent

        await self._api.async_set_equipment(
            pool_id=self.bow_id,
            equipment_id=self.system_id,
            is_on=target_speed,
        )

    @control_method
    async def turn_off(self) -> None:
        """Turn the filter off.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Filter bow_id and system_id must be set"
            raise OmniEquipmentNotInitializedError(msg)

        await self._api.async_set_equipment(
            pool_id=self.bow_id,
            equipment_id=self.system_id,
            is_on=False,
        )

    @control_method
    async def run_preset_speed(self, speed: FilterSpeedPresets) -> None:
        """Run the filter at a preset speed.

        Args:
            speed: The preset speed to use (LOW, MEDIUM, or HIGH)

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            ValueError: If an invalid speed preset is provided.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Filter bow_id and system_id must be set"
            raise OmniEquipmentNotInitializedError(msg)

        speed_value: int
        match speed:
            case FilterSpeedPresets.LOW:
                speed_value = self.low_speed
            case FilterSpeedPresets.MEDIUM:
                speed_value = self.medium_speed
            case FilterSpeedPresets.HIGH:
                speed_value = self.high_speed
            case _:
                msg = f"Invalid speed preset: {speed}"
                raise ValueError(msg)

        await self._api.async_set_equipment(
            pool_id=self.bow_id,
            equipment_id=self.system_id,
            is_on=speed_value,
        )

    @control_method
    async def set_speed(self, speed: int) -> None:
        """Set the filter to a specific speed.

        Args:
            speed: Speed value (0-100 percent). A value of 0 will turn the filter off.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            ValueError: If speed is outside the valid range.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Filter bow_id and system_id must be set"
            raise OmniEquipmentNotInitializedError(msg)

        if not self.min_percent <= speed <= self.max_percent:
            msg = f"Speed {speed} is outside valid range [{self.min_percent}, {self.max_percent}]"
            raise ValueError(msg)

        # Note: The API validates against min_percent/max_percent internally
        await self._api.async_set_filter_speed(
            pool_id=self.bow_id,
            equipment_id=self.system_id,
            speed=speed,
        )
