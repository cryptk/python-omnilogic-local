from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.decorators import dirties_state
from pyomnilogic_local.models.mspconfig import MSPPump
from pyomnilogic_local.models.telemetry import TelemetryPump
from pyomnilogic_local.omnitypes import PumpSpeedPresets, PumpState
from pyomnilogic_local.util import OmniEquipmentNotInitializedError


class Pump(OmniEquipment[MSPPump, TelemetryPump]):
    """Represents a pump in the OmniLogic system."""

    mspconfig: MSPPump
    telemetry: TelemetryPump

    # Expose MSPConfig attributes
    @property
    def equip_type(self) -> str:
        """The pump type (e.g., PMP_VARIABLE_SPEED_PUMP)."""
        return self.mspconfig.equip_type

    @property
    def function(self) -> str:
        """The pump function (e.g., PMP_PUMP, PMP_WATER_FEATURE)."""
        return self.mspconfig.function

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
        """Whether priming is enabled for this pump."""
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
    def state(self) -> PumpState | int:
        """Current pump state."""
        return self.telemetry.state

    @property
    def speed(self) -> int:
        """Current pump speed."""
        return self.telemetry.speed

    @property
    def last_speed(self) -> int:
        """Last speed setting."""
        return self.telemetry.last_speed

    @property
    def why_on(self) -> int:
        """Reason why the pump is on."""
        return self.telemetry.why_on

    # Computed properties
    @property
    def is_on(self) -> bool:
        """Check if the pump is currently on.

        Returns:
            True if pump state is ON (1), False otherwise
        """
        return self.state == PumpState.ON

    @property
    def is_ready(self) -> bool:
        """Check if the pump is ready to receive commands.

        A pump is considered ready if:
        - The backyard is not in service/config mode (checked by parent class)
        - It's in a stable state (ON or OFF)

        Returns:
            True if pump can accept commands, False otherwise
        """
        # First check if backyard is ready
        if not super().is_ready:
            return False

        # Then check pump-specific readiness
        return self.state in (PumpState.OFF, PumpState.ON)

    # Control methods
    @dirties_state()
    async def turn_on(self) -> None:
        """Turn the pump on.

        This will turn on the pump at its last used speed setting.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Pump bow_id and system_id must be set"
            raise OmniEquipmentNotInitializedError(msg)

        await self._api.async_set_equipment(
            pool_id=self.bow_id,
            equipment_id=self.system_id,
            is_on=True,
        )

    @dirties_state()
    async def turn_off(self) -> None:
        """Turn the pump off."""
        if self.bow_id is None or self.system_id is None:
            msg = "Pump bow_id and system_id must be set"
            raise OmniEquipmentNotInitializedError(msg)

        await self._api.async_set_equipment(
            pool_id=self.bow_id,
            equipment_id=self.system_id,
            is_on=False,
        )

    @dirties_state()
    async def run_preset_speed(self, speed: PumpSpeedPresets) -> None:
        """Run the pump at a preset speed.

        Args:
            speed: The preset speed to use (LOW, MEDIUM, or HIGH)

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            ValueError: If an invalid speed preset is provided.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Pump bow_id and system_id must be set"
            raise OmniEquipmentNotInitializedError(msg)

        speed_value: int
        match speed:
            case PumpSpeedPresets.LOW:
                speed_value = self.low_speed
            case PumpSpeedPresets.MEDIUM:
                speed_value = self.medium_speed
            case PumpSpeedPresets.HIGH:
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
        """Set the pump to a specific speed.

        Args:
            speed: Speed value (0-100 percent). A value of 0 will turn the pump off.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            ValueError: If speed is outside the valid range.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Pump bow_id and system_id must be set"
            raise OmniEquipmentNotInitializedError(msg)

        if not 0 <= speed <= 100:
            msg = f"Speed {speed} is outside valid range [0, 100]"
            raise ValueError(msg)

        # Note: The API validates against min_percent/max_percent internally
        await self._api.async_set_equipment(
            pool_id=self.bow_id,
            equipment_id=self.system_id,
            is_on=speed,
        )
