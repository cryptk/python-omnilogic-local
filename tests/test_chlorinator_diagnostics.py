"""Tests for chlorinator diagnostic response parsing."""

from __future__ import annotations

import math

import pytest

from pyomnilogic_local.models.chlorinator_diagnostics import ChlorinatorMeasurement, ChlorinatorRelayPolarity
from pyomnilogic_local.models.exceptions import OmniParsingError

MEASUREMENT_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<Response xmlns="http://nextgen.hayward.com/api">
    <Name>GetCHLORMeasurementRsp</Name>
    <Parameters>
        <Parameter name="PoolID" dataType="int">7</Parameter>
        <Parameter name="ChlorID" dataType="int">8</Parameter>
        <Parameter name="VoltageHighByte" dataType="byte">0</Parameter>
        <Parameter name="VoltageLowByte" dataType="byte">198</Parameter>
        <Parameter name="CurrentHighByte" dataType="byte">0</Parameter>
        <Parameter name="CurrentLowByte" dataType="byte">9</Parameter>
        <Parameter name="CellTempHighByte" dataType="byte">1</Parameter>
        <Parameter name="CellTempLowByte" dataType="byte">200</Parameter>
        <Parameter name="BoardTempHighByte" dataType="byte">1</Parameter>
        <Parameter name="BoardTempLowByte" dataType="byte">23</Parameter>
        <Parameter name="InstantSaltLevelHighByte" dataType="byte">11</Parameter>
        <Parameter name="InstantSaltLevelLowByte" dataType="byte">53</Parameter>
        <Parameter name="AverageSaltLevelHighByte" dataType="byte">11</Parameter>
        <Parameter name="AverageSaltLevelLowByte" dataType="byte">120</Parameter>
    </Parameters>
</Response>
"""

OFF_MEASUREMENT_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<Response xmlns="http://nextgen.hayward.com/api">
    <Name>GetCHLORMeasurementRsp</Name>
    <Parameters>
        <Parameter name="PoolID" dataType="int">7</Parameter>
        <Parameter name="ChlorID" dataType="int">8</Parameter>
        <Parameter name="VoltageHighByte" dataType="byte">0</Parameter>
        <Parameter name="VoltageLowByte" dataType="byte">0</Parameter>
        <Parameter name="CurrentHighByte" dataType="byte">0</Parameter>
        <Parameter name="CurrentLowByte" dataType="byte">0</Parameter>
        <Parameter name="CellTempHighByte" dataType="byte">0</Parameter>
        <Parameter name="CellTempLowByte" dataType="byte">0</Parameter>
        <Parameter name="BoardTempHighByte" dataType="byte">0</Parameter>
        <Parameter name="BoardTempLowByte" dataType="byte">0</Parameter>
        <Parameter name="InstantSaltLevelHighByte" dataType="byte">0</Parameter>
        <Parameter name="InstantSaltLevelLowByte" dataType="byte">0</Parameter>
        <Parameter name="AverageSaltLevelHighByte" dataType="byte">11</Parameter>
        <Parameter name="AverageSaltLevelLowByte" dataType="byte">84</Parameter>
    </Parameters>
</Response>
"""

INVALID_TEMPERATURE_XML = MEASUREMENT_XML.replace(
    '<Parameter name="CellTempHighByte" dataType="byte">1</Parameter>',
    '<Parameter name="CellTempHighByte" dataType="byte">255</Parameter>',
).replace(
    '<Parameter name="CellTempLowByte" dataType="byte">200</Parameter>',
    '<Parameter name="CellTempLowByte" dataType="byte">255</Parameter>',
)

POLARITY_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<Response xmlns="http://nextgen.hayward.com/api">
    <Name>GetCHLORRelayPolarityRsp</Name>
    <Parameters>
        <Parameter name="PoolID" dataType="int">7</Parameter>
        <Parameter name="ChlorID" dataType="int">8</Parameter>
        <Parameter name="RelaySetting" dataType="byte">1</Parameter>
    </Parameters>
</Response>
"""


def test_chlorinator_measurement_parses_diagnostics() -> None:
    """Parse raw measurement bytes and expose engineering units."""
    measurement = ChlorinatorMeasurement.load_xml(MEASUREMENT_XML)

    assert measurement.pool_id == 7
    assert measurement.chlorinator_id == 8
    assert measurement.voltage_raw == 198
    assert measurement.current_raw == 9
    assert measurement.cell_temperature_raw == 456
    assert measurement.board_temperature_raw == 279
    assert measurement.instant_salt_level == 2869
    assert measurement.average_salt_level == 2936
    assert math.isclose(measurement.voltage, 31.64, abs_tol=0.01)
    assert math.isclose(measurement.current, 0.36, abs_tol=0.01)
    assert math.isclose(measurement.cell_temperature_f, 85.4, abs_tol=0.1)
    assert math.isclose(measurement.board_temperature_f, 119.5, abs_tol=0.1)


def test_chlorinator_measurement_preserves_off_state() -> None:
    """Represent zero instantaneous values returned while disabled."""
    measurement = ChlorinatorMeasurement.load_xml(OFF_MEASUREMENT_XML)

    assert measurement.voltage == pytest.approx(0.0)
    assert measurement.current == pytest.approx(0.0)
    assert measurement.cell_temperature_f == pytest.approx(0.0)
    assert measurement.board_temperature_f == pytest.approx(0.0)
    assert measurement.instant_salt_level == 0
    assert measurement.average_salt_level == 2900


def test_chlorinator_measurement_reports_invalid_temperature() -> None:
    """Represent the controller's invalid temperature sentinel as None."""
    measurement = ChlorinatorMeasurement.load_xml(INVALID_TEMPERATURE_XML)

    assert measurement.cell_temperature_raw == 0xFFFF
    assert measurement.cell_temperature_f is None


def test_chlorinator_relay_polarity_parses_setting() -> None:
    """Parse the chlorinator relay polarity setting."""
    polarity = ChlorinatorRelayPolarity.load_xml(POLARITY_XML)

    assert polarity.pool_id == 7
    assert polarity.chlorinator_id == 8
    assert polarity.relay_setting == 1


def test_chlorinator_measurement_reports_missing_parameter() -> None:
    """Raise a protocol parsing error when a required parameter is absent."""
    measurement = ChlorinatorMeasurement.load_xml(MEASUREMENT_XML.replace(' name="VoltageLowByte"', ' name="UnexpectedParameter"'))

    with pytest.raises(OmniParsingError, match="Missing chlorinator diagnostic parameter: VoltageLowByte"):
        _ = measurement.voltage
