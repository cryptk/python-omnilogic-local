from __future__ import annotations

from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.models.mspconfig import MSPSensor

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic
    from pyomnilogic_local.omnitypes import SensorType, SensorUnits


class Sensor(OmniEquipment[MSPSensor, None]):
    """Represents a sensor in the OmniLogic system.

    Sensors are monitoring devices that measure various environmental and system
    parameters. Unlike other equipment, sensors do not have their own telemetry
    data structure - instead, they contribute readings to the telemetry of other
    equipment (Backyard, BoW, Heater, etc.).

    Sensor Types:
        - AIR_TEMP: Measures ambient air temperature
        - SOLAR_TEMP: Measures solar collector temperature
        - WATER_TEMP: Measures water temperature in pool/spa
        - FLOW: Detects water flow (binary on/off)
        - ORP: Measures Oxidation-Reduction Potential (chlorine effectiveness)
        - EXT_INPUT: External input sensor (various purposes)

    Sensors are read-only monitoring devices with no control methods.
    Their readings appear in the telemetry of associated equipment:
    - Air temperature → Backyard telemetry
    - Water temperature → BoW (Body of Water) telemetry
    - Solar temperature → Heater telemetry
    - Flow → BoW telemetry
    - ORP → CSAD telemetry

    Attributes:
        mspconfig: Configuration data for this sensor from MSP XML
        telemetry: Always None (sensors don't have their own telemetry)

    Properties:
        sensor_type: Type of sensor (AIR_TEMP, WATER_TEMP, FLOW, etc.)
        units: Units of measurement (FAHRENHEIT, CELSIUS, MILLIVOLTS, etc.)
        name: Sensor name from configuration
        system_id: Unique system identifier

    Example:
        >>> pool = omni.backyard.bow["Pool"]
        >>> sensors = pool.sensors
        >>>
        >>> # Iterate through sensors
        >>> for sensor in sensors:
        ...     print(f"{sensor.name}: {sensor.sensor_type} ({sensor.units})")
        >>>
        >>> # Get readings from parent equipment telemetry
        >>> # Water temp sensor → BoW telemetry
        >>> water_temp = pool.water_temp
        >>>
        >>> # Air temp sensor → Backyard telemetry
        >>> air_temp = omni.backyard.air_temp
        >>>
        >>> # Flow sensor → BoW telemetry
        >>> has_flow = pool.flow > 0

    Important:
        Sensors do NOT have their own telemetry or state. To get sensor readings,
        access the telemetry of the parent equipment:

        - For water temperature: Use bow.water_temp
        - For air temperature: Use backyard.air_temp
        - For flow: Use bow.flow
        - For ORP: Use csad.current_orp

    Note:
        - Sensors are passive monitoring devices (no control methods)
        - Sensor readings update as part of parent equipment telemetry refresh
        - Temperature sensors may use Fahrenheit or Celsius (check units property)
        - Flow sensors typically return 255 for flow, 0 for no flow
        - ORP sensors measure in millivolts (typically 400-800 mV)
    """

    mspconfig: MSPSensor

    def __init__(self, omni: OmniLogic, mspconfig: MSPSensor, telemetry: Telemetry | None) -> None:
        super().__init__(omni, mspconfig, telemetry)

    @property
    def sensor_type(self) -> SensorType | str:
        """Returns the type of sensor.

        Can be AIR_TEMP, SOLAR_TEMP, WATER_TEMP, FLOW, ORP, or EXT_INPUT.
        """
        return self.mspconfig.equip_type

    @property
    def units(self) -> SensorUnits | str:
        """Returns the units used by the sensor.

        Can be FAHRENHEIT, CELSIUS, PPM, GRAMS_PER_LITER, MILLIVOLTS,
        NO_UNITS, or ACTIVE_INACTIVE.
        """
        return self.mspconfig.units
