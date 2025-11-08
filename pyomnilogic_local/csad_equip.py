"""CSAD equipment classes for Omnilogic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPCSADEquip

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic
    from pyomnilogic_local.omnitypes import CSADEquipmentType


class CSADEquipment(OmniEquipment[MSPCSADEquip, None]):
    """Represents a CSAD (chemical automation) equipment device.

    CSADEquipment represents an individual physical CSAD device (e.g., AQL-CHEM).
    It is controlled by a parent CSAD which manages one or more physical CSAD units.

    The OmniLogic system uses a parent/child CSAD architecture:
    - CSAD: User-facing CSAD control (monitoring, dispensing)
    - CSADEquipment: Individual physical CSAD devices managed by the parent

    CSAD Equipment Types:
        - AQL_CHEM: AquaLink Chemistry System

    Note: Like chlorinator equipment, CSAD equipment does not have separate
    telemetry entries. All telemetry is reported through the parent CSAD.

    Attributes:
        mspconfig: Configuration data for this physical CSAD equipment

    Properties (Configuration):
        equip_type: Equipment type (always "PET_CSAD")
        csad_type: Type of CSAD equipment (e.g., AQL_CHEM)
        enabled: Whether this CSAD equipment is enabled

    Example:
        >>> pool = omni.backyard.bow["Pool"]
        >>> csad = pool.get_csad()
        >>>
        >>> # Access physical CSAD equipment
        >>> for equip in csad.csad_equipment:
        ...     print(f"CSAD Equipment: {equip.name}")
        ...     print(f"Type: {equip.csad_type}")
        ...     print(f"Enabled: {equip.enabled}")
        ...     print(f"System ID: {equip.system_id}")

    Important Notes:
        - CSADEquipment is read-only (no direct control methods)
        - Control CSAD equipment through the parent CSAD instance
        - Telemetry is accessed through the parent CSAD, not individual equipment
        - Equipment may be disabled but still configured in the system
    """

    mspconfig: MSPCSADEquip
    telemetry: None

    def __init__(self, omni: OmniLogic, mspconfig: MSPCSADEquip, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    @property
    def equip_type(self) -> Literal["PET_CSAD"]:
        """Returns the equipment type (always 'PET_CSAD')."""
        return self.mspconfig.equip_type

    @property
    def csad_type(self) -> CSADEquipmentType | str:
        """Returns the type of CSAD equipment (e.g., AQL_CHEM)."""
        return self.mspconfig.csad_type

    @property
    def enabled(self) -> bool:
        """Returns whether the CSAD equipment is enabled in configuration."""
        return self.mspconfig.enabled
