from __future__ import annotations

from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.chlorinator_equip import ChlorinatorEquipment
from pyomnilogic_local.collections import EquipmentDict
from pyomnilogic_local.decorators import control_method
from pyomnilogic_local.models.mspconfig import MSPChlorinator
from pyomnilogic_local.models.telemetry import TelemetryChlorinator
from pyomnilogic_local.omnitypes import ChlorinatorStatus
from pyomnilogic_local.util import OmniEquipmentNotInitializedError

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic
    from pyomnilogic_local.omnitypes import ChlorinatorCellType, ChlorinatorOperatingMode


class Chlorinator(OmniEquipment[MSPChlorinator, TelemetryChlorinator]):
    """Represents a chlorinator in the OmniLogic system.

    A chlorinator is responsible for generating chlorine through electrolysis
    (for salt-based systems) or dispensing chlorine (for liquid/tablet systems).
    It monitors and reports salt levels, chlorine generation status, and various
    alerts and errors.

    Attributes:
        mspconfig: The MSP configuration for this chlorinator
        telemetry: Real-time telemetry data for this chlorinator
        chlorinator_equipment: Collection of physical chlorinator equipment units

    Example:
        >>> chlorinator = pool.get_chlorinator()
        >>> print(f"Salt level: {chlorinator.avg_salt_level} ppm")
        >>> print(f"Is generating: {chlorinator.is_generating}")
        >>> if chlorinator.has_alert:
        ...     print(f"Alerts: {chlorinator.alert_messages}")
    """

    mspconfig: MSPChlorinator
    telemetry: TelemetryChlorinator
    chlorinator_equipment: EquipmentDict[ChlorinatorEquipment] = EquipmentDict()

    def __init__(self, omni: OmniLogic, mspconfig: MSPChlorinator, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    def _update_equipment(self, mspconfig: MSPChlorinator, telemetry: Telemetry | None) -> None:
        """Update both the configuration and telemetry data for the equipment."""
        if telemetry is None:
            return
        self._update_chlorinator_equipment(mspconfig, telemetry)

    def _update_chlorinator_equipment(self, mspconfig: MSPChlorinator, telemetry: Telemetry) -> None:
        """Update the chlorinator equipment based on the MSP configuration."""
        if mspconfig.chlorinator_equipment is None:
            self.chlorinator_equipment = EquipmentDict()
            return

        self.chlorinator_equipment = EquipmentDict(
            [ChlorinatorEquipment(self._omni, equip, telemetry) for equip in mspconfig.chlorinator_equipment]
        )

    # Expose MSPConfig attributes
    @property
    def enabled(self) -> bool:
        """Whether the chlorinator is enabled in the system configuration."""
        return self.mspconfig.enabled

    @property
    def timed_percent(self) -> int:
        """Configured chlorine generation percentage when in timed mode (0-100%)."""
        return self.mspconfig.timed_percent

    @property
    def superchlor_timeout(self) -> int:
        """Timeout duration for super-chlorination mode in minutes."""
        return self.mspconfig.superchlor_timeout

    @property
    def orp_timeout(self) -> int:
        """Timeout duration for ORP (Oxidation-Reduction Potential) mode in minutes."""
        return self.mspconfig.orp_timeout

    @property
    def dispenser_type(self) -> str:
        """Type of chlorine dispenser (SALT, LIQUID, or TABLET)."""
        return self.mspconfig.dispenser_type

    @property
    def cell_type(self) -> ChlorinatorCellType:
        """Type of T-Cell installed (e.g., T3, T5, T9, T15)."""
        return self.mspconfig.cell_type

    # Expose Telemetry attributes
    @property
    def operating_state(self) -> int:
        """Current operational state of the chlorinator (raw value)."""
        return self.telemetry.operating_state

    @property
    def operating_mode(self) -> ChlorinatorOperatingMode | int:
        """Current operating mode (DISABLED, TIMED, ORP_AUTO, or ORP_TIMED_RW).

        Returns:
            ChlorinatorOperatingMode: The operating mode enum value
        """
        return self.telemetry.operating_mode

    @property
    def timed_percent_telemetry(self) -> int | None:
        """Current chlorine generation percentage from telemetry (0-100%).

        This may differ from the configured timed_percent if the system
        is in a special mode (e.g., super-chlorination).

        Returns:
            Current generation percentage, or None if not available
        """
        return self.telemetry.timed_percent

    @property
    def sc_mode(self) -> int:
        """Super-chlorination mode status (raw value)."""
        return self.telemetry.sc_mode

    @property
    def avg_salt_level(self) -> int:
        """Average salt level reading in parts per million (ppm).

        This is a smoothed reading over time, useful for monitoring
        long-term salt levels.
        """
        return self.telemetry.avg_salt_level

    @property
    def instant_salt_level(self) -> int:
        """Instantaneous salt level reading in parts per million (ppm).

        This is the current salt level reading, which may fluctuate
        more than the average salt level.
        """
        return self.telemetry.instant_salt_level

    # Computed properties for status, alerts, and errors
    @property
    def status(self) -> list[str]:
        """List of active status flags as human-readable strings.

        Decodes the status bitmask into individual flag names.
        Possible values include:
        - ERROR_PRESENT: An error condition exists (check error_messages)
        - ALERT_PRESENT: An alert condition exists (check alert_messages)
        - GENERATING: Power is applied to T-Cell, actively chlorinating
        - SYSTEM_PAUSED: System processor is pausing chlorination
        - LOCAL_PAUSED: Local processor is pausing chlorination
        - AUTHENTICATED: T-Cell is authenticated and recognized
        - K1_ACTIVE: K1 relay is active
        - K2_ACTIVE: K2 relay is active

        Returns:
            List of active status flag names

        Example:
            >>> chlorinator.status
            ['GENERATING', 'AUTHENTICATED', 'K1_ACTIVE']
        """
        return self.telemetry.status

    @property
    def alert_messages(self) -> list[str]:
        """List of active alert conditions as human-readable strings.

        Decodes the alert bitmask into individual alert names.
        Possible values include:
        - SALT_LOW: Salt level is low (add salt soon)
        - SALT_TOO_LOW: Salt level is too low (add salt now)
        - HIGH_CURRENT: High current alert
        - LOW_VOLTAGE: Low voltage alert
        - CELL_TEMP_LOW: Cell water temperature is low
        - CELL_TEMP_SCALEBACK: Cell water temperature scaleback
        - CELL_TEMP_HIGH: Cell water temperature is high (bits 4+5 both set)
        - BOARD_TEMP_HIGH: Board temperature is high
        - BOARD_TEMP_CLEARING: Board temperature is clearing
        - CELL_CLEAN: Cell cleaning/runtime alert

        Returns:
            List of active alert names

        Example:
            >>> chlorinator.alert_messages
            ['SALT_LOW', 'CELL_CLEAN']
        """
        return self.telemetry.alerts

    @property
    def error_messages(self) -> list[str]:
        """List of active error conditions as human-readable strings.

        Decodes the error bitmask into individual error names.
        Possible values include:
        - CURRENT_SENSOR_SHORT: Current sensor short circuit
        - CURRENT_SENSOR_OPEN: Current sensor open circuit
        - VOLTAGE_SENSOR_SHORT: Voltage sensor short circuit
        - VOLTAGE_SENSOR_OPEN: Voltage sensor open circuit
        - CELL_TEMP_SENSOR_SHORT: Cell temperature sensor short
        - CELL_TEMP_SENSOR_OPEN: Cell temperature sensor open
        - BOARD_TEMP_SENSOR_SHORT: Board temperature sensor short
        - BOARD_TEMP_SENSOR_OPEN: Board temperature sensor open
        - K1_RELAY_SHORT: K1 relay short circuit
        - K1_RELAY_OPEN: K1 relay open circuit
        - K2_RELAY_SHORT: K2 relay short circuit
        - K2_RELAY_OPEN: K2 relay open circuit
        - CELL_ERROR_TYPE: Cell type error
        - CELL_ERROR_AUTH: Cell authentication error
        - CELL_COMM_LOSS: Cell communication loss (bits 12+13 both set)
        - AQUARITE_PCB_ERROR: AquaRite PCB error

        Returns:
            List of active error names

        Example:
            >>> chlorinator.error_messages
            ['CURRENT_SENSOR_SHORT', 'K1_RELAY_OPEN']
        """
        return self.telemetry.errors

    # High-level status properties
    @property
    def is_on(self) -> bool:
        """Check if the chlorinator is currently enabled and operational.

        A chlorinator is considered "on" if it is enabled in the configuration,
        regardless of whether it is actively generating chlorine at this moment.

        Returns:
            True if the chlorinator is enabled, False otherwise

        See Also:
            is_generating: Check if actively producing chlorine right now
        """
        return self.enabled and self.telemetry.enable

    @property
    def is_generating(self) -> bool:
        """Check if the chlorinator is actively generating chlorine.

        This indicates that power is currently applied to the T-Cell and
        chlorine is being produced through electrolysis.

        Returns:
            True if the GENERATING status flag is set, False otherwise

        Example:
            >>> if chlorinator.is_generating:
            ...     print(f"Generating at {chlorinator.timed_percent_telemetry}%")
        """
        return self.telemetry.active

    @property
    def is_paused(self) -> bool:
        """Check if chlorination is currently paused.

        Chlorination can be paused by either the system processor or the
        local processor for various reasons (e.g., low flow, maintenance).

        Returns:
            True if either SYSTEM_PAUSED or LOCAL_PAUSED flags are set

        Example:
            >>> if chlorinator.is_paused:
            ...     print("Chlorination is paused")
        """
        return bool(
            (ChlorinatorStatus.SYSTEM_PAUSED.value & self.telemetry.status_raw)
            or (ChlorinatorStatus.LOCAL_PAUSED.value & self.telemetry.status_raw)
        )

    @property
    def has_alert(self) -> bool:
        """Check if any alert conditions are present.

        Returns:
            True if the ALERT_PRESENT status flag is set, False otherwise

        See Also:
            alert_messages: Get the list of specific alert conditions
        """
        return ChlorinatorStatus.ALERT_PRESENT.value & self.telemetry.status_raw == ChlorinatorStatus.ALERT_PRESENT.value

    @property
    def has_error(self) -> bool:
        """Check if any error conditions are present.

        Returns:
            True if the ERROR_PRESENT status flag is set, False otherwise

        See Also:
            error_messages: Get the list of specific error conditions
        """
        return ChlorinatorStatus.ERROR_PRESENT.value & self.telemetry.status_raw == ChlorinatorStatus.ERROR_PRESENT.value

    @property
    def is_authenticated(self) -> bool:
        """Check if the T-Cell is authenticated.

        An authenticated T-Cell is recognized by the system and can generate
        chlorine. Unauthenticated cells may be counterfeit or damaged.

        Returns:
            True if the AUTHENTICATED status flag is set, False otherwise
        """
        return ChlorinatorStatus.AUTHENTICATED.value & self.telemetry.status_raw == ChlorinatorStatus.AUTHENTICATED.value

    @property
    def salt_level_status(self) -> str:
        """Get a human-readable status of the salt level.

        Returns:
            'OK' if salt level is adequate
            'LOW' if salt is low (add salt soon)
            'TOO_LOW' if salt is too low (add salt now)

        Example:
            >>> status = chlorinator.salt_level_status
            >>> if status != 'OK':
            ...     print(f"Salt level is {status}: {chlorinator.avg_salt_level} ppm")
        """
        alerts = self.alert_messages
        if "SALT_TOO_LOW" in alerts:
            return "TOO_LOW"
        if "SALT_LOW" in alerts:
            return "LOW"
        return "OK"

    @property
    def is_ready(self) -> bool:
        """Check if the chlorinator is ready to accept commands.

        A chlorinator is considered ready if:
        - The backyard is not in service/config mode (checked by parent class)
        - It is authenticated
        - It has no critical errors that would prevent it from operating

        Returns:
            True if chlorinator can accept commands, False otherwise

        Example:
            >>> if chlorinator.is_ready:
            ...     await chlorinator.set_chlorine_level(75)
        """
        # First check if backyard is ready
        if not super().is_ready:
            return False

        # Then check chlorinator-specific readiness
        return self.is_authenticated and not self.has_error

    # Control methods
    @control_method
    async def turn_on(self) -> None:
        """Turn the chlorinator on (enable it).

        Raises:
            OmniEquipmentNotInitializedError: If bow_id is None.
        """
        if self.bow_id is None:
            msg = "Cannot turn on chlorinator: bow_id is None"
            raise OmniEquipmentNotInitializedError(msg)
        await self._api.async_set_chlorinator_enable(self.bow_id, True)

    @control_method
    async def turn_off(self) -> None:
        """Turn the chlorinator off (disable it).

        Raises:
            OmniEquipmentNotInitializedError: If bow_id is None.
        """
        if self.bow_id is None:
            msg = "Cannot turn off chlorinator: bow_id is None"
            raise OmniEquipmentNotInitializedError(msg)
        await self._api.async_set_chlorinator_enable(self.bow_id, False)

    @control_method
    async def set_timed_percent(self, percent: int) -> None:
        """Set the timed percent for chlorine generation.

        Args:
            percent: The chlorine generation percentage (0-100)

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            ValueError: If percent is outside the valid range (0-100).

        Note:
            This method uses the async_set_chlorinator_params API which requires
            all chlorinator configuration parameters. The current values from
            mspconfig are used for unchanged parameters.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Cannot set timed percent: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)

        if not 0 <= percent <= 100:
            msg = f"Timed percent {percent} is outside valid range [0, 100]"
            raise ValueError(msg)

        # Get the parent Bow to determine bow_type
        # We need to find our bow in the backyard
        if (bow := self._omni.backyard.bow.get(self.bow_id)) is None:
            msg = f"Cannot find bow with id {self.bow_id}"
            raise OmniEquipmentNotInitializedError(msg)

        # Map equipment type to numeric bow_type value
        # BOW_POOL = 0, BOW_SPA = 1 (based on typical protocol values)
        bow_type = 0 if bow.equip_type == "BOW_POOL" else 1

        # Get operating mode from telemetry (it's already an int or enum with .value)
        op_mode = self.telemetry.operating_mode if isinstance(self.telemetry.operating_mode, int) else self.telemetry.operating_mode.value

        await self._api.async_set_chlorinator_params(
            pool_id=self.bow_id,
            equipment_id=self.system_id,
            timed_percent=percent,
            cell_type=self.mspconfig.cell_type.value,  # ChlorinatorCellType is now IntEnum, use .value
            op_mode=op_mode,
            sc_timeout=self.mspconfig.superchlor_timeout,
            bow_type=bow_type,
            orp_timeout=self.mspconfig.orp_timeout,
        )
