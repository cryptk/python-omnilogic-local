"""Tests for Filter and Pump equipment classes."""

# pyright: basic
# mypy: ignore-errors
# type: ignore
# pylint: skip-file

from unittest.mock import AsyncMock, Mock

import pytest

from pyomnilogic_local.filter import Filter
from pyomnilogic_local.models.mspconfig import MSPFilter, MSPPump
from pyomnilogic_local.models.telemetry import Telemetry, TelemetryFilter, TelemetryPump
from pyomnilogic_local.omnitypes import (
    FilterSpeedPresets,
    FilterState,
    OmniType,
    PumpState,
)
from pyomnilogic_local.pump import Pump


@pytest.fixture
def mock_omni():
    """Create a mock OmniLogic instance."""
    omni = Mock()
    omni._api = Mock()
    return omni


@pytest.fixture
def sample_filter_config():
    """Create a sample filter configuration."""
    return MSPFilter(
        **{
            "System-Id": 8,
            "Name": "Test Filter",
            "Filter-Type": "FMT_VARIABLE_SPEED_PUMP",
            "Max-Pump-Speed": 100,
            "Min-Pump-Speed": 30,
            "Max-Pump-RPM": 3450,
            "Min-Pump-RPM": 1000,
            "Priming-Enabled": "yes",
            "Vsp-Low-Pump-Speed": 40,
            "Vsp-Medium-Pump-Speed": 60,
            "Vsp-High-Pump-Speed": 80,
        }
    )


@pytest.fixture
def sample_filter_telemetry():
    """Create sample filter telemetry."""
    return TelemetryFilter(
        omni_type=OmniType.FILTER,
        **{
            "@systemId": 8,
            "@filterState": 1,
            "@filterSpeed": 60,
            "@valvePosition": 1,
            "@whyFilterIsOn": 14,
            "@reportedFilterSpeed": 60,
            "@power": 500,
            "@lastSpeed": 50,
        },
    )


@pytest.fixture
def sample_pump_config():
    """Create a sample pump configuration."""
    return MSPPump(
        **{
            "System-Id": 15,
            "Name": "Test Pump",
            "Type": "PMP_VARIABLE_SPEED_PUMP",
            "Function": "PMP_PUMP",
            "Max-Pump-Speed": 100,
            "Min-Pump-Speed": 30,
            "Max-Pump-RPM": 3450,
            "Min-Pump-RPM": 1000,
            "Priming-Enabled": "yes",
            "Vsp-Low-Pump-Speed": 40,
            "Vsp-Medium-Pump-Speed": 60,
            "Vsp-High-Pump-Speed": 80,
        }
    )


@pytest.fixture
def sample_pump_telemetry():
    """Create sample pump telemetry."""
    return TelemetryPump(
        omni_type=OmniType.PUMP,
        **{
            "@systemId": 15,
            "@pumpState": 1,
            "@pumpSpeed": 60,
            "@lastSpeed": 50,
            "@whyOn": 11,
        },
    )


@pytest.fixture
def mock_telemetry(sample_filter_telemetry, sample_pump_telemetry):
    """Create a mock Telemetry object."""
    telemetry = Mock(spec=Telemetry)
    telemetry.get_telem_by_systemid = Mock(
        side_effect=lambda sid: sample_filter_telemetry if sid == 8 else sample_pump_telemetry if sid == 15 else None
    )
    return telemetry


class TestFilter:
    """Tests for Filter class."""

    def test_filter_properties_config(self, mock_omni, sample_filter_config, mock_telemetry):
        """Test that filter config properties are correctly exposed."""
        sample_filter_config.bow_id = 7
        filter_obj = Filter(mock_omni, sample_filter_config, mock_telemetry)

        assert filter_obj.equip_type == "FMT_VARIABLE_SPEED_PUMP"
        assert filter_obj.max_percent == 100
        assert filter_obj.min_percent == 30
        assert filter_obj.max_rpm == 3450
        assert filter_obj.min_rpm == 1000
        assert filter_obj.priming_enabled is True
        assert filter_obj.low_speed == 40
        assert filter_obj.medium_speed == 60
        assert filter_obj.high_speed == 80

    def test_filter_properties_telemetry(self, mock_omni, sample_filter_config, mock_telemetry):
        """Test that filter telemetry properties are correctly exposed."""
        sample_filter_config.bow_id = 7
        filter_obj = Filter(mock_omni, sample_filter_config, mock_telemetry)

        assert filter_obj.state == FilterState.ON
        assert filter_obj.speed == 60
        assert filter_obj.valve_position == 1
        assert filter_obj.why_on == 14
        assert filter_obj.reported_speed == 60
        assert filter_obj.power == 500
        assert filter_obj.last_speed == 50

    def test_filter_is_on_true(self, mock_omni, sample_filter_config, mock_telemetry):
        """Test is_on returns True when filter is on."""
        sample_filter_config.bow_id = 7
        filter_obj = Filter(mock_omni, sample_filter_config, mock_telemetry)

        assert filter_obj.is_on is True

    def test_filter_is_on_false(self, mock_omni, sample_filter_config, mock_telemetry):
        """Test is_on returns False when filter is off."""
        sample_filter_config.bow_id = 7
        filter_obj = Filter(mock_omni, sample_filter_config, mock_telemetry)
        filter_obj.telemetry.state = FilterState.OFF

        assert filter_obj.is_on is False

    def test_filter_is_ready_true(self, mock_omni, sample_filter_config, mock_telemetry):
        """Test is_ready returns True for stable states."""
        sample_filter_config.bow_id = 7
        filter_obj = Filter(mock_omni, sample_filter_config, mock_telemetry)

        # ON state
        filter_obj.telemetry.state = FilterState.ON
        assert filter_obj.is_ready is True

        # OFF state
        filter_obj.telemetry.state = FilterState.OFF
        assert filter_obj.is_ready is True

    def test_filter_is_ready_false(self, mock_omni, sample_filter_config, mock_telemetry):
        """Test is_ready returns False for transitional states."""
        sample_filter_config.bow_id = 7
        filter_obj = Filter(mock_omni, sample_filter_config, mock_telemetry)

        # PRIMING state
        filter_obj.telemetry.state = FilterState.PRIMING
        assert filter_obj.is_ready is False

        # WAITING_TURN_OFF state
        filter_obj.telemetry.state = FilterState.WAITING_TURN_OFF
        assert filter_obj.is_ready is False

    @pytest.mark.asyncio
    async def test_filter_turn_on(self, mock_omni, sample_filter_config, mock_telemetry):
        """Test turn_on method calls API correctly."""
        sample_filter_config.bow_id = 7
        filter_obj = Filter(mock_omni, sample_filter_config, mock_telemetry)
        filter_obj._api.async_set_equipment = AsyncMock()

        await filter_obj.turn_on()

        filter_obj._api.async_set_equipment.assert_called_once_with(
            pool_id=7,
            equipment_id=8,
            is_on=filter_obj.last_speed,
        )

    @pytest.mark.asyncio
    async def test_filter_turn_off(self, mock_omni, sample_filter_config, mock_telemetry):
        """Test turn_off method calls API correctly."""
        sample_filter_config.bow_id = 7
        filter_obj = Filter(mock_omni, sample_filter_config, mock_telemetry)
        filter_obj._api.async_set_equipment = AsyncMock()

        await filter_obj.turn_off()

        filter_obj._api.async_set_equipment.assert_called_once_with(
            pool_id=7,
            equipment_id=8,
            is_on=False,
        )

    @pytest.mark.asyncio
    async def test_filter_run_preset_speed_low(self, mock_omni, sample_filter_config, mock_telemetry):
        """Test run_preset_speed with LOW preset."""
        sample_filter_config.bow_id = 7
        filter_obj = Filter(mock_omni, sample_filter_config, mock_telemetry)
        filter_obj._api.async_set_equipment = AsyncMock()

        await filter_obj.run_preset_speed(FilterSpeedPresets.LOW)

        filter_obj._api.async_set_equipment.assert_called_once_with(
            pool_id=7,
            equipment_id=8,
            is_on=40,
        )

    @pytest.mark.asyncio
    async def test_filter_run_preset_speed_medium(self, mock_omni, sample_filter_config, mock_telemetry):
        """Test run_preset_speed with MEDIUM preset."""
        sample_filter_config.bow_id = 7
        filter_obj = Filter(mock_omni, sample_filter_config, mock_telemetry)
        filter_obj._api.async_set_equipment = AsyncMock()

        await filter_obj.run_preset_speed(FilterSpeedPresets.MEDIUM)

        filter_obj._api.async_set_equipment.assert_called_once_with(
            pool_id=7,
            equipment_id=8,
            is_on=filter_obj.medium_speed,
        )

    @pytest.mark.asyncio
    async def test_filter_run_preset_speed_high(self, mock_omni, sample_filter_config, mock_telemetry):
        """Test run_preset_speed with HIGH preset."""
        sample_filter_config.bow_id = 7
        filter_obj = Filter(mock_omni, sample_filter_config, mock_telemetry)
        filter_obj._api.async_set_equipment = AsyncMock()

        await filter_obj.run_preset_speed(FilterSpeedPresets.HIGH)

        filter_obj._api.async_set_equipment.assert_called_once_with(
            pool_id=7,
            equipment_id=8,
            is_on=filter_obj.high_speed,
        )


class TestPump:
    """Tests for Pump class."""

    def test_pump_properties_config(self, mock_omni, sample_pump_config, mock_telemetry):
        """Test that pump config properties are correctly exposed."""
        sample_pump_config.bow_id = 7
        pump_obj = Pump(mock_omni, sample_pump_config, mock_telemetry)

        assert pump_obj.equip_type == "PMP_VARIABLE_SPEED_PUMP"
        assert pump_obj.function == "PMP_PUMP"
        assert pump_obj.max_percent == 100
        assert pump_obj.min_percent == 30
        assert pump_obj.max_rpm == 3450
        assert pump_obj.min_rpm == 1000
        assert pump_obj.priming_enabled is True
        assert pump_obj.low_speed == 40
        assert pump_obj.medium_speed == 60
        assert pump_obj.high_speed == 80

    def test_pump_properties_telemetry(self, mock_omni, sample_pump_config, mock_telemetry):
        """Test that pump telemetry properties are correctly exposed."""
        sample_pump_config.bow_id = 7
        pump_obj = Pump(mock_omni, sample_pump_config, mock_telemetry)

        assert pump_obj.state == PumpState.ON
        assert pump_obj.speed == 60
        assert pump_obj.last_speed == 50
        assert pump_obj.why_on == 11

    def test_pump_is_on_true(self, mock_omni, sample_pump_config, mock_telemetry):
        """Test is_on returns True when pump is on."""
        sample_pump_config.bow_id = 7
        pump_obj = Pump(mock_omni, sample_pump_config, mock_telemetry)

        assert pump_obj.is_on is True

    def test_pump_is_on_false(self, mock_omni, sample_pump_config, mock_telemetry):
        """Test is_on returns False when pump is off."""
        sample_pump_config.bow_id = 7
        pump_obj = Pump(mock_omni, sample_pump_config, mock_telemetry)
        pump_obj.telemetry.state = PumpState.OFF

        assert pump_obj.is_on is False

    def test_pump_is_ready(self, mock_omni, sample_pump_config, mock_telemetry):
        """Test is_ready returns True for stable states."""
        sample_pump_config.bow_id = 7
        pump_obj = Pump(mock_omni, sample_pump_config, mock_telemetry)

        # ON state
        pump_obj.telemetry.state = PumpState.ON
        assert pump_obj.is_ready is True

        # OFF state
        pump_obj.telemetry.state = PumpState.OFF
        assert pump_obj.is_ready is True

    @pytest.mark.asyncio
    async def test_pump_turn_on(self, mock_omni, sample_pump_config, mock_telemetry):
        """Test turn_on method calls API correctly."""
        sample_pump_config.bow_id = 7
        pump_obj = Pump(mock_omni, sample_pump_config, mock_telemetry)
        pump_obj._api.async_set_equipment = AsyncMock()

        await pump_obj.turn_on()

        pump_obj._api.async_set_equipment.assert_called_once_with(
            pool_id=7,
            equipment_id=15,
            is_on=True,
        )

    @pytest.mark.asyncio
    async def test_pump_turn_off(self, mock_omni, sample_pump_config, mock_telemetry):
        """Test turn_off method calls API correctly."""
        sample_pump_config.bow_id = 7
        pump_obj = Pump(mock_omni, sample_pump_config, mock_telemetry)
        pump_obj._api.async_set_equipment = AsyncMock()

        await pump_obj.turn_off()

        pump_obj._api.async_set_equipment.assert_called_once_with(
            pool_id=7,
            equipment_id=15,
            is_on=False,
        )
