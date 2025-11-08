from __future__ import annotations

from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.decorators import control_method
from pyomnilogic_local.models.mspconfig import MSPGroup
from pyomnilogic_local.models.telemetry import TelemetryGroup
from pyomnilogic_local.omnitypes import GroupState
from pyomnilogic_local.util import OmniEquipmentNotInitializedError

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic


class Group(OmniEquipment[MSPGroup, TelemetryGroup]):
    """Represents a group in the OmniLogic system.

    Groups allow multiple pieces of equipment to be controlled together as a single unit.
    When a group is activated, all equipment assigned to that group will turn on/off together.
    This provides convenient one-touch control for common pool/spa scenarios.

    Groups are defined in the OmniLogic configuration and can include any combination
    of relays, pumps, lights, heaters, and other controllable equipment.

    Within the OmniLogic App and Web Interface Groups are referred to as Themes.
    Within this library the term "Group" is used as that is how they are referred to in the
    MSPConfig.

    Attributes:
        mspconfig: Configuration data for this group from MSP XML
        telemetry: Real-time state data for the group

    Properties:
        icon_id: The icon identifier for the group (used in UI displays)
        state: Current state of the group (ON or OFF)
        is_on: True if the group is currently active

    Control Methods:
        turn_on(): Activate all equipment in the group
        turn_off(): Deactivate all equipment in the group

    Example:
        >>> omni = OmniLogic(...)
        >>> await omni.connect()
        >>>
        >>> # Access a group by name
        >>> all_features = omni.groups["All Features"]
        >>>
        >>> # Check current state
        >>> if all_features.is_on:
        ...     print("All features are currently active")
        >>>
        >>> # Control the group
        >>> await all_features.turn_on()   # Turn on all equipment in group
        >>> await all_features.turn_off()  # Turn off all equipment in group
        >>>
        >>> # Get group properties
        >>> print(f"Group: {all_features.name}")
        >>> print(f"Icon ID: {all_features.icon_id}")
        >>> print(f"System ID: {all_features.system_id}")

    Note:
        - Groups control multiple pieces of equipment simultaneously
        - Group membership is defined in OmniLogic configuration
        - Within the config, there is data for what equipment is in each group, but this library
          does not currently expose that membership information within the interaction layer.
    """

    mspconfig: MSPGroup
    telemetry: TelemetryGroup

    def __init__(self, omni: OmniLogic, mspconfig: MSPGroup, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    @property
    def icon_id(self) -> int:
        """Returns the icon ID for the group."""
        return self.mspconfig.icon_id

    @property
    def state(self) -> GroupState:
        """Returns the current state of the group."""
        return self.telemetry.state

    @property
    def is_on(self) -> bool:
        """Returns whether the group is currently active."""
        return self.state == GroupState.ON

    @control_method
    async def turn_on(self) -> None:
        """Activate the group, turning on all equipment assigned to it.

        Raises:
            OmniEquipmentNotInitializedError: If system_id is None.
        """
        if self.system_id is None:
            msg = "Cannot turn on group: system_id is None"
            raise OmniEquipmentNotInitializedError(msg)
        await self._api.async_set_group_enable(self.system_id, True)

    @control_method
    async def turn_off(self) -> None:
        """Deactivate the group, turning off all equipment assigned to it.

        Raises:
            OmniEquipmentNotInitializedError: If system_id is None.
        """
        if self.system_id is None:
            msg = "Cannot turn off group: system_id is None"
            raise OmniEquipmentNotInitializedError(msg)
        await self._api.async_set_group_enable(self.system_id, False)
