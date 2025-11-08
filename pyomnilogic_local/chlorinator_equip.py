from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPChlorinatorEquip

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic
    from pyomnilogic_local.omnitypes import ChlorinatorType


class ChlorinatorEquipment(OmniEquipment[MSPChlorinatorEquip, None]):
    """Represents physical chlorinator equipment in the OmniLogic system.

    ChlorinatorEquipment represents an individual physical chlorinator device
    (salt cell, liquid dispenser, tablet feeder, etc.). It is controlled by a
    parent Chlorinator which manages one or more physical chlorinator units.

    The OmniLogic system uses a parent/child chlorinator architecture:
    - Chlorinator: User-facing chlorinator control (turn_on, set_timed_percent, etc.)
    - ChlorinatorEquipment: Individual physical chlorination devices managed by the parent

    This architecture allows the system to coordinate multiple chlorination sources
    under a single chlorinator interface.

    Chlorinator Equipment Types:
        - MAIN_PANEL: Main panel chlorinator
        - DISPENSER: Chemical dispenser
        - AQUA_RITE: AquaRite chlorinator system

    Note: Unlike heater equipment, chlorinator equipment does not have separate
    telemetry entries. All telemetry is reported through the parent Chlorinator.

    Attributes:
        mspconfig: Configuration data for this physical chlorinator equipment

    Properties (Configuration):
        equip_type: Equipment type (always "PET_CHLORINATOR")
        chlorinator_type: Type of chlorinator (MAIN_PANEL, DISPENSER, AQUA_RITE)
        enabled: Whether this chlorinator equipment is enabled

    Example:
        >>> pool = omni.backyard.bow["Pool"]
        >>> chlorinator = pool.chlorinator
        >>>
        >>> # Access physical chlorinator equipment
        >>> for equip in chlorinator.chlorinator_equipment:
        ...     print(f"Chlorinator Equipment: {equip.name}")
        ...     print(f"Type: {equip.chlorinator_type}")
        ...     print(f"Enabled: {equip.enabled}")
        ...     print(f"System ID: {equip.system_id}")

    Important Notes:
        - ChlorinatorEquipment is read-only (no direct control methods)
        - Control chlorinator equipment through the parent Chlorinator instance
        - Multiple chlorinator equipment can work together
        - Telemetry is accessed through the parent Chlorinator, not individual equipment
        - Equipment may be disabled but still configured in the system
    """

    mspconfig: MSPChlorinatorEquip
    telemetry: None

    def __init__(self, omni: OmniLogic, mspconfig: MSPChlorinatorEquip, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    @property
    def equip_type(self) -> Literal["PET_CHLORINATOR"]:
        """Returns the equipment type (always 'PET_CHLORINATOR')."""
        return self.mspconfig.equip_type

    @property
    def chlorinator_type(self) -> ChlorinatorType:
        """Returns the type of chlorinator (MAIN_PANEL, DISPENSER, or AQUA_RITE)."""
        return self.mspconfig.chlorinator_type

    @property
    def enabled(self) -> bool:
        """Returns whether the chlorinator equipment is enabled in configuration."""
        return self.mspconfig.enabled
