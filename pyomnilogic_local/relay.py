from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.decorators import dirties_state
from pyomnilogic_local.models.mspconfig import MSPRelay
from pyomnilogic_local.models.telemetry import Telemetry, TelemetryRelay
from pyomnilogic_local.omnitypes import RelayFunction, RelayState, RelayType, RelayWhyOn
from pyomnilogic_local.util import OmniEquipmentNotInitializedError

if TYPE_CHECKING:
    from pyomnilogic_local.omnilogic import OmniLogic


class Relay(OmniEquipment[MSPRelay, TelemetryRelay]):
    """Represents a relay in the OmniLogic system."""

    def __init__(self, omni: "OmniLogic", mspconfig: MSPRelay, telemetry: Telemetry) -> None:
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

    @dirties_state()
    async def turn_on(self) -> None:
        """
        Turns the relay on.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            raise OmniEquipmentNotInitializedError("Cannot turn on relay: bow_id or system_id is None")
        await self._api.async_set_equipment(self.bow_id, self.system_id, True)

    @dirties_state()
    async def turn_off(self) -> None:
        """
        Turns the relay off.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            raise OmniEquipmentNotInitializedError("Cannot turn off relay: bow_id or system_id is None")
        await self._api.async_set_equipment(self.bow_id, self.system_id, False)
