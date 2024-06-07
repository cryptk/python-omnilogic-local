from __future__ import annotations

from typing import Any, SupportsInt, TypeAlias, TypeVar, cast, overload

from pydantic import BaseModel, Field, ValidationError
from xmltodict import parse as xml_parse

from ..exceptions import OmniParsingException
from ..types import (
    BackyardState,
    ChlorinatorOperatingMode,
    ColorLogicBrightness,
    ColorLogicPowerState,
    ColorLogicShow,
    ColorLogicSpeed,
    CSADMode,
    FilterState,
    FilterValvePosition,
    FilterWhyOn,
    HeaterMode,
    HeaterState,
    OmniType,
    PumpState,
    RelayState,
    ValveActuatorState,
)

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
    omni_type: OmniType = OmniType.BACKYARD
    system_id: int = Field(alias="@systemId")
    status_version: int = Field(alias="@statusVersion")
    air_temp: int = Field(alias="@airTemp")
    state: BackyardState | int = Field(alias="@state")
    # The below two fields are only available for telemetry with a status_version >= 11
    config_checksum: int | None = Field(alias="@ConfigChksum")
    msp_version: str | None = Field(alias="@mspVersion")


class TelemetryBoW(BaseModel):
    omni_type: OmniType = OmniType.BOW
    system_id: int = Field(alias="@systemId")
    water_temp: int = Field(alias="@waterTemp")
    flow: int = Field(alias="@flow")


class TelemetryChlorinator(BaseModel):
    omni_type: OmniType = OmniType.CHLORINATOR
    system_id: int = Field(alias="@systemId")
    status_raw: int = Field(alias="@status")
    instant_salt_level: int = Field(alias="@instantSaltLevel")
    avg_salt_level: int = Field(alias="@avgSaltLevel")
    chlr_alert: int = Field(alias="@chlrAlert")
    chlr_error: int = Field(alias="@chlrError")
    sc_mode: int = Field(alias="@scMode")
    operating_state: int = Field(alias="@operatingState")
    timed_percent: int | None = Field(alias="@Timed-Percent")
    operating_mode: ChlorinatorOperatingMode | int = Field(alias="@operatingMode")
    enable: bool = Field(alias="@enable")

    # Still need to do a bit more work to determine if a chlorinator is actively chlorinating
    # @property
    # def active(self) -> bool:
    #     return self.status_raw & 4 == 4 # Check if bit 4 is set, which means the chlorinator is currently chlorinating


class TelemetryCSAD(BaseModel):
    omni_type: OmniType = OmniType.CSAD
    system_id: int = Field(alias="@systemId")
    status_raw: int = Field(alias="@status")
    ph: float = Field(alias="@ph")
    orp: int = Field(alias="@orp")
    mode: CSADMode | int = Field(alias="@mode")


class TelemetryColorLogicLight(BaseModel):
    omni_type: OmniType = OmniType.CL_LIGHT
    system_id: int = Field(alias="@systemId")
    state: ColorLogicPowerState | int = Field(alias="@lightState")
    show: ColorLogicShow | int = Field(alias="@currentShow")
    speed: ColorLogicSpeed | int = Field(alias="@speed")
    brightness: ColorLogicBrightness | int = Field(alias="@brightness")
    special_effect: int = Field(alias="@specialEffect")


class TelemetryFilter(BaseModel):
    omni_type: OmniType = OmniType.FILTER
    system_id: int = Field(alias="@systemId")
    state: FilterState | int = Field(alias="@filterState")
    speed: int = Field(alias="@filterSpeed")
    valve_position: FilterValvePosition | int = Field(alias="@valvePosition")
    why_on: FilterWhyOn | int = Field(alias="@whyFilterIsOn")
    reported_speed: int = Field(alias="@reportedFilterSpeed")
    power: int = Field(alias="@power")
    last_speed: int = Field(alias="@lastSpeed")


class TelemetryGroup(BaseModel):
    omni_type: OmniType = OmniType.GROUP
    system_id: int = Field(alias="@systemId")
    state: int = Field(alias="@groupState")


class TelemetryHeater(BaseModel):
    omni_type: OmniType = OmniType.HEATER
    system_id: int = Field(alias="@systemId")
    state: HeaterState | int = Field(alias="@heaterState")
    temp: int = Field(alias="@temp")
    enabled: bool = Field(alias="@enable")
    priority: int = Field(alias="@priority")
    maintain_for: int = Field(alias="@maintainFor")


class TelemetryPump(BaseModel):
    omni_type: OmniType = OmniType.PUMP
    system_id: int = Field(alias="@systemId")
    state: PumpState | int = Field(alias="@pumpState")
    speed: int = Field(alias="@pumpSpeed")
    last_speed: int = Field(alias="@lastSpeed")
    why_on: int = Field(alias="@whyOn")


class TelemetryRelay(BaseModel):
    omni_type: OmniType = OmniType.RELAY
    system_id: int = Field(alias="@systemId")
    state: RelayState | int = Field(alias="@relayState")
    why_on: int = Field(alias="@whyOn")


class TelemetryValveActuator(BaseModel):
    omni_type: OmniType = OmniType.VALVE_ACTUATOR
    system_id: int = Field(alias="@systemId")
    state: ValveActuatorState | int = Field(alias="@valveActuatorState")
    why_on: int = Field(alias="@whyOn")


class TelemetryVirtualHeater(BaseModel):
    omni_type: OmniType = OmniType.VIRT_HEATER
    system_id: int = Field(alias="@systemId")
    current_set_point: int = Field(alias="@Current-Set-Point")
    enabled: bool = Field(alias="@enable")
    solar_set_point: int = Field(alias="@SolarSetPoint")
    mode: HeaterMode | int = Field(alias="@Mode")
    silent_mode: int = Field(alias="@SilentMode")
    why_on: int = Field(alias="@whyHeaterIsOn")


TelemetryType: TypeAlias = (
    TelemetryBackyard
    | TelemetryBoW
    | TelemetryChlorinator
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
    version: str = Field(alias="@version")
    backyard: TelemetryBackyard = Field(alias="Backyard")
    bow: list[TelemetryBoW] = Field(alias="BodyOfWater")
    chlorinator: list[TelemetryChlorinator] | None = Field(alias="Chlorinator")
    colorlogic_light: list[TelemetryColorLogicLight] | None = Field(alias="ColorLogic-Light")
    csad: list[TelemetryCSAD] | None = Field(alias="CSAD")
    filter: list[TelemetryFilter] | None = Field(alias="Filter")
    group: list[TelemetryGroup] | None = Field(alias="Group")
    heater: list[TelemetryHeater] | None = Field(alias="Heater")
    pump: list[TelemetryPump] | None = Field(alias="Pump")
    relay: list[TelemetryRelay] | None = Field(alias="Relay")
    valve_actuator: list[TelemetryValveActuator] | None = Field(alias="ValveActuator")
    virtual_heater: list[TelemetryVirtualHeater] | None = Field(alias="VirtualHeater")

    class Config:
        orm_mode = True

    @staticmethod
    def load_xml(xml: str) -> Telemetry:
        TypeVar("KT")
        TypeVar("VT", SupportsInt, Any)

        @overload
        def xml_postprocessor(path: Any, key: Any, value: SupportsInt) -> tuple[Any, SupportsInt]:
            ...

        @overload
        def xml_postprocessor(path: Any, key: Any, value: Any) -> tuple[Any, Any]:
            ...

        def xml_postprocessor(path: Any, key: Any, value: SupportsInt | Any) -> tuple[Any, SupportsInt | Any]:
            """Post process XML to attempt to convert values to int.

            Pydantic can coerce values natively, but the Omni API returns values as strings of numbers (I.E. "2", "5", etc) and we need them
            coerced into int enums.  Pydantic only seems to be able to handle one coercion, so it could coerce an int into an Enum, but it
            cannot coerce a string into an int and then into the Enum. We help it out a little bit here by pre-emptively coercing any
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
            return Telemetry.parse_obj(data["STATUS"])
        except ValidationError as exc:
            raise OmniParsingException(f"Failed to parse Telemetry: {exc}") from exc

    def get_telem_by_systemid(self, system_id: int) -> TelemetryType | None:
        for field_name, value in self:
            if field_name == "version" or value is None:
                continue
            if isinstance(value, list):
                for model in value:
                    cast_model = cast(TelemetryType, model)
                    if cast_model.system_id == system_id:
                        return cast_model
            else:
                cast_model = cast(TelemetryType, value)
                if cast_model.system_id == system_id:
                    return cast_model
        return None
