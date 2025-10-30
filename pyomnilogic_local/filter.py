from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPFilter
from pyomnilogic_local.models.telemetry import TelemetryFilter


class Filter(OmniEquipment[MSPFilter, TelemetryFilter]):
    """Represents a filter in the OmniLogic system."""
