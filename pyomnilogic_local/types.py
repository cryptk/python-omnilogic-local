from .util import PrettyEnum


class BackyardState(str, PrettyEnum):
    OFF = 0
    ON = 1
    SERVICE_MODE = 2
    CONFIG_MODE = 3
    TIMED_SERVICE_MODE = 4


class BodyOfWaterStatus(str, PrettyEnum):
    NO_FLOW = 0
    FLOW = 1


# Chlorinator status is a bitmask that we still need to figure out
# class ChlorinatorStatus(str,Enum):
#     pass
class ChlorinatorOperatingMode(str, PrettyEnum):
    TIMED = 1
    ORP = 2


class ColorLogicSpeed(str, PrettyEnum):
    ONE_SIXTEENTH = 0
    ONE_EIGHTH = 1
    ONE_QUARTER = 2
    ONE_HALF = 3
    ONE_TIMES = 4
    TWO_TIMES = 5
    FOUR_TIMES = 6
    EIGHT_TIMES = 7
    SIXTEEN_TIMES = 8


class ColorLogicBrightness(str, PrettyEnum):
    TWENTY_PERCENT = 0
    FOURTY_PERCENT = 1
    SIXTY_PERCENT = 2
    EIGHTY_PERCENT = 3
    ONE_HUNDRED_PERCENT = 4


class ColorLogicShow(str, PrettyEnum):
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
    #### THESE SHOW IN THE APP AFTER SETTING, BUT MAY NOT MATCH ALL LIGHTS
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


class ColorLogicPowerStates(str, PrettyEnum):
    OFF = 0
    POWERING_OFF = 1
    CHANGING_SHOW = 3
    FIFTEEN_SECONDS_WHITE = 4
    ACTIVE = 6
    COOLDOWN = 7


class CSADStatus(str, PrettyEnum):
    NOT_DISPENSING = 0
    DISPENSING = 1


class CSADMode(str, PrettyEnum):
    OFF = 0
    AUTO = 1
    FORCE_ON = 2
    MONITORING = 3
    DISPENSING_OFF = 4


class FilterState(str, PrettyEnum):
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


class FilterValvePosition(str, PrettyEnum):
    POOL_ONLY = 1
    SPA_ONLY = 2
    SPILLOVER = 3
    LOW_PRIO_HEAT = 4
    HIGH_PRIO_HEAT = 5


class FilterWhyOn(str, PrettyEnum):
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


class HeaterStatus(str, PrettyEnum):
    OFF = 0
    ON = 1
    PAUSE = 2


class MessageType(PrettyEnum):
    XML_ACK = 0000
    REQUEST_CONFIGURATION = 1
    SET_FILTER_SPEED = 9
    REQUEST_LOG_CONFIG = 31
    SET_HEATER_ENABLED = 147
    SET_EQUIPMENT = 164
    CREATE_SCHEDULE = 230
    DELETE_SCHEDULE = 231
    GET_TELEMETRY = 300
    GET_ALARM_LIST = 304
    SET_STANDALONE_LIGHT_SHOW = 308
    GET_FILTER_DIAGNOSTIC_INFO = 386
    HANDSHAKE = 1000
    ACK = 1002
    MSP_TELEMETRY_UPDATE = 1004
    MSP_CONFIGURATIONUPDATE = 1003
    MSP_ALARM_LIST = 1304
    MSP_LEADMESSAGE = 1998
    MSP_BLOCKMESSAGE = 1999


class PumpStatus(str, PrettyEnum):
    OFF = 0
    ON = 0


class RelayStatus(str, PrettyEnum):
    OFF = 0
    ON = 1


class ValveActuatorStatus(str, PrettyEnum):
    OFF = 0
    ON = 1
