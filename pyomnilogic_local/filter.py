from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.decorators import dirties_state
from pyomnilogic_local.models.mspconfig import MSPFilter
from pyomnilogic_local.models.telemetry import TelemetryFilter
from pyomnilogic_local.omnitypes import FilterSpeedPresets, FilterState
from pyomnilogic_local.util import OmniEquipmentNotInitializedError


class Filter(OmniEquipment[MSPFilter, TelemetryFilter]):
    """Represents a filter in the OmniLogic system."""

    mspconfig: MSPFilter
    telemetry: TelemetryFilter

    # Expose MSPConfig attributes
    @property
    def equip_type(self) -> str:
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
    def state(self) -> FilterState | int:
        """Current filter state."""
        return self.telemetry.state

    @property
    def speed(self) -> int:
        """Current filter speed."""
        return self.telemetry.speed

    @property
    def valve_position(self) -> int:
        """Current valve position."""
        return self.telemetry.valve_position

    @property
    def why_on(self) -> int:
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

        # Then check filter-specific readiness
        return self.state in (FilterState.OFF, FilterState.ON)

    # Control methods
    @dirties_state()
    async def turn_on(self) -> None:
        """Turn the filter on.

        This will turn on the filter at its last used speed setting.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Filter bow_id and system_id must be set"
            raise OmniEquipmentNotInitializedError(msg)

        await self._api.async_set_equipment(
            pool_id=self.bow_id,
            equipment_id=self.system_id,
            is_on=self.last_speed,
        )

    @dirties_state()
    async def turn_off(self) -> None:
        """Turn the filter off."""
        if self.bow_id is None or self.system_id is None:
            msg = "Filter bow_id and system_id must be set"
            raise OmniEquipmentNotInitializedError(msg)

        await self._api.async_set_equipment(
            pool_id=self.bow_id,
            equipment_id=self.system_id,
            is_on=False,
        )

    @dirties_state()
    async def run_preset_speed(self, speed: FilterSpeedPresets) -> None:
        """Run the filter at a preset speed.

        Args:
            speed: The preset speed to use (LOW, MEDIUM, or HIGH)
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

    @dirties_state()
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

        if not 0 <= speed <= 100:
            msg = f"Speed {speed} is outside valid range [0, 100]"
            raise ValueError(msg)

        # Note: The API validates against min_percent/max_percent internally
        await self._api.async_set_filter_speed(
            pool_id=self.bow_id,
            equipment_id=self.system_id,
            speed=speed,
        )
