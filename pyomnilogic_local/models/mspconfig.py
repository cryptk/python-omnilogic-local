from __future__ import annotations

import logging
from typing import Any, Literal

from pydantic import BaseModel, Field
from xmltodict import parse as xml_parse

from ..types import (
    BodyOfWaterType,
    FilterType,
    HeaterType,
    RelayFunction,
    RelayType,
    SensorType,
    SensorUnits,
)

_LOGGER = logging.getLogger(__name__)


class OmniBase(BaseModel):
    system_id: int = Field(alias="System-Id")
    name: str = Field(alias="Name")


class BOWMixin(BaseModel):
    bow_id: int | None

    def propagate_bow_id(self, bow_id: int | None) -> None:
        self.bow_id = bow_id
        for field in self.__fields__:
            devices = getattr(self, field)
            try:
                for device in devices:
                    device.propogate_bow_id(bow_id)
            except (AttributeError, TypeError):
                # The child is not using the BOWMixin
                pass


class MSPSystem(BaseModel):
    vsp_speed_format: Literal["RPM", "Percent"] = Field(alias="Msp-Vsp-Speed-Format")
    units: Literal["Standard", "Metric"] = Field(alias="Units")


class MSPSensor(BOWMixin, OmniBase):
    type: SensorType = Field(alias="Type")
    units: SensorUnits = Field(alias="Units")


class MSPFilter(BOWMixin, BaseModel):
    system_id: int = Field(alias="System-Id")
    name: str = Field(alias="Name")
    type: FilterType = Field(alias="Filter-Type")
    max_percent: int = Field(alias="Max-Pump-Speed")
    min_percent: int = Field(alias="Min-Pump-Speed")
    max_rpm: int = Field(alias="Max-Pump-RPM")
    min_rpm: int = Field(alias="Min-Pump-RPM")
    # We should figure out how to coerce this field into a True/False
    priming_enabled: Literal["yes", "no"] = Field(alias="Priming-Enabled")
    low_speed: int = Field(alias="Vsp-Low-Pump-Speed")
    medium_speed: int = Field(alias="Vsp-Medium-Pump-Speed")
    high_speed: int = Field(alias="Vsp-High-Pump-Speed")


class MSPRelay(BOWMixin, OmniBase):
    type: RelayType = Field(alias="Type")
    function: RelayFunction = Field(alias="Function")


class MSPHeaterEquip(BOWMixin, OmniBase):
    type: Literal["PET_HEATER"] = Field(alias="Type")
    heater_type: HeaterType = Field(alias="Heater-Type")
    enabled: Literal["yes", "no"] = Field(alias="Enabled")
    min_filter_speed: int = Field(alias="Min-Speed-For-Operation")
    sensor_id: int = Field(alias="Sensor-System-Id")
    supports_cooling: Literal["yes", "no"] = Field(alias="SupportsCooling")


# This is the entry for the VirtualHeater, it does not use OmniBase because it has no name attribute
class MSPVirtualHeater(BOWMixin, BaseModel):
    system_id: int = Field(alias="System-Id")
    enabled: Literal["yes", "no"] = Field(alias="Enabled")
    set_point: int = Field(alias="Current-Set-Point")
    solar_set_point: int = Field(alias="SolarSetPoint")
    max_temp: int = Field(alias="Max-Settable-Water-Temp")
    min_temp: int = Field(alias="Min-Settable-Water-Temp")
    heater_equipment: list[MSPHeaterEquip] | None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

        # The heater equipment are nested down inside a list of "Operations", which also includes non Heater-Equipment items.  We need to
        # first filter down to just the heater equipment items, then populate our self.heater_equipment with parsed versions of those items.
        heater_equip_data = [op for op in data.get("Operation", {}) if "Heater-Equipment" in op]
        if heater_equip_data:
            self.heater_equipment = [MSPHeaterEquip.parse_obj(equip["Heater-Equipment"]) for equip in heater_equip_data]


class MSPBoW(BOWMixin, OmniBase):
    type: BodyOfWaterType = Field(alias="Type")
    filter: list[MSPFilter] | None = Field(alias="Filter")
    relay: list[MSPRelay] | None = Field(alias="Relay")
    heater: MSPVirtualHeater | None = Field(alias="Heater")
    sensor: list[MSPSensor] | None = Field(alias="Sensor")

    # We override the __init__ here so that we can trigger the propagation of the bow_id down to all of it's sub devices after the bow
    # itself is initialized
    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.propagate_bow_id(self.system_id)


class MSPBackyard(OmniBase):
    sensor: list[MSPSensor] | None = Field(alias="Sensor")
    bow: list[MSPBoW] | None = Field(alias="Body-of-water")


class MSPSchedule(BaseModel):
    system_id: int = Field(alias="schedule-system-id")
    bow_id: int = Field(alias="bow-system-id")
    equipment_id: int = Field(alias="equipment-id")
    enabled: bool = Field()

    def __init__(self, **data: Any) -> None:
        print(data)
        super().__init__(**data)


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
            force_list=("Body-of-water", "Sensor", "Filter", "Relay", "sche", "Favorites", "Groups"),
        )
        return MSPConfig.parse_obj(data["MSPConfig"])

    # def get_telem_by_systemid(self, system_id: int) -> TTelemetry | None:
    #     for field_name, value in self:
    #         if field_name == "version" or value is None:
    #             continue
    #         for model in value:
    #             cast_model = cast(TTelemetry, model)
    #             if cast_model.system_id == system_id:
    #                 return cast_model
    #     return None
