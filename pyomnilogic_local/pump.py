from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPPump
from pyomnilogic_local.models.telemetry import TelemetryPump


class Pump(OmniEquipment[MSPPump, TelemetryPump]):
    """Represents a pump in the OmniLogic system."""
