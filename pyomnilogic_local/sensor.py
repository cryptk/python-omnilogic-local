from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPSensor
from pyomnilogic_local.models.telemetry import Telemetry
from pyomnilogic_local.omnitypes import SensorType, SensorUnits

if TYPE_CHECKING:
    from pyomnilogic_local.omnilogic import OmniLogic


class Sensor(OmniEquipment[MSPSensor, None]):
    """
    Represents a sensor in the OmniLogic system.

    Note: Sensors don't have their own telemetry - they contribute data to
    other equipment (like BoW, Backyard, Heaters, etc.)
    """

    mspconfig: MSPSensor

    def __init__(self, omni: "OmniLogic", mspconfig: MSPSensor, telemetry: Telemetry | None) -> None:
        super().__init__(omni, mspconfig, telemetry)

    @property
    def sensor_type(self) -> SensorType | str:
        """
        Returns the type of sensor.

        Can be AIR_TEMP, SOLAR_TEMP, WATER_TEMP, FLOW, ORP, or EXT_INPUT.
        """
        return self.mspconfig.equip_type

    @property
    def units(self) -> SensorUnits | str:
        """
        Returns the units used by the sensor.

        Can be FAHRENHEIT, CELSIUS, PPM, GRAMS_PER_LITER, MILLIVOLTS,
        NO_UNITS, or ACTIVE_INACTIVE.
        """
        return self.mspconfig.units
