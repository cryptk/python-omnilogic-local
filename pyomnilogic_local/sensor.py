from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPSensor


class Sensor(OmniEquipment[MSPSensor, None]):
    """Represents a sensor in the OmniLogic system.

    Note: Sensors don't have their own telemetry - they contribute data to
    other equipment (like BoW, Backyard, Heaters, etc.)
    """
