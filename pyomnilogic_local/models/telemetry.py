from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from pydantic.utils import GetterDict

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
from .const import XML_NS

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


class TelemetryGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        # print(key)
        # foo = self._obj.find(f".//{key}", XML_NS).attrib
        # print(foo)
        try:
            if len(self._obj.findall(f".//{key}", XML_NS)) > 1:
                return [i.attrib for i in self._obj.findall(f".//{key}", XML_NS)]
            return self._obj.find(f".//{key}", XML_NS).attrib
        except AttributeError:
            return default


class TelemetryBackyard(BaseModel):
    system_id: int = Field(alias="systemId")
    status_version: int = Field(alias="statusVersion")
    air_temp: int = Field(alias="airTemp")
    state: BackyardState
    config_checksum: int = Field(alias="ConfigChksum")
    msp_version: str = Field(alias="mspVersion")


class TelemetryBOW(BaseModel):
    system_id: int = Field(alias="systemId")
    water_temp: int = Field(alias="waterTemp")
    flow: int


class TelemetryChlorinator(BaseModel):
    system_id: int = Field(alias="systemId")
    status: int
    instant_salt_level: int = Field(alias="instantSaltLevel")
    avg_salt_level: int = Field(alias="avgSaltLevel")
    chlr_alert: int = Field(alias="chlrAlert")
    chlr_error: int = Field(alias="chlrError")
    sc_mode: int = Field(alias="scMode")
    operating_state: int = Field(alias="operatingState")
    timed_percent: int = Field(alias="Timed-Percent")
    operating_mode: ChlorinatorOperatingMode = Field(alias="operatingMode")
    enable: bool


class TelemetryColorLogicLight(BaseModel):
    system_id: int = Field(alias="systemId")
    state: ColorLogicPowerStates = Field(alias="lightState")
    show: ColorLogicShow = Field(alias="currentShow")
    speed: ColorLogicSpeed = Field()
    brightness: ColorLogicBrightness
    special_effect: int = Field(alias="specialEffect")


class TelemetryFilter(BaseModel):
    system_id: int = Field(alias="systemId")
    state: FilterState = Field(alias="filterState")
    speed: int = Field(alias="filterSpeed")
    valve_position: FilterValvePosition = Field(alias="valvePosition")
    why_on: FilterWhyOn = Field(alias="whyFilterIsOn")
    reported_speed: int = Field(alias="reportedFilterSpeed")
    power: int
    last_speed: int = Field(alias="lastSpeed")


class TelemetryGroup(BaseModel):
    system_id: int = Field(alias="systemId")
    state: int = Field(alias="groupState")


class TelemetryHeater(BaseModel):
    system_id: int = Field(alias="systemId")
    state: HeaterStatus = Field(alias="heaterState")
    temp: int
    enabled: bool = Field(alias="enable")
    priority: int
    maintain_for: int = Field(alias="maintainFor")


class TelemetryPump(BaseModel):
    system_id: int = Field(alias="systemId")
    state: PumpStatus = Field(alias="pumpState")
    speed: int = Field(alias="pummpSpeed")
    last_speed: int = Field(alias="lastSpeed")
    why_on: int = Field(alias="whyOn")


class TelemetryRelay(BaseModel):
    system_id: int = Field(alias="systemId")
    state: RelayStatus = Field(alias="relayState")
    why_on: int = Field(alias="whyOn")


class TelemetryValveActuator(BaseModel):
    system_id: int = Field(alias="systemId")
    state: ValveActuatorStatus = Field(alias="valveActuatorState")
    why_on: int = Field(alias="whyOn")


class TelemetryVirtualHeater(BaseModel):
    system_id: int = Field(alias="systemId")
    current_set_point: int = Field(alias="Current-Set-Point")
    enabled: bool = Field(alias="enable")
    solar_set_point: int = Field(alias="SolarSetPoint")
    mode: int = Field(alias="Mode")
    silent_mode: int = Field(alias="SilentMode")
    why_on: int = Field(alias="whyHeaterIsOn")


class Telemetry(BaseModel):
    # version: str
    backyard: TelemetryBackyard = Field(alias="Backyard")
    bow: TelemetryBOW = Field(alias="BodyOfWater")
    chlorinator: list[TelemetryChlorinator] | TelemetryChlorinator = Field(alias="Chlorinator")
    colorlogic_light: list[TelemetryColorLogicLight] | TelemetryColorLogicLight = Field(alias="ColorLogic-Light")
    filter: list[TelemetryFilter] | TelemetryFilter = Field(alias="Filter")
    group: list[TelemetryGroup] | TelemetryGroup = Field(alias="Group")
    heater: list[TelemetryHeater] | TelemetryHeater = Field(alias="Heater")
    pump: list[TelemetryPump] | TelemetryPump = Field(alias="Pump")
    relay: list[TelemetryRelay] | TelemetryRelay = Field(alias="Relay")
    valve_actuator: list[TelemetryValveActuator] | TelemetryValveActuator = Field(alias="ValveActuator")
    virtual_heater: list[TelemetryVirtualHeater] | TelemetryVirtualHeater = Field(alias="VirtualHeater")

    class Config:
        orm_mode = True
        getter_dict = TelemetryGetter
