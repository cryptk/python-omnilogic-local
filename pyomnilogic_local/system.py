from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPSystem


class System:
    """Represents the main system equipment in the OmniLogic system."""

    mspconfig: MSPSystem

    def __init__(self, mspconfig: MSPSystem) -> None:
        self.update_config(mspconfig)

    @property
    def vsp_speed_format(self) -> Literal["RPM", "Percent"]:
        """The VSP speed format of the system."""
        return self.mspconfig.vsp_speed_format

    @property
    def units(self) -> Literal["Standard", "Metric"]:
        """The units of the system."""
        return self.mspconfig.units

    def update_config(self, mspconfig: MSPSystem) -> None:
        """Update the configuration data for the equipment."""
        self.mspconfig = mspconfig
