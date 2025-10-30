from enum import Enum, Flag, IntEnum, StrEnum

from .util import PrettyEnum


# OmniAPI Enums
class MessageType(Enum):
    XML_ACK = 0000
    REQUEST_CONFIGURATION = 1
    SET_FILTER_SPEED = 9
    SET_HEATER_COMMAND = 11
    SET_SUPERCHLORINATE = 15
    SET_SOLAR_SET_POINT_COMMAND = 40
    SET_HEATER_MODE_COMMAND = 42
    SET_CHLOR_ENABLED = 121
    SET_HEATER_ENABLED = 147
    SET_CHLOR_PARAMS = 155
    SET_EQUIPMENT = 164
    CREATE_SCHEDULE = 230
    DELETE_SCHEDULE = 231
    GET_TELEMETRY = 300
    SET_STANDALONE_LIGHT_SHOW = 308
    SET_SPILLOVER = 311
    RUN_GROUP_CMD = 317
    RESTORE_IDLE_STATE = 340
    GET_FILTER_DIAGNOSTIC_INFO = 386
    HANDSHAKE = 1000
    ACK = 1002
    MSP_TELEMETRY_UPDATE = 1004
    MSP_CONFIGURATIONUPDATE = 1003
    MSP_LEADMESSAGE = 1998
    MSP_BLOCKMESSAGE = 1999


class ClientType(IntEnum, PrettyEnum):
    XML = 0
    SIMPLE = 1
    OMNI = 3


class OmniType(StrEnum):
    BACKYARD = "Backyard"
    BOW = "BodyOfWater"
    BOW_MSP = "Body-of-water"
    CHLORINATOR = "Chlorinator"
    CHLORINATOR_EQUIP = "Chlorinator-Equipment"
    CSAD = "CSAD"
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
class BackyardState(IntEnum, PrettyEnum):
    OFF = 0
    ON = 1
    SERVICE_MODE = 2
    CONFIG_MODE = 3
    TIMED_SERVICE_MODE = 4


class BodyOfWaterState(IntEnum, PrettyEnum):
    NO_FLOW = 0
    FLOW = 1


class BodyOfWaterType(StrEnum, PrettyEnum):
    POOL = "BOW_POOL"
    SPA = "BOW_SPA"


# Chlorinators
class ChlorinatorStatus(Flag):
    """Chlorinator status flags.

    These flags represent the current operational state of the chlorinator
    and can be combined (multiple flags can be active simultaneously).
    """

    ERROR_PRESENT = 1 << 0  # Error present, check chlrError value
    ALERT_PRESENT = 1 << 1  # Alert present, check chlrAlert value
    GENERATING = 1 << 2  # Power is applied to T-Cell (actively chlorinating)
    SYSTEM_PAUSED = 1 << 3  # System processor is pausing chlorination
    LOCAL_PAUSED = 1 << 4  # Local processor is pausing chlorination
    AUTHENTICATED = 1 << 5  # T-Cell is authenticated
    K1_ACTIVE = 1 << 6  # K1 relay is active
    K2_ACTIVE = 1 << 7  # K2 relay is active


class ChlorinatorAlert(Flag):
    """Chlorinator alert flags.

    Multi-bit fields are represented by their individual values.
    Use the helper properties on TelemetryChlorinator for semantic interpretation.
    """

    SALT_LOW = 1 << 0  # Salt level is low
    SALT_TOO_LOW = 1 << 1  # Salt level is too low
    HIGH_CURRENT = 1 << 2  # High current alert
    LOW_VOLTAGE = 1 << 3  # Low voltage alert
    CELL_TEMP_LOW = 1 << 4  # Cell water temperature low
    CELL_TEMP_SCALEBACK = 1 << 5  # Cell water temperature scaleback
    # CELL_TEMP_LOW and CELL_TEMP_SCALEBACK = CELL_TEMP_HIGH
    BOARD_TEMP_HIGH = 1 << 6  # Board temperature high
    BOARD_TEMP_CLEARING = 1 << 7  # Board temperature clearing
    CELL_CLEAN = 1 << 11  # Cell cleaning runtime alert


class ChlorinatorError(Flag):
    """Chlorinator error flags.

    Multi-bit fields are represented by their individual values.
    Use the helper properties on TelemetryChlorinator for semantic interpretation.
    """

    CURRENT_SENSOR_SHORT = 1 << 0
    CURRENT_SENSOR_OPEN = 1 << 1
    VOLTAGE_SENSOR_SHORT = 1 << 2
    VOLTAGE_SENSOR_OPEN = 1 << 3
    CELL_TEMP_SENSOR_SHORT = 1 << 4
    CELL_TEMP_SENSOR_OPEN = 1 << 5
    BOARD_TEMP_SENSOR_SHORT = 1 << 6
    BOARD_TEMP_SENSOR_OPEN = 1 << 7
    K1_RELAY_SHORT = 1 << 8
    K1_RELAY_OPEN = 1 << 9
    K2_RELAY_SHORT = 1 << 10
    K2_RELAY_OPEN = 1 << 11
    CELL_ERROR_TYPE = 1 << 12
    CELL_ERROR_AUTH = 1 << 13
    AQUARITE_PCB_ERROR = 1 << 14


class ChlorinatorOperatingMode(IntEnum, PrettyEnum):
    DISABLED = 0
    TIMED = 1
    ORP_AUTO = 2
    ORP_TIMED_RW = 3  # CSAD in ORP mode experienced condition that prevents ORP operation


class ChlorinatorDispenserType(StrEnum, PrettyEnum):
    SALT = "SALT_DISPENSING"
    LIQUID = "LIQUID_DISPENSING"
    TABLET = "TABLET_DISPENSING"


class ChlorinatorCellType(StrEnum, PrettyEnum):
    UNKNOWN = "CELL_TYPE_UNKNOWN"
    T3 = "CELL_TYPE_T3"
    T5 = "CELL_TYPE_T5"
    T9 = "CELL_TYPE_T9"
    T15 = "CELL_TYPE_T15"
    T15_LS = "CELL_TYPE_T15_LS"
    TCELLS315 = "CELL_TYPE_TCELLS315"
    TCELLS325 = "CELL_TYPE_TCELLS325"
    TCELLS340 = "CELL_TYPE_TCELLS340"
    LIQUID = "CELL_TYPE_LIQUID"
    TABLET = "CELL_TYPE_TABLET"

    # There is probably an easier way to do this
    def __int__(self) -> int:
        return ChlorinatorCellInt[self.name].value


class ChlorinatorCellInt(IntEnum, PrettyEnum):
    UNKNOWN = 0
    T3 = 1
    T5 = 2
    T9 = 3
    T15 = 4
    T15_LS = 5
    TCELLS315 = 6
    TCELLS325 = 7
    TCELLS340 = 8
    LIQUID = 9
    TABLET = 10


# Lights
class ColorLogicSpeed(IntEnum, PrettyEnum):
    ONE_SIXTEENTH = 0
    ONE_EIGHTH = 1
    ONE_QUARTER = 2
    ONE_HALF = 3
    ONE_TIMES = 4
    TWO_TIMES = 5
    FOUR_TIMES = 6
    EIGHT_TIMES = 7
    SIXTEEN_TIMES = 8


class ColorLogicBrightness(IntEnum, PrettyEnum):
    TWENTY_PERCENT = 0
    FOURTY_PERCENT = 1
    SIXTY_PERCENT = 2
    EIGHTY_PERCENT = 3
    ONE_HUNDRED_PERCENT = 4


type LightShows = ColorLogicShow25 | ColorLogicShow40 | ColorLogicShowUCL | ColorLogicShowUCLV2 | PentairShow | ZodiacShow


class ColorLogicShow25(IntEnum, PrettyEnum):
    VOODOO_LOUNGE = 0
    DEEP_BLUE_SEA = 1
    AFTERNOON_SKY = 2
    EMERALD = 3
    SANGRIA = 4
    CLOUD_WHITE = 5
    TWILIGHT = 6
    TRANQUILITY = 7
    GEMSTONE = 8
    USA = 9
    MARDI_GRAS = 10
    COOL_CABARET = 11


class ColorLogicShow40(IntEnum, PrettyEnum):
    VOODOO_LOUNGE = 0
    DEEP_BLUE_SEA = 1
    AFTERNOON_SKY = 2
    EMERALD = 3
    SANGRIA = 4
    CLOUD_WHITE = 5
    TWILIGHT = 6
    TRANQUILITY = 7
    GEMSTONE = 8
    USA = 9
    MARDI_GRAS = 10
    COOL_CABARET = 11


class ColorLogicShowUCL(IntEnum, PrettyEnum):
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


class ColorLogicShowUCLV2(IntEnum, PrettyEnum):
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


class PentairShow(IntEnum, PrettyEnum):
    SAM = 0
    PARTY = 1
    ROMANCE = 2
    CARIBBEAN = 3
    AMERICAN = 4
    CALIFORNIA_SUNSET = 5
    ROYAL = 6
    BLUE = 7
    GREEN = 8
    RED = 9
    WHITE = 10
    MAGENTA = 11


class ZodiacShow(IntEnum, PrettyEnum):
    ALPINE_WHITE = 0
    SKY_BLUE = 1
    COBALT_BLUE = 2
    CARIBBEAN_BLUE = 3
    SPRING_GREEN = 4
    EMERALD_GREEN = 5
    EMERALD_ROSE = 6
    MAGENTA = 7
    VIOLET = 8
    SLOW_COLOR_SPLASH = 9
    FAST_COLOR_SPLASH = 10
    AMERICA_THE_BEAUTIFUL = 11
    FAT_TUESDAY = 12
    DISCO_TECH = 13


class ColorLogicPowerState(IntEnum, PrettyEnum):
    OFF = 0
    POWERING_OFF = 1
    CHANGING_SHOW = 3
    FIFTEEN_SECONDS_WHITE = 4
    ACTIVE = 6
    COOLDOWN = 7


class ColorLogicLightType(StrEnum, PrettyEnum):
    UCL = "COLOR_LOGIC_UCL"
    FOUR_ZERO = "COLOR_LOGIC_4_0"
    TWO_FIVE = "COLOR_LOGIC_2_5"
    SAM = "COLOR_LOGIC_SAM"
    PENTAIR_COLOR = "CL_P_COLOR"
    ZODIAC_COLOR = "CL_Z_COLOR"

    def __str__(self) -> str:
        return ColorLogicLightType[self.name].value


class CSADType(StrEnum, PrettyEnum):
    ACID = "ACID"
    CO2 = "CO2"


# Chemistry Sense and Dispense
class CSADStatus(IntEnum, PrettyEnum):
    NOT_DISPENSING = 0
    DISPENSING = 1


class CSADMode(IntEnum, PrettyEnum):
    OFF = 0
    AUTO = 1
    FORCE_ON = 2
    MONITORING = 3
    DISPENSING_OFF = 4


# Filters
class FilterState(IntEnum, PrettyEnum):
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


class FilterType(StrEnum, PrettyEnum):
    VARIABLE_SPEED = "FMT_VARIABLE_SPEED_PUMP"
    DUAL_SPEED = "FMT_DUAL_SPEED"
    SINGLE_SPEED = "FMT_SINGLE_SPEED"


class FilterValvePosition(IntEnum, PrettyEnum):
    POOL_ONLY = 1
    SPA_ONLY = 2
    SPILLOVER = 3
    LOW_PRIO_HEAT = 4
    HIGH_PRIO_HEAT = 5


class FilterWhyOn(IntEnum, PrettyEnum):
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
class HeaterState(IntEnum, PrettyEnum):
    OFF = 0
    ON = 1
    PAUSE = 2


class HeaterType(StrEnum, PrettyEnum):
    GAS = "HTR_GAS"
    HEAT_PUMP = "HTR_HEAT_PUMP"
    SOLAR = "HTR_SOLAR"
    ELECTRIC = "HTR_ELECTRIC"
    GEOTHERMAL = "HTR_GEOTHERMAL"
    SMART = "HTR_SMART"


class HeaterMode(IntEnum, PrettyEnum):
    HEAT = 0
    COOL = 1
    AUTO = 2


# Pumps
class PumpState(IntEnum, PrettyEnum):
    OFF = 0
    ON = 1


class PumpType(StrEnum, PrettyEnum):
    SINGLE_SPEED = "PMP_SINGLE_SPEED"
    DUAL_SPEED = "PMP_DUAL_SPEED"
    VARIABLE_SPEED = "PMP_VARIABLE_SPEED_PUMP"


class PumpFunction(StrEnum, PrettyEnum):
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
class RelayFunction(StrEnum, PrettyEnum):
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


class RelayState(IntEnum, PrettyEnum):
    OFF = 0
    ON = 1


class RelayType(StrEnum, PrettyEnum):
    VALVE_ACTUATOR = "RLY_VALVE_ACTUATOR"
    HIGH_VOLTAGE = "RLY_HIGH_VOLTAGE_RELAY"
    LOW_VOLTAGE = "RLY_LOW_VOLTAGE_RELAY"


class RelayWhyOn(IntEnum, PrettyEnum):
    OFF = 0
    ON = 1
    FREEZE_PROTECT = 2
    WAITING_FOR_INTERLOCK = 3
    PAUSED = 4
    WAITING_FOR_FILTER = 5


# Sensors
class SensorType(StrEnum, PrettyEnum):
    AIR_TEMP = "SENSOR_AIR_TEMP"
    SOLAR_TEMP = "SENSOR_SOLAR_TEMP"
    WATER_TEMP = "SENSOR_WATER_TEMP"
    FLOW = "SENSOR_FLOW"
    ORP = "SENSOR_ORP"
    EXT_INPUT = "SENSOR_EXT_INPUT"


class SensorUnits(StrEnum, PrettyEnum):
    FAHRENHEIT = "UNITS_FAHRENHEIT"
    CELSIUS = "UNITS_CELSIUS"
    PPM = "UNITS_PPM"
    GRAMS_PER_LITER = "UNITS_GRAMS_PER_LITER"
    MILLIVOLTS = "UNITS_MILLIVOLTS"
    NO_UNITS = "UNITS_NO_UNITS"
    ACTIVE_INACTIVE = "UNITS_ACTIVE_INACTIVE"


# Valve Actuators
class ValveActuatorState(IntEnum, PrettyEnum):
    OFF = 0
    ON = 1
