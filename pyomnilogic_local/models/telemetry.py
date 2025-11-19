# ruff: noqa: TC001  # pydantic relies on the omnitypes imports at runtime
from __future__ import annotations

from typing import Any, SupportsInt, cast, overload

from pydantic import BaseModel, ConfigDict, Field, ValidationError, computed_field
from xmltodict import parse as xml_parse

from pyomnilogic_local.omnitypes import (
    BackyardState,
    ChlorinatorAlert,
    ChlorinatorError,
    ChlorinatorOperatingMode,
    ChlorinatorStatus,
    ColorLogicBrightness,
    ColorLogicLightType,
    ColorLogicPowerState,
    ColorLogicShow25,
    ColorLogicShow40,
    ColorLogicShowUCL,
    ColorLogicShowUCLV2,
    ColorLogicSpeed,
    CSADMode,
    CSADStatus,
    FilterState,
    FilterValvePosition,
    FilterWhyOn,
    GroupState,
    HeaterMode,
    HeaterState,
    LightShows,
    OmniType,
    PentairShow,
    PumpState,
    RelayState,
    RelayWhyOn,
    ValveActuatorState,
    ZodiacShow,
)

from .exceptions import OmniParsingError

# Example telemetry XML data:
#
# <?xml version="1.0" encoding="UTF-8" ?>
# <STATUS version="1.11">
#     <Backyard systemId="0" statusVersion="11" airTemp="77" state="1" ConfigChksum="2211028" mspVersion="R0408000" />
#     <BodyOfWater systemId="7" waterTemp="-1" flow="255" />
#     <Filter systemId="8" filterState="0" filterSpeed="0" valvePosition="1" whyFilterIsOn="0" fpOverride="0" reportedFilterSpeed="0" power="0" lastSpeed="50" /> # noqa: E501
#     <ValveActuator systemId="9" valveActuatorState="0" whyOn="0" />
#     <ColorLogic-Light systemId="10" lightState="6" currentShow="0" speed="4" brightness="4" specialEffect="0" />
#     <ValveActuator systemId="13" valveActuatorState="0" whyOn="0" />
#     <ValveActuator systemId="14" valveActuatorState="0" whyOn="0" />
#     <VirtualHeater systemId="18" Current-Set-Point="85" enable="1" SolarSetPoint="90" Mode="0" SilentMode="0" whyHeaterIsOn="1" />
#     <Heater systemId="19" heaterState="0" temp="74" enable="1" priority="254" maintainFor="24" />
#     <Group systemId="21" groupState="0" />
# </STATUS>


class TelemetryBackyard(BaseModel):
    """Real-time telemetry for the backyard/controller system.

    This is the top-level telemetry object containing system-wide state information.
    Always present in telemetry responses.

    Fields:
        air_temp: Air temperature in Fahrenheit, None if sensor unavailable
        state: Current operational state (ON, OFF, SERVICE_MODE, etc.)
        config_checksum: Configuration version identifier for detecting changes
        msp_version: Controller firmware version (available in status_version >= 11)
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.BACKYARD
    system_id: int = Field(alias="@systemId")
    status_version: int = Field(alias="@statusVersion")
    air_temp: int | None = Field(alias="@airTemp")
    state: BackyardState = Field(alias="@state")
    # The below two fields are only available for telemetry with a status_version >= 11
    config_checksum: int = Field(alias="@ConfigChksum", default=0)
    msp_version: str | None = Field(alias="@mspVersion", default=None)


class TelemetryBoW(BaseModel):
    """Real-time telemetry for a body of water (pool or spa).

    Contains current water conditions and flow status.

    Fields:
        water_temp: Water temperature in Fahrenheit, -1 if sensor unavailable
        flow: Flow sensor value, 255 or 1 typically indicate flow detected, 0 for no flow
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.BOW
    system_id: int = Field(alias="@systemId")
    water_temp: int = Field(alias="@waterTemp")
    flow: int = Field(alias="@flow")


class TelemetryChlorinator(BaseModel):
    """Real-time telemetry for salt chlorinator systems.

    Includes salt levels, operational status, alerts, and errors. Use computed
    properties (status, alerts, errors) for decoded bitmask values.

    Fields:
        instant_salt_level: Current salt reading in PPM
        avg_salt_level: Average salt level in PPM over time
        status_raw: Bitmask of operational status flags (use .status property for decoded properties)
        chlr_alert_raw: Bitmask of alert conditions (use .alerts property for decoded properties)
        chlr_error_raw: Bitmask of error conditions (use .errors property for decoded properties)
        timed_percent: Chlorination output percentage in timed mode (0-100), None if not applicable
        operating_mode: DISABLED, TIMED, ORP_AUTO, or ORP_TIMED_RW
        enable: Whether chlorinator is enabled for operation
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.CHLORINATOR
    system_id: int = Field(alias="@systemId")
    status_raw: int = Field(alias="@status")
    instant_salt_level: int = Field(alias="@instantSaltLevel")
    avg_salt_level: int = Field(alias="@avgSaltLevel")
    chlr_alert_raw: int = Field(alias="@chlrAlert")
    chlr_error_raw: int = Field(alias="@chlrError")
    sc_mode: int = Field(alias="@scMode")
    operating_state: int = Field(alias="@operatingState")
    timed_percent: int | None = Field(alias="@Timed-Percent", default=None)
    operating_mode: ChlorinatorOperatingMode = Field(alias="@operatingMode")
    enable: bool = Field(alias="@enable")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> list[str]:
        """Decode status bitmask into a list of active status flag names.

        Returns:
            List of active ChlorinatorStatus flag names as strings

        Example:
            >>> chlorinator.status
            ['ALERT_PRESENT', 'GENERATING', 'K1_ACTIVE']
        """
        return [flag.name for flag in ChlorinatorStatus if self.status_raw & flag.value and flag.name is not None]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def alerts(self) -> list[str]:
        """Decode chlrAlert bitmask into a list of active alert flag names.

        Returns:
            List of active ChlorinatorAlert flag names as strings

        Note:
            When both CELL_TEMP_LOW and CELL_TEMP_SCALEBACK are set (bits 5:4 = 11),
            they are replaced with "CELL_TEMP_HIGH" for semantic correctness.

        Example:
            >>> chlorinator.alerts
            ['SALT_LOW', 'HIGH_CURRENT']
        """
        flags = ChlorinatorAlert(self.chlr_alert_raw)
        high_temp_bits = ChlorinatorAlert.CELL_TEMP_LOW | ChlorinatorAlert.CELL_TEMP_SCALEBACK
        cell_temp_high = False

        if flags & high_temp_bits == high_temp_bits:
            cell_temp_high = True
            flags = flags & ~high_temp_bits

        final_flags = [flag.name for flag in ChlorinatorAlert if flags & flag and flag.name is not None]
        if cell_temp_high:
            final_flags.append("CELL_TEMP_HIGH")

        return final_flags

    @computed_field  # type: ignore[prop-decorator]
    @property
    def errors(self) -> list[str]:
        """Decode chlrError bitmask into a list of active error flag names.

        Returns:
            List of active ChlorinatorError flag names as strings

        Note:
            When both CELL_ERROR_TYPE and CELL_ERROR_AUTH are set (bits 13:12 = 11),
            they are replaced with "CELL_COMM_LOSS" for semantic correctness.

        Example:
            >>> chlorinator.errors
            ['CURRENT_SENSOR_SHORT', 'VOLTAGE_SENSOR_OPEN']
        """
        flags = ChlorinatorError(self.chlr_error_raw)
        cell_comm_loss_bits = ChlorinatorError.CELL_ERROR_TYPE | ChlorinatorError.CELL_ERROR_AUTH
        cell_comm_loss = False

        if flags & cell_comm_loss_bits == cell_comm_loss_bits:
            cell_comm_loss = True
            flags = flags & ~cell_comm_loss_bits

        final_flags = [flag.name for flag in ChlorinatorError if flags & flag and flag.name is not None]
        if cell_comm_loss:
            final_flags.append("CELL_COMM_LOSS")

        return final_flags

    @computed_field  # type: ignore[prop-decorator]
    @property
    def active(self) -> bool:
        """Check if the chlorinator is actively generating chlorine.

        Returns:
            True if the GENERATING status flag is set, False otherwise
        """
        return ChlorinatorStatus.GENERATING.value & self.status_raw == ChlorinatorStatus.GENERATING.value


class TelemetryCSAD(BaseModel):
    """Real-time telemetry for Chemistry Sense and Dispense systems.

    Provides current water chemistry readings and dispensing status.

    Fields:
        ph: Current pH level reading (typically 0.0-14.0)
        orp: Oxidation-Reduction Potential in millivolts
        mode: Current operation mode (OFF, AUTO, FORCE_ON, MONITORING, DISPENSING_OFF)
        status: Dispensing status (NOT_DISPENSING, DISPENSING)
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.CSAD
    system_id: int = Field(alias="@systemId")
    status: CSADStatus = Field(alias="@status")
    ph: float = Field(alias="@ph")
    orp: int = Field(alias="@orp")
    mode: CSADMode = Field(alias="@mode")


class TelemetryColorLogicLight(BaseModel):
    """Real-time telemetry for ColorLogic LED lighting systems.

    Tracks power state, active show, speed, and brightness settings. Light cannot
    accept commands during transitional states (CHANGING_SHOW, POWERING_OFF, COOLDOWN).

    Not all fields are applicable to all light models.

    Fields:
        state: Power/operational state (OFF, ACTIVE, transitional states)
        show: Currently active light show (type depends on light model)
        speed: Animation speed (ONE_SIXTEENTH to SIXTEEN_TIMES)
        brightness: Light brightness level (TWENTY_PERCENT to ONE_HUNDRED_PERCENT)
        special_effect: Special effect identifier (usage varies by model)
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.CL_LIGHT
    system_id: int = Field(alias="@systemId")
    state: ColorLogicPowerState = Field(alias="@lightState")
    show: LightShows = Field(alias="@currentShow")
    speed: ColorLogicSpeed = Field(alias="@speed")
    brightness: ColorLogicBrightness = Field(alias="@brightness")
    special_effect: int = Field(alias="@specialEffect")

    def show_name(
        self, model: ColorLogicLightType, v2: bool
    ) -> ColorLogicShow25 | ColorLogicShow40 | ColorLogicShowUCL | ColorLogicShowUCLV2 | PentairShow | ZodiacShow:
        """Get the current light show depending on the light type.

        Returns:
            ColorLogicShowUCL enum member corresponding to the current show,
            or None if the show value is invalid.
        """
        match model:
            case ColorLogicLightType.TWO_FIVE:
                return ColorLogicShow25(self.show)
            case ColorLogicLightType.FOUR_ZERO:
                return ColorLogicShow40(self.show)
            case ColorLogicLightType.UCL:
                if v2:
                    return ColorLogicShowUCLV2(self.show)
                return ColorLogicShowUCL(self.show)
            case ColorLogicLightType.PENTAIR_COLOR:
                return PentairShow(self.show)
            case ColorLogicLightType.ZODIAC_COLOR:
                return ZodiacShow(self.show)
        msg = f"Unknown ColorLogicLightType {model} for show name parsing"
        raise OmniParsingError(msg)


class TelemetryFilter(BaseModel):
    """Real-time telemetry for filter pump systems.

    Includes operational state, speed settings, and valve position. Filter cannot
    accept commands during transitional states (PRIMING, COOLDOWN, etc.).

    Fields:
        state: Current operational state (OFF, ON, transitional states)
        speed: Current speed setting (percentage 0-100)
        valve_position: Current valve position for multi-port systems
        why_on: Reason filter is running (MANUAL_ON, TIMED_EVENT, FREEZE_PROTECT, etc.)
        reported_speed: Actual reported speed from variable speed pump (percentage 0-100)
        power: Current power consumption (watts)
        last_speed: Previous speed setting before state change
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.FILTER
    system_id: int = Field(alias="@systemId")
    state: FilterState = Field(alias="@filterState")
    speed: int = Field(alias="@filterSpeed")
    valve_position: FilterValvePosition = Field(alias="@valvePosition")
    why_on: FilterWhyOn = Field(alias="@whyFilterIsOn")
    reported_speed: int = Field(alias="@reportedFilterSpeed")
    power: int = Field(alias="@power")
    last_speed: int = Field(alias="@lastSpeed")


class TelemetryGroup(BaseModel):
    """Real-time telemetry for equipment groups.

    Groups allow controlling multiple pieces of equipment together as a single unit.

    Fields:
        state: Current group state (OFF or ON)
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.GROUP
    system_id: int = Field(alias="@systemId")
    state: GroupState = Field(alias="@groupState")


class TelemetryHeater(BaseModel):
    """Real-time telemetry for physical heater equipment.

    Represents actual heater hardware (gas, heat pump, solar, etc.) controlled
    by a VirtualHeater. See TelemetryVirtualHeater for set points and modes.

    Fields:
        state: Current heater state (OFF, ON, PAUSE)
        temp: Current water temperature reading in Fahrenheit
        enabled: Whether heater is enabled for operation
        priority: Heater priority for sequencing
        maintain_for: Hours to maintain temperature after reaching set point
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.HEATER
    system_id: int = Field(alias="@systemId")
    state: HeaterState = Field(alias="@heaterState")
    temp: int = Field(alias="@temp")
    enabled: bool = Field(alias="@enable")
    priority: int = Field(alias="@priority")
    maintain_for: int = Field(alias="@maintainFor")


class TelemetryPump(BaseModel):
    """Real-time telemetry for auxiliary pump equipment.

    Auxiliary pumps are separate from filter pumps and used for water features,
    cleaners, etc. Pump cannot accept commands during transitional states.

    Fields:
        state: Current pump state (OFF, ON, FREEZE_PROTECT)
        speed: Current speed setting (percentage 0-100 or RPM depending on type)
        last_speed: Previous speed setting before state change
        why_on: Reason pump is running (usage similar to FilterWhyOn)
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.PUMP
    system_id: int = Field(alias="@systemId")
    state: PumpState = Field(alias="@pumpState")
    speed: int = Field(alias="@pumpSpeed")
    last_speed: int = Field(alias="@lastSpeed")
    why_on: int = Field(alias="@whyOn")


class TelemetryRelay(BaseModel):
    """Real-time telemetry for relay-controlled equipment.

    Relays provide simple on/off control for lights, water features, and other
    accessories not requiring variable speed control.

    Fields:
        state: Current relay state (OFF or ON)
        why_on: Reason relay is on (MANUAL_ON, SCHEDULE_ON, GROUP_ON, FREEZE_PROTECT, etc.)
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.RELAY
    system_id: int = Field(alias="@systemId")
    state: RelayState = Field(alias="@relayState")
    why_on: RelayWhyOn = Field(alias="@whyOn")


class TelemetryValveActuator(BaseModel):
    """Real-time telemetry for valve actuator equipment.

    Valve actuators control motorized valves for directing water flow. Functionally
    similar to relays with on/off states.

    Fields:
        state: Current valve state (OFF or ON)
        why_on: Reason valve is active (uses RelayWhyOn enum values)
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.VALVE_ACTUATOR
    system_id: int = Field(alias="@systemId")
    state: ValveActuatorState = Field(alias="@valveActuatorState")
    # Valve actuators are actually relays, so we can reuse the RelayWhyOn enum here
    why_on: RelayWhyOn = Field(alias="@whyOn")


class TelemetryVirtualHeater(BaseModel):
    """Real-time telemetry for virtual heater controller.

    Virtual heater acts as the control logic for one or more physical heaters,
    managing set points, modes, and sequencing. Each body of water has one virtual heater.

    Fields:
        current_set_point: Active temperature target in Fahrenheit
        enabled: Whether heating/cooling is enabled
        solar_set_point: Solar heater set point in Fahrenheit
        mode: Operating mode (HEAT, COOL, or AUTO)
        silent_mode: Heat pump quiet mode setting
        why_on: Reason heater is active (usage varies)
    """

    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.VIRT_HEATER
    system_id: int = Field(alias="@systemId")
    current_set_point: int = Field(alias="@Current-Set-Point")
    enabled: bool = Field(alias="@enable")
    solar_set_point: int = Field(alias="@SolarSetPoint")
    mode: HeaterMode = Field(alias="@Mode")
    silent_mode: int = Field(alias="@SilentMode")
    why_on: int = Field(alias="@whyHeaterIsOn")


type TelemetryType = (
    TelemetryBackyard
    | TelemetryBoW
    | TelemetryChlorinator
    | TelemetryCSAD
    | TelemetryColorLogicLight
    | TelemetryFilter
    | TelemetryGroup
    | TelemetryHeater
    | TelemetryPump
    | TelemetryRelay
    | TelemetryValveActuator
    | TelemetryVirtualHeater
)


class Telemetry(BaseModel):
    """Complete real-time telemetry snapshot from the OmniLogic controller.

    Contains the current state of all equipment in the system. Telemetry is requested
    via async_get_telemetry() and should be refreshed periodically to get current values.

    All equipment collections except backyard and bow are optional and will be None
    if no equipment of that type exists in the system.

    Fields:
        version: Telemetry format version from controller
        backyard: System-wide state (always present)
        bow: Bodies of water telemetry (always present, one or more)
        chlorinator: Salt chlorinator telemetry (optional)
        colorlogic_light: LED light telemetry (optional)
        csad: Chemistry controller telemetry (optional)
        filter: Filter pump telemetry (optional)
        group: Equipment group telemetry (optional)
        heater: Physical heater telemetry (optional)
        pump: Auxiliary pump telemetry (optional)
        relay: Relay-controlled equipment telemetry (optional)
        valve_actuator: Valve actuator telemetry (optional)
        virtual_heater: Heater controller telemetry (optional)
    """

    model_config = ConfigDict(from_attributes=True)

    version: str = Field(alias="@version")
    backyard: TelemetryBackyard = Field(alias="Backyard")
    bow: list[TelemetryBoW] = Field(alias="BodyOfWater")
    chlorinator: list[TelemetryChlorinator] | None = Field(alias="Chlorinator", default=None)
    colorlogic_light: list[TelemetryColorLogicLight] | None = Field(alias="ColorLogic-Light", default=None)
    csad: list[TelemetryCSAD] | None = Field(alias="CSAD", default=None)
    filter: list[TelemetryFilter] | None = Field(alias="Filter", default=None)
    group: list[TelemetryGroup] | None = Field(alias="Group", default=None)
    heater: list[TelemetryHeater] | None = Field(alias="Heater", default=None)
    pump: list[TelemetryPump] | None = Field(alias="Pump", default=None)
    relay: list[TelemetryRelay] | None = Field(alias="Relay", default=None)
    valve_actuator: list[TelemetryValveActuator] | None = Field(alias="ValveActuator", default=None)
    virtual_heater: list[TelemetryVirtualHeater] | None = Field(alias="VirtualHeater", default=None)

    @staticmethod
    def load_xml(xml: str) -> Telemetry:
        @overload
        def xml_postprocessor(path: Any, key: Any, value: SupportsInt) -> tuple[Any, SupportsInt]: ...
        @overload
        def xml_postprocessor(path: Any, key: Any, value: Any) -> tuple[Any, Any]: ...
        def xml_postprocessor(path: Any, key: Any, value: SupportsInt | Any) -> tuple[Any, SupportsInt | Any]:  # noqa: ARG001  # Unused argument is part of the xmltodict postprocessor signature
            """Post process XML to attempt to convert values to int.

            Pydantic can coerce values natively, but the Omni API returns values as strings of numbers (I.E. "2", "5", etc) and we need them
            coerced into int enums.  Pydantic only seems to be able to handle one coercion, so it could coerce an int into an Enum, but it
            cannot coerce a string into an int and then into the Enum. We help it out a little bit here by preemptively coercing any
            string ints into an int, then pydantic handles the int to enum coercion if necessary.
            """
            newvalue: SupportsInt | Any

            try:
                newvalue = int(value)
            except (ValueError, TypeError):
                newvalue = value

            return key, newvalue

        data = xml_parse(
            xml,
            postprocessor=xml_postprocessor,
            # Some things will be lists or not depending on if a pool has more than one of that piece of equipment.  Here we are coercing
            # everything into lists to make the parsing more consistent. This does mean that some things that would normally never be lists
            # will become lists (I.E.: Backyard, VirtualHeater), but the upside is that we need far less conditional code to deal with the
            # "maybe list maybe not" devices.
            force_list=(
                OmniType.BOW,
                OmniType.CHLORINATOR,
                OmniType.CSAD,
                OmniType.CL_LIGHT,
                OmniType.FILTER,
                OmniType.GROUP,
                OmniType.HEATER,
                OmniType.PUMP,
                OmniType.RELAY,
                OmniType.VALVE_ACTUATOR,
                OmniType.VIRT_HEATER,
            ),
        )
        try:
            return Telemetry.model_validate(data["STATUS"])
        except ValidationError as exc:
            msg = f"Failed to parse Telemetry: {exc}"
            raise OmniParsingError(msg) from exc

    def get_telem_by_systemid(self, system_id: int) -> TelemetryType | None:
        for field_name, value in self:
            if field_name == "version" or value is None:
                continue
            if isinstance(value, list):
                for model in value:
                    cast_model = cast("TelemetryType", model)
                    if cast_model.system_id == system_id:
                        return cast_model
            else:
                cast_model = cast("TelemetryType", value)
                if cast_model.system_id == system_id:
                    return cast_model
        return None
