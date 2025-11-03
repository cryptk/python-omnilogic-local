# pylint: skip-file
# type: ignore

"""
Comprehensive tests for the OmniLogic API layer.

Focuses on:
- Validation function tests (table-driven)
- API initialization tests
- XML message generation tests
- Transport/protocol integration tests
"""

from unittest.mock import AsyncMock, MagicMock, patch
from xml.etree import ElementTree as ET

import pytest
from pytest_subtests import SubTests

from pyomnilogic_local.api.api import (
    OmniLogicAPI,
    _validate_id,
    _validate_speed,
    _validate_temperature,
)
from pyomnilogic_local.api.constants import (
    MAX_SPEED_PERCENT,
    MAX_TEMPERATURE_F,
    MIN_SPEED_PERCENT,
    MIN_TEMPERATURE_F,
    XML_NAMESPACE,
)
from pyomnilogic_local.api.exceptions import OmniValidationException
from pyomnilogic_local.omnitypes import (
    ColorLogicBrightness,
    ColorLogicShow40,
    ColorLogicSpeed,
    HeaterMode,
)

# ============================================================================
# Helper Functions
# ============================================================================


def _get_xml_tag(element: ET.Element) -> str:
    """Strip namespace from XML tag for easier assertions."""
    return element.tag.split("}")[-1] if "}" in element.tag else element.tag


def _find_elem(root: ET.Element, path: str) -> ET.Element:
    """Find element with namespace support, raising if not found."""
    elem = root.find(f".//{{{XML_NAMESPACE}}}{path}")
    if elem is None:
        raise AssertionError(f"Element {path} not found in XML")
    return elem


def _find_param(root: ET.Element, name: str) -> ET.Element:
    """Find parameter by name attribute."""
    elem = root.find(f".//{{{XML_NAMESPACE}}}Parameter[@name='{name}']")
    if elem is None:
        raise AssertionError(f"Parameter {name} not found in XML")
    return elem


# ============================================================================
# Validation Function Tests (Table-Driven)
# ============================================================================


def test_validate_temperature(subtests: SubTests) -> None:
    """Test temperature validation with various inputs using table-driven approach."""
    test_cases = [
        # (temperature, param_name, should_pass, description)
        (MIN_TEMPERATURE_F, "temp", True, "minimum valid temperature"),
        (MAX_TEMPERATURE_F, "temp", True, "maximum valid temperature"),
        (80, "temp", True, "mid-range valid temperature"),
        (MIN_TEMPERATURE_F - 1, "temp", False, "below minimum temperature"),
        (MAX_TEMPERATURE_F + 1, "temp", False, "above maximum temperature"),
        ("80", "temp", False, "string instead of int"),
        (80.5, "temp", False, "float instead of int"),
        (None, "temp", False, "None value"),
    ]

    for temperature, param_name, should_pass, description in test_cases:
        with subtests.test(msg=description, temperature=temperature):
            if should_pass:
                _validate_temperature(temperature, param_name)  # Should not raise
            else:
                with pytest.raises(OmniValidationException):
                    _validate_temperature(temperature, param_name)


def test_validate_speed(subtests: SubTests) -> None:
    """Test speed validation with various inputs using table-driven approach."""
    test_cases = [
        # (speed, param_name, should_pass, description)
        (MIN_SPEED_PERCENT, "speed", True, "minimum valid speed (0)"),
        (MAX_SPEED_PERCENT, "speed", True, "maximum valid speed (100)"),
        (50, "speed", True, "mid-range valid speed"),
        (MIN_SPEED_PERCENT - 1, "speed", False, "below minimum speed"),
        (MAX_SPEED_PERCENT + 1, "speed", False, "above maximum speed"),
        ("50", "speed", False, "string instead of int"),
        (50.5, "speed", False, "float instead of int"),
        (None, "speed", False, "None value"),
    ]

    for speed, param_name, should_pass, description in test_cases:
        with subtests.test(msg=description, speed=speed):
            if should_pass:
                _validate_speed(speed, param_name)  # Should not raise
            else:
                with pytest.raises(OmniValidationException):
                    _validate_speed(speed, param_name)


def test_validate_id(subtests: SubTests) -> None:
    """Test ID validation with various inputs using table-driven approach."""
    test_cases = [
        # (id_value, param_name, should_pass, description)
        (0, "pool_id", True, "zero ID"),
        (1, "pool_id", True, "positive ID"),
        (999999, "pool_id", True, "large positive ID"),
        (-1, "pool_id", False, "negative ID"),
        ("1", "pool_id", False, "string instead of int"),
        (1.5, "pool_id", False, "float instead of int"),
        (None, "pool_id", False, "None value"),
    ]

    for id_value, param_name, should_pass, description in test_cases:
        with subtests.test(msg=description, id_value=id_value):
            if should_pass:
                _validate_id(id_value, param_name)  # Should not raise
            else:
                with pytest.raises(OmniValidationException):
                    _validate_id(id_value, param_name)


# ============================================================================
# OmniLogicAPI Constructor Tests
# ============================================================================


def test_api_init_valid() -> None:
    """Test OmniLogicAPI initialization with valid parameters."""
    api = OmniLogicAPI("192.168.1.100")
    assert api.controller_ip == "192.168.1.100"
    assert api.controller_port == 10444
    assert api.response_timeout == 5.0


def test_api_init_custom_params() -> None:
    """Test OmniLogicAPI initialization with custom parameters."""
    api = OmniLogicAPI("10.0.0.50", controller_port=12345, response_timeout=10.0)
    assert api.controller_ip == "10.0.0.50"
    assert api.controller_port == 12345
    assert api.response_timeout == 10.0


def test_api_init_validation(subtests: SubTests) -> None:
    """Test OmniLogicAPI initialization validation using table-driven approach."""
    test_cases = [
        # (ip, port, timeout, should_pass, description)
        ("", 10444, 5.0, False, "empty IP address"),
        ("192.168.1.100", 0, 5.0, False, "zero port"),
        ("192.168.1.100", -1, 5.0, False, "negative port"),
        ("192.168.1.100", 65536, 5.0, False, "port too high"),
        ("192.168.1.100", "10444", 5.0, False, "port as string"),
        ("192.168.1.100", 10444, 0, False, "zero timeout"),
        ("192.168.1.100", 10444, -1, False, "negative timeout"),
        ("192.168.1.100", 10444, "5.0", False, "timeout as string"),
    ]

    for ip, port, timeout, should_pass, description in test_cases:
        with subtests.test(msg=description):
            if should_pass:
                api = OmniLogicAPI(ip, port, timeout)
                assert api is not None
            else:
                with pytest.raises(OmniValidationException):
                    OmniLogicAPI(ip, port, timeout)


# ============================================================================
# Message Generation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_async_get_mspconfig_generates_valid_xml() -> None:
    """Test that async_get_mspconfig generates valid XML request."""
    api = OmniLogicAPI("192.168.1.100")

    with patch.object(api, "async_send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = '<?xml version="1.0"?><Response><Name>Configuration</Name></Response>'

        await api.async_get_mspconfig(raw=True)

        mock_send.assert_called_once()
        call_args = mock_send.call_args

        xml_payload = call_args[0][1]
        root = ET.fromstring(xml_payload)

        assert _get_xml_tag(root) == "Request"
        assert _find_elem(root, "Name").text == "RequestConfiguration"


@pytest.mark.asyncio
async def test_async_get_telemetry_generates_valid_xml() -> None:
    """Test that async_get_telemetry generates valid XML request."""
    api = OmniLogicAPI("192.168.1.100")

    with patch.object(api, "async_send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = '<?xml version="1.0"?><Response><Name>Telemetry</Name></Response>'

        await api.async_get_telemetry(raw=True)

        mock_send.assert_called_once()
        call_args = mock_send.call_args

        xml_payload = call_args[0][1]
        root = ET.fromstring(xml_payload)

        assert _get_xml_tag(root) == "Request"
        assert _find_elem(root, "Name").text == "RequestTelemetryData"


@pytest.mark.asyncio
async def test_async_get_filter_diagnostics_generates_valid_xml() -> None:
    """Test that async_get_filter_diagnostics generates valid XML with correct parameters."""
    api = OmniLogicAPI("192.168.1.100")

    with patch.object(api, "async_send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = '<?xml version="1.0"?><Response><Name>FilterDiagnostics</Name></Response>'

        await api.async_get_filter_diagnostics(pool_id=1, equipment_id=2, raw=True)

        mock_send.assert_called_once()
        call_args = mock_send.call_args

        xml_payload = call_args[0][1]
        root = ET.fromstring(xml_payload)

        assert _get_xml_tag(root) == "Request"
        assert _find_elem(root, "Name").text == "GetUIFilterDiagnosticInfo"
        assert _find_param(root, "poolId").text == "1"
        assert _find_param(root, "equipmentId").text == "2"


@pytest.mark.asyncio
async def test_async_set_heater_generates_valid_xml() -> None:
    """Test that async_set_heater generates valid XML with correct parameters."""
    api = OmniLogicAPI("192.168.1.100")

    with patch.object(api, "async_send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None

        await api.async_set_heater(pool_id=1, equipment_id=2, temperature=75)

        mock_send.assert_called_once()
        call_args = mock_send.call_args

        xml_payload = call_args[0][1]
        root = ET.fromstring(xml_payload)

        assert _get_xml_tag(root) == "Request"
        assert _find_elem(root, "Name").text == "SetUIHeaterCmd"
        assert _find_param(root, "poolId").text == "1"
        assert _find_param(root, "HeaterID").text == "2"
        temp_param = _find_param(root, "Temp")
        assert temp_param.text == "75"
        assert temp_param.get("unit") == "F"


@pytest.mark.asyncio
async def test_async_set_filter_speed_generates_valid_xml() -> None:
    """Test that async_set_filter_speed generates valid XML with correct parameters."""
    api = OmniLogicAPI("192.168.1.100")

    with patch.object(api, "async_send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None

        await api.async_set_filter_speed(pool_id=1, equipment_id=2, speed=75)

        mock_send.assert_called_once()
        call_args = mock_send.call_args

        xml_payload = call_args[0][1]
        root = ET.fromstring(xml_payload)

        assert _get_xml_tag(root) == "Request"
        assert _find_elem(root, "Name").text == "SetUIFilterSpeedCmd"
        assert _find_param(root, "poolId").text == "1"
        assert _find_param(root, "FilterID").text == "2"
        assert _find_param(root, "Speed").text == "75"


@pytest.mark.asyncio
async def test_async_set_equipment_generates_valid_xml() -> None:
    """Test that async_set_equipment generates valid XML with correct parameters."""
    api = OmniLogicAPI("192.168.1.100")

    with patch.object(api, "async_send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None

        await api.async_set_equipment(
            pool_id=1,
            equipment_id=2,
            is_on=True,
            is_countdown_timer=False,
            start_time_hours=10,
            start_time_minutes=30,
            end_time_hours=14,
            end_time_minutes=45,
            days_active=127,
            recurring=True,
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args

        xml_payload = call_args[0][1]
        root = ET.fromstring(xml_payload)

        assert _get_xml_tag(root) == "Request"
        assert _find_elem(root, "Name").text == "SetUIEquipmentCmd"

        # Verify all parameters
        assert _find_param(root, "poolId").text == "1"
        assert _find_param(root, "equipmentId").text == "2"
        assert _find_param(root, "isOn").text == "1"
        assert _find_param(root, "IsCountDownTimer").text == "0"
        assert _find_param(root, "StartTimeHours").text == "10"
        assert _find_param(root, "StartTimeMinutes").text == "30"
        assert _find_param(root, "EndTimeHours").text == "14"
        assert _find_param(root, "EndTimeMinutes").text == "45"
        assert _find_param(root, "DaysActive").text == "127"
        assert _find_param(root, "Recurring").text == "1"


@pytest.mark.asyncio
async def test_async_set_heater_mode_generates_valid_xml() -> None:
    """Test that async_set_heater_mode generates valid XML with correct enum values."""
    api = OmniLogicAPI("192.168.1.100")

    with patch.object(api, "async_send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None

        await api.async_set_heater_mode(pool_id=1, equipment_id=2, mode=HeaterMode.HEAT)

        mock_send.assert_called_once()
        call_args = mock_send.call_args

        xml_payload = call_args[0][1]
        root = ET.fromstring(xml_payload)

        assert _get_xml_tag(root) == "Request"
        assert _find_elem(root, "Name").text == "SetUIHeaterModeCmd"
        assert _find_param(root, "Mode").text == str(HeaterMode.HEAT.value)


@pytest.mark.asyncio
async def test_async_set_light_show_generates_valid_xml() -> None:
    """Test that async_set_light_show generates valid XML with correct enum values."""
    api = OmniLogicAPI("192.168.1.100")

    with patch.object(api, "async_send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None

        await api.async_set_light_show(
            pool_id=1,
            equipment_id=2,
            show=ColorLogicShow40.DEEP_BLUE_SEA,
            speed=ColorLogicSpeed.TWO_TIMES,
            brightness=ColorLogicBrightness.EIGHTY_PERCENT,
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args

        xml_payload = call_args[0][1]
        root = ET.fromstring(xml_payload)

        assert _get_xml_tag(root) == "Request"
        assert _find_elem(root, "Name").text == "SetStandAloneLightShow"
        assert _find_param(root, "poolId").text == "1"
        assert _find_param(root, "LightID").text == "2"
        assert _find_param(root, "Show").text == str(ColorLogicShow40.DEEP_BLUE_SEA.value)
        assert _find_param(root, "Speed").text == str(ColorLogicSpeed.TWO_TIMES.value)
        assert _find_param(root, "Brightness").text == str(ColorLogicBrightness.EIGHTY_PERCENT.value)


@pytest.mark.asyncio
async def test_async_set_chlorinator_enable_boolean_conversion(subtests: SubTests) -> None:
    """Test that async_set_chlorinator_enable properly converts boolean to int."""
    api = OmniLogicAPI("192.168.1.100")

    test_cases = [
        (True, "1", "boolean True"),
        (False, "0", "boolean False"),
        (1, "1", "int 1"),
        (0, "0", "int 0"),
    ]

    for enabled, expected, description in test_cases:
        with subtests.test(msg=description):
            with patch.object(api, "async_send_message", new_callable=AsyncMock) as mock_send:
                mock_send.return_value = None

                await api.async_set_chlorinator_enable(pool_id=1, enabled=enabled)

                call_args = mock_send.call_args
                xml_payload = call_args[0][1]
                root = ET.fromstring(xml_payload)

                assert _find_param(root, "Enabled").text == expected


@pytest.mark.asyncio
async def test_async_set_heater_enable_boolean_conversion(subtests: SubTests) -> None:
    """Test that async_set_heater_enable properly converts boolean to int."""
    api = OmniLogicAPI("192.168.1.100")

    test_cases = [
        (True, "1", "boolean True"),
        (False, "0", "boolean False"),
        (1, "1", "int 1"),
        (0, "0", "int 0"),
    ]

    for enabled, expected, description in test_cases:
        with subtests.test(msg=description):
            with patch.object(api, "async_send_message", new_callable=AsyncMock) as mock_send:
                mock_send.return_value = None

                await api.async_set_heater_enable(pool_id=1, equipment_id=2, enabled=enabled)

                call_args = mock_send.call_args
                xml_payload = call_args[0][1]
                root = ET.fromstring(xml_payload)

                assert _find_param(root, "Enabled").text == expected


@pytest.mark.asyncio
async def test_async_set_chlorinator_params_generates_valid_xml() -> None:
    """Test that async_set_chlorinator_params generates valid XML with all parameters."""
    api = OmniLogicAPI("192.168.1.100")

    with patch.object(api, "async_send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None

        await api.async_set_chlorinator_params(
            pool_id=1,
            equipment_id=2,
            timed_percent=50,
            cell_type=3,
            op_mode=1,
            sc_timeout=24,
            bow_type=0,
            orp_timeout=12,
            cfg_state=3,
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args

        xml_payload = call_args[0][1]
        root = ET.fromstring(xml_payload)

        assert _get_xml_tag(root) == "Request"
        assert _find_elem(root, "Name").text == "SetCHLORParams"

        # Verify all parameters
        assert _find_param(root, "poolId").text == "1"
        assert _find_param(root, "ChlorID").text == "2"
        assert _find_param(root, "CfgState").text == "3"
        assert _find_param(root, "OpMode").text == "1"
        assert _find_param(root, "BOWType").text == "0"
        assert _find_param(root, "CellType").text == "3"
        assert _find_param(root, "TimedPercent").text == "50"
        assert _find_param(root, "SCTimeout").text == "24"
        assert _find_param(root, "ORPTimout").text == "12"


# ============================================================================
# async_send_message Tests
# ============================================================================


@pytest.mark.asyncio
async def test_async_send_message_creates_transport() -> None:
    """Test that async_send_message creates a UDP transport."""
    api = OmniLogicAPI("192.168.1.100", controller_port=10444)

    mock_transport = MagicMock()
    mock_protocol = AsyncMock()
    mock_protocol.send_message = AsyncMock()

    with patch("asyncio.get_running_loop") as mock_loop:
        mock_loop.return_value.create_datagram_endpoint = AsyncMock(return_value=(mock_transport, mock_protocol))

        await api.async_send_message(0x01, "test", need_response=False)

        # Verify endpoint was created with correct parameters
        mock_loop.return_value.create_datagram_endpoint.assert_called_once()
        call_kwargs = mock_loop.return_value.create_datagram_endpoint.call_args[1]
        assert call_kwargs["remote_addr"] == ("192.168.1.100", 10444)

        # Verify transport was closed
        mock_transport.close.assert_called_once()


@pytest.mark.asyncio
async def test_async_send_message_with_response() -> None:
    """Test that async_send_message with need_response=True calls send_and_receive."""
    api = OmniLogicAPI("192.168.1.100")

    mock_transport = MagicMock()
    mock_protocol = AsyncMock()
    mock_protocol.send_and_receive = AsyncMock(return_value="test response")

    with patch("asyncio.get_running_loop") as mock_loop:
        mock_loop.return_value.create_datagram_endpoint = AsyncMock(return_value=(mock_transport, mock_protocol))

        result = await api.async_send_message(0x01, "test", need_response=True)

        assert result == "test response"
        mock_protocol.send_and_receive.assert_called_once()
        mock_transport.close.assert_called_once()


@pytest.mark.asyncio
async def test_async_send_message_without_response() -> None:
    """Test that async_send_message with need_response=False calls send_message."""
    api = OmniLogicAPI("192.168.1.100")

    mock_transport = MagicMock()
    mock_protocol = AsyncMock()
    mock_protocol.send_message = AsyncMock()

    with patch("asyncio.get_running_loop") as mock_loop:
        mock_loop.return_value.create_datagram_endpoint = AsyncMock(return_value=(mock_transport, mock_protocol))

        result = await api.async_send_message(0x01, "test", need_response=False)

        assert result is None
        mock_protocol.send_message.assert_called_once()
        mock_transport.close.assert_called_once()


@pytest.mark.asyncio
async def test_async_send_message_closes_transport_on_error() -> None:
    """Test that async_send_message closes transport even when an error occurs."""
    api = OmniLogicAPI("192.168.1.100")

    mock_transport = MagicMock()
    mock_protocol = AsyncMock()
    mock_protocol.send_message = AsyncMock(side_effect=Exception("Test error"))

    with patch("asyncio.get_running_loop") as mock_loop:
        mock_loop.return_value.create_datagram_endpoint = AsyncMock(return_value=(mock_transport, mock_protocol))

        with pytest.raises(Exception, match="Test error"):
            await api.async_send_message(0x01, "test", need_response=False)

        # Verify transport was still closed despite the error
        mock_transport.close.assert_called_once()
