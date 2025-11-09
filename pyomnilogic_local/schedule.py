from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.decorators import control_method
from pyomnilogic_local.models.mspconfig import MSPSchedule
from pyomnilogic_local.util import OmniEquipmentNotInitializedError

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic


class Schedule(OmniEquipment[MSPSchedule, None]):
    """Represents a schedule in the OmniLogic system.

    Schedules control automatic timing of equipment operations. Each schedule defines
    when equipment should turn on/off or change state, what days of the week it should
    run, and whether it should repeat.

    Attributes:
        mspconfig: Configuration data for this schedule from MSP XML
        telemetry: None (schedules do not have telemetry data)

    Properties:
        bow_id: The Body of Water ID this schedule belongs to
        equipment_id: The equipment system ID controlled by this schedule
        controlled_equipment: The actual equipment instance controlled by this schedule
        event: The MessageType/action that will be executed
        data: The data value for the action (e.g., speed, on/off state)
        enabled: Whether the schedule is currently enabled
        start_hour: Hour to start (0-23)
        start_minute: Minute to start (0-59)
        end_hour: Hour to end (0-23)
        end_minute: Minute to end (0-59)
        days_active_raw: Bitmask of active days (1=Mon, 2=Tue, 4=Wed, etc.)
        days_active: List of active day names (e.g., ['Monday', 'Wednesday'])
        recurring: Whether the schedule repeats

    Control Methods:
        turn_on(): Enable the schedule
        turn_off(): Disable the schedule

    Example:
        >>> omni = OmniLogic(...)
        >>> await omni.connect()
        >>>
        >>> # Access schedules (when implemented in OmniLogic)
        >>> schedule = omni.schedules[15]  # Access by system_id
        >>>
        >>> # Check schedule details
        >>> print(f"Controls equipment ID: {schedule.equipment_id}")
        >>> print(f"Runs on: {', '.join(schedule.days_active)}")
        >>> print(f"Time: {schedule.start_hour}:{schedule.start_minute:02d} - {schedule.end_hour}:{schedule.end_minute:02d}")
        >>> print(f"Enabled: {schedule.enabled}")
        >>>
        >>> # Control schedule
        >>> await schedule.turn_on()   # Enable the schedule
        >>> await schedule.turn_off()  # Disable the schedule

    Note:
        - Schedules do not have telemetry; state is only in configuration
        - Turning on/off a schedule only changes its enabled state
        - All other schedule parameters (timing, days, equipment) remain unchanged
        - The schedule-system-id is used to identify which schedule to edit
    """

    mspconfig: MSPSchedule
    telemetry: None

    def __init__(self, omni: OmniLogic, mspconfig: MSPSchedule, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    @property
    def equipment_id(self) -> int:
        """Returns the equipment ID controlled by this schedule."""
        return self.mspconfig.equipment_id

    @property
    def event(self) -> int:
        """Returns the event/action ID that will be executed."""
        return self.mspconfig.event.value

    @property
    def data(self) -> int:
        """Returns the data value for the scheduled action."""
        return self.mspconfig.data

    @property
    def enabled(self) -> bool:
        """Returns whether the schedule is currently enabled."""
        return self.mspconfig.enabled

    @property
    def start_hour(self) -> int:
        """Returns the hour the schedule starts (0-23)."""
        return self.mspconfig.start_hour

    @property
    def start_minute(self) -> int:
        """Returns the minute the schedule starts (0-59)."""
        return self.mspconfig.start_minute

    @property
    def end_hour(self) -> int:
        """Returns the hour the schedule ends (0-23)."""
        return self.mspconfig.end_hour

    @property
    def end_minute(self) -> int:
        """Returns the minute the schedule ends (0-59)."""
        return self.mspconfig.end_minute

    @property
    def days_active_raw(self) -> int:
        """Returns the raw bitmask of active days."""
        return self.mspconfig.days_active_raw

    @property
    def days_active(self) -> list[str]:
        """Returns a list of active day names."""
        return self.mspconfig.days_active

    @property
    def recurring(self) -> bool:
        """Returns whether the schedule repeats."""
        return self.mspconfig.recurring

    @property
    def controlled_equipment(self) -> OmniEquipment[Any, Any] | None:
        """Returns the equipment controlled by this schedule.

        Uses the schedule's equipment_id to dynamically look up the actual
        equipment instance from the OmniLogic parent.

        Returns:
            The equipment instance controlled by this schedule, or None if not found.

        Example:
            >>> schedule = omni.schedules[15]
            >>> equipment = schedule.controlled_equipment
            >>> if equipment:
            ...     print(f"This schedule controls: {equipment.name}")
        """
        return self._omni.get_equipment_by_id(self.equipment_id)

    @control_method
    async def turn_on(self) -> None:
        """Enable the schedule.

        Sends an edit command with all current schedule parameters but sets
        the enabled state to True.

        Raises:
            OmniEquipmentNotInitializedError: If system_id is None.
        """
        if self.system_id is None:
            msg = "Cannot turn on schedule: system_id is None"
            raise OmniEquipmentNotInitializedError(msg)

        await self._api.async_edit_schedule(
            equipment_id=self.system_id,  # This is the schedule-system-id
            data=self.data,
            action_id=self.event,
            start_time_hours=self.start_hour,
            start_time_minutes=self.start_minute,
            end_time_hours=self.end_hour,
            end_time_minutes=self.end_minute,
            days_active=self.days_active_raw,
            is_enabled=True,  # Enable the schedule
            recurring=self.recurring,
        )

    @control_method
    async def turn_off(self) -> None:
        """Disable the schedule.

        Sends an edit command with all current schedule parameters but sets
        the enabled state to False.

        Raises:
            OmniEquipmentNotInitializedError: If system_id is None.
        """
        if self.system_id is None:
            msg = "Cannot turn off schedule: system_id is None"
            raise OmniEquipmentNotInitializedError(msg)

        await self._api.async_edit_schedule(
            equipment_id=self.system_id,  # This is the schedule-system-id
            data=self.data,
            action_id=self.event,
            start_time_hours=self.start_hour,
            start_time_minutes=self.start_minute,
            end_time_hours=self.end_hour,
            end_time_minutes=self.end_minute,
            days_active=self.days_active_raw,
            is_enabled=False,  # Disable the schedule
            recurring=self.recurring,
        )
