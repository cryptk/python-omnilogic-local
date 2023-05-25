from __future__ import annotations

from typing import cast

from pydantic import BaseModel, Field
from xmltodict import parse as xml_parse

from ..types import (
    BackyardState,
    ChlorinatorOperatingMode,
    ColorLogicBrightness,
    ColorLogicPowerStates,
    ColorLogicShow,
    ColorLogicSpeed,
    FilterState,
    FilterValvePosition,
    FilterWhyOn,
    HeaterStatus,
    PumpStatus,
    RelayStatus,
    ValveActuatorStatus,
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
    omni_type = "Backyard"
    system_id: int = Field(alias="@systemId")
    status_version: int = Field(alias="@statusVersion")
    air_temp: int = Field(alias="@airTemp")
    state: BackyardState = Field(alias="@state")
    config_checksum: int = Field(alias="@ConfigChksum")
    msp_version: str = Field(alias="@mspVersion")


class TelemetryBOW(BaseModel):
    omni_type = "BodyOfWater"
    system_id: int = Field(alias="@systemId")
    water_temp: int = Field(alias="@waterTemp")
    flow: int = Field(alias="@flow")


class TelemetryChlorinator(BaseModel):
    omni_type = "Chlorinator"
    system_id: int = Field(alias="@systemId")
    status: int = Field(alias="@status")
    instant_salt_level: int = Field(alias="@instantSaltLevel")
    avg_salt_level: int = Field(alias="@avgSaltLevel")
    chlr_alert: int = Field(alias="@chlrAlert")
    chlr_error: int = Field(alias="@chlrError")
    sc_mode: int = Field(alias="@scMode")
    operating_state: int = Field(alias="@operatingState")
    timed_percent: int = Field(alias="@Timed-Percent")
    operating_mode: ChlorinatorOperatingMode = Field(alias="@operatingMode")
    enable: bool


class TelemetryColorLogicLight(BaseModel):
    omni_type = "ColorLogic-Light"
    system_id: int = Field(alias="@systemId")
    state: ColorLogicPowerStates = Field(alias="@lightState")
    show: ColorLogicShow = Field(alias="@currentShow")
    speed: ColorLogicSpeed = Field(alias="@speed")
    brightness: ColorLogicBrightness = Field(alias="@brightness")
    special_effect: int = Field(alias="@specialEffect")


class TelemetryFilter(BaseModel):
    omni_type = "Filter"
    system_id: int = Field(alias="@systemId")
    state: FilterState = Field(alias="@filterState")
    speed: int = Field(alias="@filterSpeed")
    valve_position: FilterValvePosition = Field(alias="@valvePosition")
    why_on: FilterWhyOn = Field(alias="@whyFilterIsOn")
    reported_speed: int = Field(alias="@reportedFilterSpeed")
    power: int = Field(alias="@power")
    last_speed: int = Field(alias="@lastSpeed")


class TelemetryGroup(BaseModel):
    omni_type = "Group"
    system_id: int = Field(alias="@systemId")
    state: int = Field(alias="@groupState")


class TelemetryHeater(BaseModel):
    omni_type = "Heater"
    system_id: int = Field(alias="@systemId")
    state: HeaterStatus = Field(alias="@heaterState")
    temp: int = Field(alias="@temp")
    enabled: bool = Field(alias="@enable")
    priority: int = Field(alias="@priority")
    maintain_for: int = Field(alias="@maintainFor")


class TelemetryPump(BaseModel):
    omni_type = "Pump"
    system_id: int = Field(alias="@systemId")
    state: PumpStatus = Field(alias="@pumpState")
    speed: int = Field(alias="@pummpSpeed")
    last_speed: int = Field(alias="@lastSpeed")
    why_on: int = Field(alias="@whyOn")


class TelemetryRelay(BaseModel):
    omni_type = "Relay"
    system_id: int = Field(alias="@systemId")
    state: RelayStatus = Field(alias="@relayState")
    why_on: int = Field(alias="@whyOn")


class TelemetryValveActuator(BaseModel):
    omni_type = "ValveActuator"
    system_id: int = Field(alias="@systemId")
    state: ValveActuatorStatus = Field(alias="@valveActuatorState")
    why_on: int = Field(alias="@whyOn")


class TelemetryVirtualHeater(BaseModel):
    omni_type = "VirtualHeater"
    system_id: int = Field(alias="@systemId")
    current_set_point: int = Field(alias="@Current-Set-Point")
    enabled: bool = Field(alias="@enable")
    solar_set_point: int = Field(alias="@SolarSetPoint")
    mode: int = Field(alias="@Mode")
    silent_mode: int = Field(alias="@SilentMode")
    why_on: int = Field(alias="@whyHeaterIsOn")


TTelemetry = (
    TelemetryBackyard
    | TelemetryBOW
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
    backyard: list[TelemetryBackyard] = Field(alias="Backyard")
    bow: list[TelemetryBOW] = Field(alias="BodyOfWater")
    chlorinator: list[TelemetryChlorinator] | None = Field(alias="Chlorinator")
    colorlogic_light: list[TelemetryColorLogicLight] | None = Field(alias="ColorLogic-Light")
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
        data = xml_parse(
            xml,
            # Some things will be lists or not depending on if a pool has more than one of that piece of equipment.  Here we are coercing
            # everything into lists to make the parsing more consistent. This does mean that some things that would normally never be lists
            # will become lists (I.E.: Backyard, VirtualHeater), but the upside is that we need far less conditional code to deal with the
            # "maybe list maybe not" devices.
            force_list=(
                "Backyard",
                "BodyOfWater",
                "Chlorinator",
                "ColorLogic-Light",
                "Filter",
                "Group",
                "Heater",
                "Pump",
                "Relay",
                "ValveActuator",
                "VirtualHeater",
            ),
        )
        return Telemetry.parse_obj(data["STATUS"])

    def get_telem_by_systemid(self, system_id: int) -> TTelemetry | None:
        for field_name, value in self:
            if field_name == "version" or value is None:
                continue
            for model in value:
                cast_model = cast(TTelemetry, model)
                if cast_model.system_id == system_id:
                    return cast_model
        return None
