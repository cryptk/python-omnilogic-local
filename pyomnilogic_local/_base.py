from typing import Any

from pyomnilogic_local.models import MSPEquipmentType, Telemetry


class OmniEquipment:
    """Base class for OmniLogic equipment."""

    def __init__(self, mspconfig: MSPEquipmentType, telemetry: Telemetry | None = None) -> None:
        """Initialize the equipment with configuration and telemetry data."""
        # If the Equipment has subdevices, we don't store those as part of this device's config
        # They will get parsed and stored as their own equipment instances
        try:
            self.mspconfig = mspconfig.without_subdevices()
        except AttributeError:
            self.mspconfig = mspconfig

        if hasattr(self, "telemetry") and telemetry is not None:
            self.telemetry = telemetry.get_telem_by_systemid(self.mspconfig.system_id)

        # Populate fields from MSP configuration and telemetry
        # This is some moderate magic to avoid having to manually set each field
        # The TL;DR is that we loop over all fields defined in the MSPConfig and Telemetry models
        # and set the corresponding attributes on this equipment instance.
        for field in self.mspconfig.__class__.model_fields:
            if getattr(self.mspconfig, field, None) is not None:
                setattr(self, field, self._from_mspconfig(field))
        for field in self.mspconfig.__class__.model_computed_fields:
            if getattr(self.mspconfig, field, None) is not None:
                setattr(self, field, self._from_mspconfig(field))
        if hasattr(self, "telemetry") and self.telemetry is not None:
            for field in self.telemetry.__class__.model_fields:
                if getattr(self.telemetry, field, None) is not None:
                    setattr(self, field, self._from_telemetry(field))
            for field in self.telemetry.__class__.model_computed_fields:
                if getattr(self.telemetry, field, None) is not None:
                    setattr(self, field, self._from_telemetry(field))

    def update_config(self, mspconfig: MSPEquipmentType) -> None:
        """Update the configuration data for the equipment."""
        if hasattr(self, "mspconfig"):
            self.mspconfig = mspconfig.without_subdevices()
        else:
            raise NotImplementedError("This equipment does not have MSP configuration.")

    def update_telemetry(self, telemetry: Telemetry) -> None:
        """Update the telemetry data for the equipment."""
        if hasattr(self, "telemetry"):
            self.telemetry = telemetry.get_telem_by_systemid(self.mspconfig.system_id)
        else:
            raise NotImplementedError("This equipment does not have telemetry data.")

    def _from_mspconfig(self, attribute: str) -> Any:
        """Helper method to get a value from the MSP configuration."""
        return getattr(self.mspconfig, attribute, None)

    def _from_telemetry(self, attribute: str) -> Any:
        """Helper method to get a value from the telemetry data."""
        if hasattr(self, "telemetry"):
            return getattr(self.telemetry, attribute, None)
        return None
