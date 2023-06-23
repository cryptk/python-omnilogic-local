from __future__ import annotations

import logging
import sys
from typing import Any, Literal, TypeAlias

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from pydantic import BaseModel, Field, ValidationError
from xmltodict import parse as xml_parse

from ..exceptions import OmniParsingException
from ..types import (
    BodyOfWaterType,
    ChlorinatorDispenserType,
    ColorLogicLightType,
    ColorLogicShow,
    FilterType,
    HeaterType,
    OmniType,
    PumpFunction,
    PumpType,
    RelayFunction,
    RelayType,
    SensorType,
    SensorUnits,
)

_LOGGER = logging.getLogger(__name__)


class OmniBase(BaseModel):
    _sub_devices: set[str] | None = None
    system_id: int = Field(alias="System-Id")
    name: str | None = Field(alias="Name")
    bow_id: int | None

    def without_subdevices(self) -> Self:
        return self.copy(exclude=self._sub_devices)

    def propagate_bow_id(self, bow_id: int | None) -> None:
        # First we set our own bow_id
        self.bow_id = bow_id
        # If we have no devices under us, we have nothing to do
        if self._sub_devices is None:
            return
        for subdevice_name in self._sub_devices:
            subdevice = getattr(self, subdevice_name)
            # If our subdevice is a list of subdevices ...
            if isinstance(subdevice, list):
                for device in subdevice:
                    # ... then call propagate_bow_id on each of them ...
                    if device is not None:
                        device.propagate_bow_id(bow_id)
            # ... otherwise just call it on the single subdevice
            elif subdevice is not None:
                subdevice.propagate_bow_id(bow_id)


class MSPSystem(BaseModel):
    omni_type: OmniType = OmniType.SYSTEM
    vsp_speed_format: Literal["RPM", "Percent"] = Field(alias="Msp-Vsp-Speed-Format")
    units: Literal["Standard", "Metric"] = Field(alias="Units")


class MSPSensor(OmniBase):
    omni_type: OmniType = OmniType.SENSOR
    type: SensorType | str = Field(alias="Type")
    units: SensorUnits | str = Field(alias="Units")


class MSPFilter(OmniBase):
    omni_type: OmniType = OmniType.FILTER
    type: FilterType | str = Field(alias="Filter-Type")
    max_percent: int = Field(alias="Max-Pump-Speed")
    min_percent: int = Field(alias="Min-Pump-Speed")
    max_rpm: int = Field(alias="Max-Pump-RPM")
    min_rpm: int = Field(alias="Min-Pump-RPM")
    # We should figure out how to coerce this field into a True/False
    priming_enabled: Literal["yes", "no"] = Field(alias="Priming-Enabled")
    low_speed: int = Field(alias="Vsp-Low-Pump-Speed")
    medium_speed: int = Field(alias="Vsp-Medium-Pump-Speed")
    high_speed: int = Field(alias="Vsp-High-Pump-Speed")


class MSPPump(OmniBase):
    omni_type: OmniType = OmniType.PUMP
    type: PumpType | str = Field(alias="Type")
    function: PumpFunction | str = Field(alias="Function")
    max_percent: int = Field(alias="Max-Pump-Speed")
    min_percent: int = Field(alias="Min-Pump-Speed")
    max_rpm: int = Field(alias="Max-Pump-RPM")
    min_rpm: int = Field(alias="Min-Pump-RPM")
    # We should figure out how to coerce this field into a True/False
    priming_enabled: Literal["yes", "no"] = Field(alias="Priming-Enabled")
    low_speed: int = Field(alias="Vsp-Low-Pump-Speed")
    medium_speed: int = Field(alias="Vsp-Medium-Pump-Speed")
    high_speed: int = Field(alias="Vsp-High-Pump-Speed")


class MSPRelay(OmniBase):
    omni_type: OmniType = OmniType.RELAY
    type: RelayType | str = Field(alias="Type")
    function: RelayFunction | str = Field(alias="Function")


class MSPHeaterEquip(OmniBase):
    omni_type: OmniType = OmniType.HEATER_EQUIP
    type: Literal["PET_HEATER"] = Field(alias="Type")
    heater_type: HeaterType | str = Field(alias="Heater-Type")
    enabled: Literal["yes", "no"] = Field(alias="Enabled")
    min_filter_speed: int = Field(alias="Min-Speed-For-Operation")
    sensor_id: int = Field(alias="Sensor-System-Id")
    supports_cooling: Literal["yes", "no"] | None = Field(alias="SupportsCooling")


# This is the entry for the VirtualHeater, it does not use OmniBase because it has no name attribute
class MSPVirtualHeater(OmniBase):
    _sub_devices = {"heater_equipment"}

    omni_type: OmniType = OmniType.VIRT_HEATER
    enabled: Literal["yes", "no"] = Field(alias="Enabled")
    set_point: int = Field(alias="Current-Set-Point")
    solar_set_point: int | None = Field(alias="SolarSetPoint")
    max_temp: int = Field(alias="Max-Settable-Water-Temp")
    min_temp: int = Field(alias="Min-Settable-Water-Temp")
    heater_equipment: list[MSPHeaterEquip] | None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

        # The heater equipment are nested down inside a list of "Operations", which also includes non Heater-Equipment items.  We need to
        # first filter down to just the heater equipment items, then populate our self.heater_equipment with parsed versions of those items.
        heater_equip_data = [op[OmniType.HEATER_EQUIP] for op in data.get("Operation", {}) if OmniType.HEATER_EQUIP in op]
        self.heater_equipment = [MSPHeaterEquip.parse_obj(equip) for equip in heater_equip_data]


class MSPChlorinatorEquip(OmniBase):
    omni_type: OmniType = OmniType.CHLORINATOR_EQUIP
    enabled: Literal["yes", "no"] = Field(alias="Enabled")


class MSPChlorinator(OmniBase):
    _sub_devices = {"chlorinator_equipment"}

    omni_type: OmniType = OmniType.CHLORINATOR
    enabled: Literal["yes", "no"] = Field(alias="Enabled")
    timed_percent: int = Field(alias="Timed-Percent")
    superchlor_timeout: int = Field(alias="SuperChlor-Timeout")
    dispenser_type: ChlorinatorDispenserType | str = Field(alias="Dispenser-Type")
    chlorinator_equipment: list[MSPChlorinatorEquip] | None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

        # The heater equipment are nested down inside a list of "Operations", which also includes non Heater-Equipment items.  We need to
        # first filter down to just the heater equipment items, then populate our self.heater_equipment with parsed versions of those items.
        chlorinator_equip_data = [op for op in data.get("Operation", {}) if OmniType.CHLORINATOR_EQUIP in op][0]
        self.chlorinator_equipment = [MSPChlorinatorEquip.parse_obj(equip) for equip in chlorinator_equip_data[OmniType.CHLORINATOR_EQUIP]]


class MSPColorLogicLight(OmniBase):
    omni_type: OmniType = OmniType.CL_LIGHT
    type: ColorLogicLightType | str = Field(alias="Type")
    v2_active: Literal["yes", "no"] | None = Field(alias="V2-Active")
    effects: list[ColorLogicShow] | None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.effects = list(ColorLogicShow) if self.v2_active == "yes" else [show for show in ColorLogicShow if show.value <= 16]


class MSPBoW(OmniBase):
    _sub_devices = {"filter", "relay", "heater", "sensor", "colorlogic_light", "pump", "chlorinator"}

    omni_type: OmniType = OmniType.BOW
    type: BodyOfWaterType | str = Field(alias="Type")
    filter: list[MSPFilter] | None = Field(alias="Filter")
    relay: list[MSPRelay] | None = Field(alias="Relay")
    heater: MSPVirtualHeater | None = Field(alias="Heater")
    sensor: list[MSPSensor] | None = Field(alias="Sensor")
    colorlogic_light: list[MSPColorLogicLight] | None = Field(alias="ColorLogic-Light")
    pump: list[MSPPump] | None = Field(alias="Pump")
    chlorinator: MSPChlorinator | None = Field(alias="Chlorinator")

    # We override the __init__ here so that we can trigger the propagation of the bow_id down to all of it's sub devices after the bow
    # itself is initialized
    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.propagate_bow_id(self.system_id)


class MSPBackyard(OmniBase):
    _sub_devices = {"sensor", "bow"}

    omni_type: OmniType = OmniType.BACKYARD
    sensor: list[MSPSensor] | None = Field(alias="Sensor")
    bow: list[MSPBoW] | None = Field(alias="Body-of-water")
    relay: list[MSPRelay] | None = Field(alias="Relay")


class MSPSchedule(OmniBase):
    omni_type: OmniType = OmniType.SCHEDULE
    system_id: int = Field(alias="schedule-system-id")
    bow_id: int = Field(alias="bow-system-id")
    equipment_id: int = Field(alias="equipment-id")
    enabled: bool = Field()


MSPConfigType: TypeAlias = (
    MSPSystem | MSPSchedule | MSPBackyard | MSPBoW | MSPVirtualHeater | MSPHeaterEquip | MSPRelay | MSPFilter | MSPSensor
)


class MSPConfig(BaseModel):
    system: MSPSystem = Field(alias="System")
    backyard: MSPBackyard = Field(alias="Backyard")

    class Config:
        orm_mode = True

    @staticmethod
    def load_xml(xml: str) -> MSPConfig:
        data = xml_parse(
            xml,
            # Some things will be lists or not depending on if a pool has more than one of that piece of equipment.  Here we are coercing
            # everything that *could* be a list into a list to make the parsing more consistent.
            force_list=(
                OmniType.BOW_MSP,
                OmniType.CHLORINATOR_EQUIP,
                OmniType.CL_LIGHT,
                OmniType.FAVORITES,
                OmniType.FILTER,
                OmniType.GROUPS,
                OmniType.PUMP,
                OmniType.RELAY,
                OmniType.SENSOR,
                OmniType.SCHE,
            ),
        )
        try:
            return MSPConfig.parse_obj(data["MSPConfig"])
        except ValidationError as exc:
            raise OmniParsingException(f"Failed to parse MSP Configuration: {exc}") from exc
