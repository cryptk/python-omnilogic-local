from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPRelay
from pyomnilogic_local.models.telemetry import TelemetryRelay


class Relay(OmniEquipment[MSPRelay, TelemetryRelay]):
    """Represents a relay in the OmniLogic system."""
