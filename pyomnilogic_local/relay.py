from __future__ import annotations

from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.decorators import control_method
from pyomnilogic_local.models.mspconfig import MSPRelay
from pyomnilogic_local.models.telemetry import TelemetryRelay
from pyomnilogic_local.omnitypes import RelayState
from pyomnilogic_local.util import OmniEquipmentNotInitializedError

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic
    from pyomnilogic_local.omnitypes import RelayFunction, RelayType, RelayWhyOn


class Relay(OmniEquipment[MSPRelay, TelemetryRelay]):
    """Represents a relay in the OmniLogic system.

    Relays are ON/OFF switches that control various pool and spa equipment that
    doesn't require variable speed control. Common relay applications include:
    - Pool/spa lights (non-ColorLogic)
    - Water features and fountains
    - Deck jets and bubblers
    - Auxiliary equipment (blowers, misters, etc.)
    - Landscape lighting
    - Accessory equipment

    Each relay has a configured function that determines its purpose and behavior.
    Relays can be controlled manually or automatically based on schedules and
    other system conditions.

    Attributes:
        mspconfig: Configuration data for this relay from MSP XML
        telemetry: Real-time state and status data

    Properties:
        relay_type: Type of relay (e.g., VALVE_ACTUATOR, HIGH_VOLTAGE_RELAY, LOW_VOLTAGE_RELAY)
        function: Relay function (e.g., WATER_FEATURE, CLEANER, etc)
        state: Current state (ON or OFF)
        why_on: Reason code for relay being on (manual, schedule, etc.)
        is_on: True if relay is currently energized

    Control Methods:
        turn_on(): Energize the relay (turn equipment on)
        turn_off(): De-energize the relay (turn equipment off)

    Example:
        >>> pool = omni.backyard.bow["Pool"]
        >>> deck_jets = pool.relays["Deck Jets"]
        >>>
        >>> # Check current state
        >>> if deck_jets.is_on:
        ...     print("Deck jets are currently running")
        >>>
        >>> # Control relay
        >>> await deck_jets.turn_on()
        >>> await deck_jets.turn_off()
        >>>
        >>> # Check function
        >>> print(f"Relay function: {deck_jets.function}")
        >>> print(f"Relay type: {deck_jets.relay_type}")
        >>>
        >>> # Check why the relay is on
        >>> if deck_jets.is_on:
        ...     print(f"Why on: {deck_jets.why_on}")

    Note:
        - Relays are binary ON/OFF devices (no speed or intensity control)
        - The why_on property indicates if control is manual or automatic
        - Relay state changes are immediate (no priming or delay states)
    """

    mspconfig: MSPRelay
    telemetry: TelemetryRelay

    def __init__(self, omni: OmniLogic, mspconfig: MSPRelay, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    @property
    def relay_type(self) -> RelayType:
        """Returns the type of the relay."""
        return self.mspconfig.type

    @property
    def function(self) -> RelayFunction:
        """Returns the function of the relay."""
        return self.mspconfig.function

    @property
    def state(self) -> RelayState:
        """Returns the current state of the relay."""
        return self.telemetry.state

    @property
    def why_on(self) -> RelayWhyOn:
        """Returns the reason why the relay is on."""
        return self.telemetry.why_on

    @property
    def is_on(self) -> bool:
        """Returns whether the relay is currently on."""
        return self.state == RelayState.ON

    @control_method
    async def turn_on(self) -> None:
        """Turn on the relay.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Cannot turn on relay: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)
        await self._api.async_set_equipment(self.bow_id, self.system_id, True)

    @control_method
    async def turn_off(self) -> None:
        """Turn off the relay.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Cannot turn off relay: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)
        await self._api.async_set_equipment(self.bow_id, self.system_id, False)
