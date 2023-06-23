from enum import Enum

from .util import PrettyEnum


# OmniAPI Enums
class MessageType(Enum):
    XML_ACK = 0000
    REQUEST_CONFIGURATION = 1
    SET_FILTER_SPEED = 9
    SET_HEATER_COMMAND = 11
    SET_SUPERCHLORINATE = 15
    REQUEST_LOG_CONFIG = 31
    SET_SOLAR_SET_POINT_COMMAND = 40
    SET_HEATER_MODE_COMMAND = 42
    SET_CHLOR_ENABLED = 121
    SET_HEATER_ENABLED = 147
    SET_CHLOR_PARAMS = 155
    SET_EQUIPMENT = 164
    CREATE_SCHEDULE = 230
    DELETE_SCHEDULE = 231
    GET_TELEMETRY = 300
    GET_ALARM_LIST = 304
    SET_STANDALONE_LIGHT_SHOW = 308
    SET_SPILLOVER = 311
    RESTORE_IDLE_STATE = 340
    GET_FILTER_DIAGNOSTIC_INFO = 386
    HANDSHAKE = 1000
    ACK = 1002
    MSP_TELEMETRY_UPDATE = 1004
    MSP_CONFIGURATIONUPDATE = 1003
    MSP_ALARM_LIST = 1304
    MSP_LEADMESSAGE = 1998
    MSP_BLOCKMESSAGE = 1999


class ClientType(Enum):
    XML = 0
    SIMPLE = 1
    OMNI = 3


class OmniType(str, Enum):
    BACKYARD = "Backyard"
    BOW = "BodyOfWater"
    BOW_MSP = "Body-of-water"
    CHLORINATOR = "Chlorinator"
    CHLORINATOR_EQUIP = "Chlorinator-Equipment"
    CL_LIGHT = "ColorLogic-Light"
    FAVORITES = "Favorites"
    FILTER = "Filter"
    GROUP = "Group"
    GROUPS = "Groups"
    HEATER = "Heater"
    HEATER_EQUIP = "Heater-Equipment"
    PUMP = "Pump"
    RELAY = "Relay"
    SCHE = "sche"
    SCHEDULE = "Schedule"
    SENSOR = "Sensor"
    SYSTEM = "System"
    VALVE_ACTUATOR = "ValveActuator"
    VIRT_HEATER = "VirtualHeater"


# Backyard/BoW
class BackyardState(PrettyEnum):
    OFF = 0
    ON = 1
    SERVICE_MODE = 2
    CONFIG_MODE = 3
    TIMED_SERVICE_MODE = 4


class BodyOfWaterState(PrettyEnum):
    NO_FLOW = 0
    FLOW = 1


class BodyOfWaterType(str, PrettyEnum):
    POOL = "BOW_POOL"
    SPA = "BOW_SPA"


# Chlorinators
# Chlorinator status is a bitmask that we still need to figure out
# class ChlorinatorStatus(str,Enum):
#     pass
class ChlorinatorOperatingMode(PrettyEnum):
    TIMED = 1
    ORP = 2


class ChlorinatorDispenserType(str, PrettyEnum):
    SALT = "SALT_DISPENSING"


# Lights
class ColorLogicSpeed(PrettyEnum):
    ONE_SIXTEENTH = 0
    ONE_EIGHTH = 1
    ONE_QUARTER = 2
    ONE_HALF = 3
    ONE_TIMES = 4
    TWO_TIMES = 5
    FOUR_TIMES = 6
    EIGHT_TIMES = 7
    SIXTEEN_TIMES = 8


class ColorLogicBrightness(PrettyEnum):
    TWENTY_PERCENT = 0
    FOURTY_PERCENT = 1
    SIXTY_PERCENT = 2
    EIGHTY_PERCENT = 3
    ONE_HUNDRED_PERCENT = 4


class ColorLogicShow(PrettyEnum):
    VOODOO_LOUNGE = 0
    DEEP_BLUE_SEA = 1
    ROYAL_BLUE = 2
    AFTERNOON_SKY = 3
    AQUA_GREEN = 4
    EMERALD = 5
    CLOUD_WHITE = 6
    WARM_RED = 7
    FLAMINGO = 8
    VIVID_VIOLET = 9
    SANGRIA = 10
    TWILIGHT = 11
    TRANQUILITY = 12
    GEMSTONE = 13
    USA = 14
    MARDI_GRAS = 15
    COOL_CABARET = 16
    #### The below options only work on lights that support OmniDirect / V2-Active in MSPConfig
    YELLOW = 17
    ORANGE = 18
    GOLD = 19
    MINT = 20
    TEAL = 21
    BURNT_ORANGE = 22
    PURE_WHITE = 23
    CRISP_WHITE = 24
    WARM_WHITE = 25
    BRIGHT_YELLOW = 26


class ColorLogicPowerState(PrettyEnum):
    OFF = 0
    POWERING_OFF = 1
    CHANGING_SHOW = 3
    FIFTEEN_SECONDS_WHITE = 4
    ACTIVE = 6
    COOLDOWN = 7


class ColorLogicLightType(str, PrettyEnum):
    UCL = "COLOR_LOGIC_UCL"
    FOUR_ZERO = "COLOR_LOGIC_4_0"
    TWO_FIVE = "COLOR_LOGIC_2_5"


# Chemistry Sense and Dispense
class CSADStatus(PrettyEnum):
    NOT_DISPENSING = 0
    DISPENSING = 1


class CSADMode(PrettyEnum):
    OFF = 0
    AUTO = 1
    FORCE_ON = 2
    MONITORING = 3
    DISPENSING_OFF = 4


# Filters
class FilterState(PrettyEnum):
    OFF = 0
    ON = 1
    PRIMING = 2
    WAITING_TURN_OFF = 3
    WAITING_TURN_OFF_MANUAL = 4
    HEATER_EXTEND = 5
    COOLDOWN = 6
    SUSPEND = 7
    CSAD_EXTEND = 8
    FILTER_SUPERCHLORINATE = 9
    FILTER_FORCE_PRIMING = 10
    FILTER_WAITING_TURN_OFF = 11


class FilterType(str, PrettyEnum):
    VARIABLE_SPEED = "FMT_VARIABLE_SPEED_PUMP"
    DUAL_SPEED = "FMT_DUAL_SPEED"
    SINGLE_SPEED = "FMT_SINGLE_SPEED"


class FilterValvePosition(PrettyEnum):
    POOL_ONLY = 1
    SPA_ONLY = 2
    SPILLOVER = 3
    LOW_PRIO_HEAT = 4
    HIGH_PRIO_HEAT = 5


class FilterWhyOn(PrettyEnum):
    OFF = 0
    NO_WATER_FLOW = 1
    COOLDOWN = 2
    PH_REDUCE_EXTEND = 3
    HEATER_EXTEND = 4
    PAUSED = 5
    VALVE_CHANGING = 6
    FORCE_HIGH_SPEED = 7
    OFF_EXTERNAL_INTERLOCK = 8
    SUPER_CHLORINATE = 9
    COUNTDOWN = 10
    MANUAL_ON = 11
    MANUAL_SPILLOVER = 12
    TIMER_SPILLOVER = 13
    TIMER_ON = 14
    FREEZE_PROTECT = 15
    UNKNOWN_16 = 16
    UNKNOWN_17 = 17
    UNKNOWN_18 = 18


# Heaters
class HeaterState(PrettyEnum):
    OFF = 0
    ON = 1
    PAUSE = 2


class HeaterType(str, PrettyEnum):
    GAS = "HTR_GAS"
    HEAT_PUMP = "HTR_HEAT_PUMP"
    SOLAR = "HTR_SOLAR"
    ELECTRIC = "HTR_ELECTRIC"
    GEOTHERMAL = "HTR_GEOTHERMAL"
    SMART = "HTR_SMART"


class HeaterMode(PrettyEnum):
    HEAT = 0
    COOL = 1
    AUTO = 2


# Pumps
class PumpState(PrettyEnum):
    OFF = 0
    ON = 1


class PumpType(str, PrettyEnum):
    SINGLE_SPEED = "PMP_SINGLE_SPEED"
    DUAL_SPEED = "PMP_DUAL_SPEED"
    VARIABLE_SPEED = "PMP_VARIABLE_SPEED_PUMP"


class PumpFunction(str, PrettyEnum):
    PUMP = "PMP_PUMP"
    WATER_FEATURE = "PMP_WATER_FEATURE"
    CLEANER = "PMP_CLEANER"
    WATER_SLIDE = "PMP_WATER_SLIDE"
    WATERFALL = "PMP_WATERFALL"
    LAMINARS = "PMP_LAMINARS"
    FOUNTAIN = "PMP_FOUNTAIN"
    JETS = "PMP_JETS"
    BLOWER = "PMP_BLOWER"
    ACCESSORY = "PMP_ACCESSORY"
    CLEANER_PRESSURE = "PMP_CLEANER_PRESSURE"
    CLEANER_SUCTION = "PMP_CLEANER_SUCTION"
    CLEANER_ROBOTIC = "PMP_CLEANER_ROBOTIC"
    CLEANER_IN_FLOOR = "PMP_CLEANER_IN_FLOOR"


# Relays
class RelayFunction(str, PrettyEnum):
    WATER_FEATURE = "RLY_WATER_FEATURE"
    LIGHT = "RLY_LIGHT"
    BACKYARD_LIGHT = "RLY_BACKYARD_LIGHT"
    POOL_LIGHT = "RLY_POOL_LIGHT"
    CLEANER = "RLY_CLEANER"
    WATER_SLIDE = "RLY_WATER_SLIDE"
    WATERFALL = "RLY_WATERFALL"
    LAMINARS = "RLY_LAMINARS"
    FOUNTAIN = "RLY_FOUNTAIN"
    FIREPIT = "RLY_FIREPIT"
    JETS = "RLY_JETS"
    BLOWER = "RLY_BLOWER"
    ACCESSORY = "RLY_ACCESSORY"
    CLEANER_PRESSURE = "RLY_CLEANER_PRESSURE"
    CLEANER_SUCTION = "RLY_CLEANER_SUCTION"
    CLEANER_ROBOTIC = "RLY_CLEANER_ROBOTIC"
    CLEANER_IN_FLOOR = "RLY_CLEANER_IN_FLOOR"


class RelayState(PrettyEnum):
    OFF = 0
    ON = 1


class RelayType(str, PrettyEnum):
    VALVE_ACTUATOR = "RLY_VALVE_ACTUATOR"
    HIGH_VOLTAGE = "RLY_HIGH_VOLTAGE_RELAY"
    LOW_VOLTAGE = "RLY_LOW_VOLTAGE_RELAY"


# Sensors
class SensorType(str, PrettyEnum):
    AIR_TEMP = "SENSOR_AIR_TEMP"
    SOLAR_TEMP = "SENSOR_SOLAR_TEMP"
    WATER_TEMP = "SENSOR_WATER_TEMP"
    FLOW = "SENSOR_FLOW"
    ORP = "SENSOR_ORP"
    EXT_INPUT = "SENSOR_EXT_INPUT"


class SensorUnits(str, PrettyEnum):
    FAHRENHEIT = "UNITS_FAHRENHEIT"
    CELSIUS = "UNITS_CELSIUS"
    PPM = "UNITS_PPM"
    GRAMS_PER_LITER = "UNITS_GRAMS_PER_LITER"
    MILLIVOLTS = "UNITS_MILLIVOLTS"
    NO_UNITS = "UNITS_NO_UNITS"
    ACTIVE_INACTIVE = "UNITS_ACTIVE_INACTIVE"


# Valve Actuators
class ValveActuatorState(PrettyEnum):
    OFF = 0
    ON = 1
