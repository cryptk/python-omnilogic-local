"""Models for OmniLogic chlorinator diagnostic responses."""

from __future__ import annotations

import math
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from xmltodict import parse as xml_parse

from pyomnilogic_local.models.exceptions import OmniParsingError

_INVALID_DIAGNOSTIC_VALUE = 0xFFFF
_ADC_REFERENCE_VOLTAGE = 5
_ADC_MAX_VALUE = 255
_VOLTAGE_SCALE = 8.15
_CURRENT_SCALE = 0.489

# OmniLogic uses 10 kΩ NTC thermistors for these temperature readings.
# Lookup table used by OmniLogic to convert the cell and board thermistor ADC
# readings to tenths of a degree Fahrenheit. Values between entries are
# interpolated using the low three bits of the raw reading.
_TEMPERATURE_TENTHS_F = (
    8000,
    3740,
    3136,
    2817,
    2603,
    2444,
    2318,
    2214,
    2125,
    2048,
    1980,
    1919,
    1864,
    1813,
    1767,
    1723,
    1683,
    1645,
    1610,
    1576,
    1544,
    1514,
    1485,
    1458,
    1431,
    1406,
    1381,
    1358,
    1335,
    1313,
    1291,
    1270,
    1250,
    1230,
    1211,
    1193,
    1174,
    1156,
    1139,
    1122,
    1105,
    1088,
    1072,
    1056,
    1041,
    1025,
    1010,
    995,
    980,
    966,
    951,
    937,
    923,
    909,
    895,
    881,
    868,
    854,
    841,
    828,
    815,
    802,
    789,
    776,
    763,
    750,
    737,
    725,
    712,
    699,
    687,
    674,
    661,
    649,
    636,
    624,
    611,
    598,
    586,
    573,
    560,
    547,
    534,
    521,
    508,
    495,
    482,
    469,
    455,
    442,
    428,
    414,
    400,
    386,
    372,
    357,
    342,
    327,
    312,
    297,
    281,
    265,
    248,
    231,
    214,
    196,
    178,
    159,
    140,
    120,
    99,
    77,
    54,
    31,
    6,
)


def _combine_bytes(high_byte: int, low_byte: int) -> int:
    return high_byte << 8 | low_byte


def _decode_temperature(raw_value: int) -> float | None:
    if raw_value == 0:
        return 0.0
    table_index, interpolation = divmod(raw_value, 8)
    if raw_value >= _INVALID_DIAGNOSTIC_VALUE or table_index >= len(_TEMPERATURE_TENTHS_F) - 1:
        return None

    temperature = _TEMPERATURE_TENTHS_F[table_index]
    if interpolation:
        difference = temperature - _TEMPERATURE_TENTHS_F[table_index + 1]
        temperature -= math.floor(((difference * interpolation * 10 / 8) + 5) / 10)
    return temperature / 10


class ChlorinatorDiagnosticParameter(BaseModel):
    """A named value from a chlorinator diagnostic response."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(alias="@name")
    data_type: str = Field(alias="@dataType")
    value: int = Field(alias="#text")


class ChlorinatorDiagnosticResponse(BaseModel):
    """Base model for parameter-based chlorinator diagnostic responses."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(alias="Name")
    parameters: list[ChlorinatorDiagnosticParameter] = Field(alias="Parameters")

    def get_param_by_name(self, name: str) -> int:
        """Return a diagnostic parameter by its wire name."""
        parameter = next((parameter for parameter in self.parameters if parameter.name == name), None)
        if parameter is None:
            msg = f"Missing chlorinator diagnostic parameter: {name}"
            raise OmniParsingError(msg)
        return parameter.value

    @classmethod
    def load_xml(cls, xml: str) -> Self:
        """Parse a chlorinator diagnostic XML response."""
        data = xml_parse(xml, force_list=("Parameter",))
        data["Response"]["Parameters"] = data["Response"]["Parameters"]["Parameter"]
        try:
            instance = cls.model_validate(data["Response"])
        except ValidationError as exc:
            msg = f"Failed to parse chlorinator diagnostics: {exc}"
            raise OmniParsingError(msg) from exc
        return instance


class ChlorinatorMeasurement(ChlorinatorDiagnosticResponse):
    """Electrical, temperature, and salt measurements from a chlorinator cell."""

    @property
    def pool_id(self) -> int:
        """Body-of-water system ID."""
        return self.get_param_by_name("PoolID")

    @property
    def chlorinator_id(self) -> int:
        """Physical chlorinator equipment ID."""
        return self.get_param_by_name("ChlorID")

    def _combined_parameter(self, prefix: str) -> int:
        return _combine_bytes(self.get_param_by_name(f"{prefix}HighByte"), self.get_param_by_name(f"{prefix}LowByte"))

    @property
    def voltage_raw(self) -> int:
        """Raw cell-voltage ADC reading."""
        return self._combined_parameter("Voltage")

    @property
    def current_raw(self) -> int:
        """Raw cell-current ADC reading."""
        return self._combined_parameter("Current")

    @property
    def cell_temperature_raw(self) -> int:
        """Raw cell-temperature thermistor reading."""
        return self._combined_parameter("CellTemp")

    @property
    def board_temperature_raw(self) -> int:
        """Raw controller-board temperature thermistor reading."""
        return self._combined_parameter("BoardTemp")

    @property
    def voltage(self) -> float | None:
        """Cell voltage in volts, or None when the controller reports an invalid sentinel."""
        if self.voltage_raw >= _INVALID_DIAGNOSTIC_VALUE:
            return None
        return self.voltage_raw * _ADC_REFERENCE_VOLTAGE / _ADC_MAX_VALUE * _VOLTAGE_SCALE

    @property
    def current(self) -> float | None:
        """Cell current in amperes, or None when the controller reports an invalid sentinel."""
        if self.current_raw >= _INVALID_DIAGNOSTIC_VALUE:
            return None
        return (self.current_raw * _ADC_REFERENCE_VOLTAGE / _ADC_MAX_VALUE) / _CURRENT_SCALE

    @property
    def cell_temperature_f(self) -> float | None:
        """Cell temperature in degrees Fahrenheit, or None when invalid."""
        return _decode_temperature(self.cell_temperature_raw)

    @property
    def board_temperature_f(self) -> float | None:
        """Controller-board temperature in degrees Fahrenheit, or None when invalid."""
        return _decode_temperature(self.board_temperature_raw)

    @property
    def instant_salt_level(self) -> int:
        """Instantaneous salt level in parts per million."""
        return self._combined_parameter("InstantSaltLevel")

    @property
    def average_salt_level(self) -> int:
        """Average salt level in parts per million."""
        return self._combined_parameter("AverageSaltLevel")


class ChlorinatorRelayPolarity(ChlorinatorDiagnosticResponse):
    """Relay polarity reported by the physical chlorinator equipment."""

    @property
    def pool_id(self) -> int:
        """Body-of-water system ID."""
        return self.get_param_by_name("PoolID")

    @property
    def chlorinator_id(self) -> int:
        """Physical chlorinator equipment ID."""
        return self.get_param_by_name("ChlorID")

    @property
    def relay_setting(self) -> int:
        """Raw chlorinator relay polarity setting."""
        return self.get_param_by_name("RelaySetting")
