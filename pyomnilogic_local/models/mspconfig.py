# ruff: noqa: TC001  # pydantic relies on the omnitypes imports at runtime
from __future__ import annotations

import contextlib
import logging
from typing import Any, ClassVar, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    computed_field,
    model_validator,
)
from xmltodict import parse as xml_parse

from pyomnilogic_local.omnitypes import (
    BodyOfWaterType,
    ChlorinatorCellType,
    ChlorinatorDispenserType,
    ChlorinatorType,
    ColorLogicLightType,
    ColorLogicShow25,
    ColorLogicShow40,
    ColorLogicShowUCL,
    ColorLogicShowUCLV2,
    CSADEquipmentType,
    CSADType,
    FilterType,
    HeaterType,
    LightShows,
    MessageType,
    OmniType,
    PentairShow,
    PumpFunction,
    PumpType,
    RelayFunction,
    RelayType,
    ScheduleDaysActive,
    SensorType,
    SensorUnits,
    ZodiacShow,
)

from .exceptions import OmniParsingError

_LOGGER = logging.getLogger(__name__)


class OmniBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    _sub_devices: set[str] | None = None
    system_id: int = Field(alias="System-Id")
    name: str | None = Field(alias="Name", default=None)
    bow_id: int = -1
    omni_type: OmniType

    def without_subdevices(self) -> Self:
        data = self.model_dump(exclude=self._sub_devices, round_trip=True, by_alias=True)
        copied = self.model_validate(data)
        _LOGGER.debug("without_subdevices: original=%s, copied=%s", self, copied)
        return copied

    def propagate_bow_id(self, bow_id: int) -> None:
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

    _YES_NO_FIELDS: ClassVar[set[str]] = set()

    @model_validator(mode="before")
    @classmethod
    def convert_yes_no_to_bool(cls, data: Any) -> Any:
        # Check if data is a dictionary (common when loading from XML/JSON)
        if not isinstance(data, dict):
            return data

        for key in cls._YES_NO_FIELDS:
            raw_value = data.get(key)

            if isinstance(raw_value, str):
                lower_value = raw_value.lower()

                if lower_value == "yes":
                    data[key] = True
                elif lower_value == "no":
                    data[key] = False

        return data


class MSPSystem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    omni_type: OmniType = OmniType.SYSTEM

    vsp_speed_format: Literal["RPM", "Percent"] = Field(alias="Msp-Vsp-Speed-Format")
    units: Literal["Standard", "Metric"] = Field(alias="Units")


class MSPSensor(OmniBase):
    omni_type: OmniType = OmniType.SENSOR

    equip_type: SensorType = Field(alias="Type")
    units: SensorUnits = Field(alias="Units")


class MSPFilter(OmniBase):
    _YES_NO_FIELDS = {"priming_enabled"}

    omni_type: OmniType = OmniType.FILTER

    equip_type: FilterType = Field(alias="Filter-Type")
    max_percent: int = Field(alias="Max-Pump-Speed")
    min_percent: int = Field(alias="Min-Pump-Speed")
    max_rpm: int = Field(alias="Max-Pump-RPM")
    min_rpm: int = Field(alias="Min-Pump-RPM")
    # We should figure out how to coerce this field into a True/False
    priming_enabled: bool = Field(alias="Priming-Enabled")
    low_speed: int = Field(alias="Vsp-Low-Pump-Speed")
    medium_speed: int = Field(alias="Vsp-Medium-Pump-Speed")
    high_speed: int = Field(alias="Vsp-High-Pump-Speed")


class MSPPump(OmniBase):
    _YES_NO_FIELDS = {"priming_enabled"}

    omni_type: OmniType = OmniType.PUMP

    equip_type: PumpType = Field(alias="Type")
    function: PumpFunction = Field(alias="Function")
    max_percent: int = Field(alias="Max-Pump-Speed")
    min_percent: int = Field(alias="Min-Pump-Speed")
    max_rpm: int = Field(alias="Max-Pump-RPM")
    min_rpm: int = Field(alias="Min-Pump-RPM")
    # We should figure out how to coerce this field into a True/False
    priming_enabled: bool = Field(alias="Priming-Enabled")
    low_speed: int = Field(alias="Vsp-Low-Pump-Speed")
    medium_speed: int = Field(alias="Vsp-Medium-Pump-Speed")
    high_speed: int = Field(alias="Vsp-High-Pump-Speed")


class MSPRelay(OmniBase):
    omni_type: OmniType = OmniType.RELAY

    type: RelayType = Field(alias="Type")
    function: RelayFunction = Field(alias="Function")


class MSPHeaterEquip(OmniBase):
    _YES_NO_FIELDS = {"enabled", "supports_cooling"}

    omni_type: OmniType = OmniType.HEATER_EQUIP

    equip_type: Literal["PET_HEATER"] = Field(alias="Type")
    heater_type: HeaterType = Field(alias="Heater-Type")
    enabled: bool = Field(alias="Enabled")
    min_filter_speed: int = Field(alias="Min-Speed-For-Operation")
    sensor_id: int = Field(alias="Sensor-System-Id")
    supports_cooling: bool | None = Field(alias="SupportsCooling", default=None)


# This is the entry for the VirtualHeater, it does not use OmniBase because it has no name attribute
class MSPVirtualHeater(OmniBase):
    _sub_devices = {"heater_equipment"}
    _YES_NO_FIELDS = {"enabled"}

    omni_type: OmniType = OmniType.VIRT_HEATER

    enabled: bool = Field(alias="Enabled")
    set_point: int = Field(alias="Current-Set-Point")
    solar_set_point: int | None = Field(alias="SolarSetPoint", default=None)
    max_temp: int = Field(alias="Max-Settable-Water-Temp")
    min_temp: int = Field(alias="Min-Settable-Water-Temp")
    heater_equipment: list[MSPHeaterEquip] | None = None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

        # The heater equipment are nested down inside a list of "Operations", which also includes non Heater-Equipment items.  We need to
        # first filter down to just the heater equipment items, then populate our self.heater_equipment with parsed versions of those items.
        heater_equip_data = [op[OmniType.HEATER_EQUIP] for op in data.get("Operation", {}) if OmniType.HEATER_EQUIP in op]
        self.heater_equipment = [MSPHeaterEquip.model_validate(equip) for equip in heater_equip_data]


class MSPChlorinatorEquip(OmniBase):
    _YES_NO_FIELDS = {"enabled"}

    omni_type: OmniType = OmniType.CHLORINATOR_EQUIP

    equip_type: Literal["PET_CHLORINATOR"] = Field(alias="Type")
    chlorinator_type: ChlorinatorType = Field(alias="Chlorinator-Type")
    enabled: bool = Field(alias="Enabled")


class MSPChlorinator(OmniBase):
    _sub_devices = {"chlorinator_equipment"}
    _YES_NO_FIELDS = {"enabled"}

    omni_type: OmniType = OmniType.CHLORINATOR

    enabled: bool = Field(alias="Enabled")
    timed_percent: int = Field(alias="Timed-Percent")
    superchlor_timeout: int = Field(alias="SuperChlor-Timeout")
    orp_timeout: int = Field(alias="ORP-Timeout")
    dispenser_type: ChlorinatorDispenserType = Field(alias="Dispenser-Type")
    cell_type: ChlorinatorCellType = Field(alias="Cell-Type")
    chlorinator_equipment: list[MSPChlorinatorEquip] | None = None

    @model_validator(mode="before")
    @classmethod
    def convert_cell_type(cls, data: Any) -> Any:
        """Convert cell_type string to ChlorinatorCellType enum by name."""
        if isinstance(data, dict) and "Cell-Type" in data:
            cell_type_str = data["Cell-Type"]
            if isinstance(cell_type_str, str):
                # Parse by enum member name (e.g., "CELL_TYPE_T15" -> ChlorinatorCellType.CELL_TYPE_T15)
                with contextlib.suppress(KeyError):
                    data["Cell-Type"] = ChlorinatorCellType[cell_type_str]
        return data

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

        # The chlorinator equipment are nested down inside a list of "Operations", which also includes non Chlorinator-Equipment items.
        # We need to first filter down to just the chlorinator equipment items, then populate our self.chlorinator_equipment with parsed
        # versions of those items.
        chlorinator_equip_data = [op[OmniType.CHLORINATOR_EQUIP] for op in data.get("Operation", {}) if OmniType.CHLORINATOR_EQUIP in op]
        self.chlorinator_equipment = [MSPChlorinatorEquip.model_validate(equip) for equip in chlorinator_equip_data]


class MSPCSADEquip(OmniBase):
    _YES_NO_FIELDS = {"enabled"}

    omni_type: OmniType = OmniType.CSAD_EQUIP

    equip_type: Literal["PET_CSAD"] = Field(alias="Type")
    csad_type: CSADEquipmentType | str = Field(alias="CSAD-Type")
    enabled: bool = Field(alias="Enabled")


class MSPCSAD(OmniBase):
    _sub_devices = {"csad_equipment"}
    _YES_NO_FIELDS = {"enabled"}

    omni_type: OmniType = OmniType.CSAD

    enabled: bool = Field(alias="Enabled")
    equip_type: CSADType = Field(alias="Type")
    target_value: float = Field(alias="TargetValue")
    calibration_value: float = Field(alias="CalibrationValue")
    ph_low_alarm_value: float = Field(alias="PHLowAlarmLevel")
    ph_high_alarm_value: float = Field(alias="PHHighAlarmLevel")
    orp_target_level: int = Field(alias="ORP-Target-Level")
    orp_runtime_level: int = Field(alias="ORP-Runtime-Level")
    orp_low_alarm_level: int = Field(alias="ORP-Low-Alarm-Level")
    orp_high_alarm_level: int = Field(alias="ORP-High-Alarm-Level")
    orp_forced_on_time: int = Field(alias="ORP-Forced-On-Time")
    orp_forced_enabled: bool = Field(alias="ORP-Forced-Enabled")
    csad_equipment: list[MSPCSADEquip] | None = None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

        # The CSAD equipment are nested down inside a list of "Operations", which also includes non CSAD-Equipment items.
        # We need to first filter down to just the CSAD equipment items, then populate our self.csad_equipment with parsed
        # versions of those items.
        csad_equip_data = [op[OmniType.CSAD_EQUIP] for op in data.get("Operation", {}) if OmniType.CSAD_EQUIP in op]
        self.csad_equipment = [MSPCSADEquip.model_validate(equip) for equip in csad_equip_data]


class MSPColorLogicLight(OmniBase):
    _YES_NO_FIELDS = {"v2_active"}

    omni_type: OmniType = OmniType.CL_LIGHT

    v2_active: bool = Field(alias="V2-Active", default=False)
    equip_type: ColorLogicLightType = Field(alias="Type")
    effects: list[LightShows] | None = None

    @model_validator(mode="after")
    def set_effects(self) -> Any:
        """Set the available light shows based on the light type."""
        match self.equip_type:
            case ColorLogicLightType.TWO_FIVE:
                self.effects = list(ColorLogicShow25)
            case ColorLogicLightType.FOUR_ZERO:
                self.effects = list(ColorLogicShow40)
            case ColorLogicLightType.UCL:
                if self.v2_active:
                    self.effects = list(ColorLogicShowUCLV2)
                else:
                    self.effects = list(ColorLogicShowUCL)
            case ColorLogicLightType.PENTAIR_COLOR:
                self.effects = list(PentairShow)
            case ColorLogicLightType.ZODIAC_COLOR:
                self.effects = list(ZodiacShow)
        return self


class MSPGroup(OmniBase):
    omni_type: OmniType = OmniType.GROUP

    icon_id: int = Field(alias="Icon-Id")


class MSPBoW(OmniBase):
    _sub_devices = {"filter", "relay", "heater", "sensor", "colorlogic_light", "pump", "chlorinator", "csad"}
    _YES_NO_FIELDS = {"supports_spillover"}

    omni_type: OmniType = OmniType.BOW

    equip_type: BodyOfWaterType = Field(alias="Type")
    supports_spillover: bool = Field(alias="Supports-Spillover", default=False)
    filter: list[MSPFilter] | None = Field(alias="Filter", default=None)
    relay: list[MSPRelay] | None = Field(alias="Relay", default=None)
    heater: MSPVirtualHeater | None = Field(alias="Heater", default=None)
    sensor: list[MSPSensor] | None = Field(alias="Sensor", default=None)
    colorlogic_light: list[MSPColorLogicLight] | None = Field(alias="ColorLogic-Light", default=None)
    pump: list[MSPPump] | None = Field(alias="Pump", default=None)
    chlorinator: MSPChlorinator | None = Field(alias="Chlorinator", default=None)
    csad: list[MSPCSAD] | None = Field(alias="CSAD", default=None)

    # We override the __init__ here so that we can trigger the propagation of the bow_id down to all of it's sub devices after the bow
    # itself is initialized
    def __init__(self, **data: Any) -> None:
        # As we are requiring a bow_id on everything in OmniBase, we need to propagate it down now
        # before calling super().__init__() so that it will be present for validation.
        super().__init__(**data)
        self.propagate_bow_id(self.system_id)


class MSPBackyard(OmniBase):
    _sub_devices = {"sensor", "bow", "colorlogic_light", "relay"}
    bow_id: int = -1

    omni_type: OmniType = OmniType.BACKYARD

    bow: list[MSPBoW] | None = Field(alias="Body-of-water", default=None)
    colorlogic_light: list[MSPColorLogicLight] | None = Field(alias="ColorLogic-Light", default=None)
    relay: list[MSPRelay] | None = Field(alias="Relay", default=None)
    sensor: list[MSPSensor] | None = Field(alias="Sensor", default=None)


class MSPSchedule(OmniBase):
    omni_type: OmniType = OmniType.SCHEDULE

    bow_id: int = Field(alias="bow-system-id")  # pyright: ignore[reportGeneralTypeIssues]
    equipment_id: int = Field(alias="equipment-id")
    system_id: int = Field(alias="schedule-system-id")
    event: MessageType = Field(alias="event")
    data: int = Field(alias="data")
    enabled: bool = Field()
    start_minute: int = Field(alias="start-minute")
    start_hour: int = Field(alias="start-hour")
    end_minute: int = Field(alias="end-minute")
    end_hour: int = Field(alias="end-hour")
    days_active_raw: int = Field(alias="days-active")
    recurring: bool = Field(alias="recurring")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def days_active(self) -> list[str]:
        """Decode days_active_raw bitmask into a list of active day names.

        Returns:
            List of active day names as strings

        Example:
            >>> schedule.days_active
            ['Monday', 'Wednesday', 'Friday']
        """
        flags = ScheduleDaysActive(self.days_active_raw)
        return [flag.name for flag in ScheduleDaysActive if flags & flag and flag.name is not None]


type MSPEquipmentType = (
    MSPSchedule
    | MSPBackyard
    | MSPBoW
    | MSPVirtualHeater
    | MSPHeaterEquip
    | MSPRelay
    | MSPFilter
    | MSPSensor
    | MSPPump
    | MSPChlorinator
    | MSPChlorinatorEquip
    | MSPCSAD
    | MSPCSADEquip
    | MSPColorLogicLight
    | MSPGroup
)

type MSPConfigType = MSPSystem | MSPEquipmentType


class MSPConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    system: MSPSystem = Field(alias="System")
    backyard: MSPBackyard = Field(alias="Backyard")
    groups: list[MSPGroup] | None = None
    schedules: list[MSPSchedule] | None = None

    def __init__(self, **data: Any) -> None:
        # Extract groups from the Groups container if present
        group_data: dict[str, Any] | None = None
        with contextlib.suppress(KeyError):
            group_data = data["Groups"]["Group"]

        if group_data:
            data["groups"] = [MSPGroup.model_validate(g) for g in group_data]
        else:
            data["groups"] = []

        # Extract schedules from the Schedules container if present
        schedule_data: dict[str, Any] | None = None
        with contextlib.suppress(KeyError):
            schedule_data = data["Schedules"]["sche"]

        if schedule_data:
            data["schedules"] = [MSPSchedule.model_validate(s) for s in schedule_data]
        else:
            data["schedules"] = []

        super().__init__(**data)

    @staticmethod
    def load_xml(xml: str) -> MSPConfig:
        data = xml_parse(
            xml,
            # Some things will be lists or not depending on if a pool has more than one of that piece of equipment.  Here we are coercing
            # everything that *could* be a list into a list to make the parsing more consistent.
            force_list=(
                OmniType.BOW_MSP,
                OmniType.CSAD,
                OmniType.CL_LIGHT,
                OmniType.FAVORITES,
                OmniType.FILTER,
                OmniType.GROUP,
                OmniType.PUMP,
                OmniType.RELAY,
                OmniType.SENSOR,
                OmniType.SCHE,
            ),
        )
        try:
            return MSPConfig.model_validate(data["MSPConfig"], from_attributes=True)
        except ValidationError as exc:
            msg = f"Failed to parse MSP Configuration: {exc}"
            raise OmniParsingError(msg) from exc
