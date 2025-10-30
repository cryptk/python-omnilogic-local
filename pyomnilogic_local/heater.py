from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPVirtualHeater
from pyomnilogic_local.models.telemetry import TelemetryHeater


class Heater(OmniEquipment[MSPVirtualHeater, TelemetryHeater]):
    """Represents a heater in the OmniLogic system."""
