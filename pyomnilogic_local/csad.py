from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPCSAD
from pyomnilogic_local.models.telemetry import TelemetryCSAD


class CSAD(OmniEquipment[MSPCSAD, TelemetryCSAD]):
    """Represents a CSAD in the OmniLogic system."""

    mspconfig: MSPCSAD
    telemetry: TelemetryCSAD
