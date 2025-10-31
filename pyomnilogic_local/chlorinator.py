from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPChlorinator
from pyomnilogic_local.models.telemetry import TelemetryChlorinator


class Chlorinator(OmniEquipment[MSPChlorinator, TelemetryChlorinator]):
    """Represents a chlorinator in the OmniLogic system."""

    mspconfig: MSPChlorinator
    telemetry: TelemetryChlorinator
