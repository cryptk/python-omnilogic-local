from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPSystem


class System:
    """Represents the main system equipment in the OmniLogic system."""

    mspconfig: MSPSystem

    def __init__(self, mspconfig: MSPSystem) -> None:
        self.update_config(mspconfig)

    @property
    def vsp_speed_format(self) -> str | None:
        """The VSP speed format of the system."""
        return self.mspconfig.vsp_speed_format

    @property
    def units(self) -> str | None:
        """The units of the system."""
        return self.mspconfig.units

    def update_config(self, mspconfig: MSPSystem) -> None:
        """Update the configuration data for the equipment."""
        self.mspconfig = mspconfig
