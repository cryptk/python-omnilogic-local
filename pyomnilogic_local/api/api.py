from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Literal, overload

from pyomnilogic_local.models.filter_diagnostics import FilterDiagnostics
from pyomnilogic_local.models.mspconfig import MSPConfig
from pyomnilogic_local.models.telemetry import Telemetry
from pyomnilogic_local.omnitypes import (
    ColorLogicBrightness,
    ColorLogicSpeed,
    MessageType,
)

from .constants import (
    DEFAULT_CONTROLLER_PORT,
    DEFAULT_RESPONSE_TIMEOUT,
    MAX_SPEED_PERCENT,
    MAX_TEMPERATURE_F,
    MIN_SPEED_PERCENT,
    MIN_TEMPERATURE_F,
    XML_ENCODING,
    XML_NAMESPACE,
)
from .exceptions import OmniValidationError
from .protocol import OmniLogicProtocol

if TYPE_CHECKING:
    from pyomnilogic_local.omnitypes import HeaterMode, LightShows

_LOGGER = logging.getLogger(__name__)


def _validate_temperature(temperature: int, param_name: str = "temperature") -> None:
    """Validate temperature is within acceptable range.

    Args:
        temperature: Temperature value in Fahrenheit.
        param_name: Name of the parameter for error messages.

    Raises:
        OmniValidationException: If temperature is out of range.
    """
    if not isinstance(temperature, int):
        msg = f"{param_name} must be an integer, got {type(temperature).__name__}"
        raise OmniValidationError(msg)
    if not MIN_TEMPERATURE_F <= temperature <= MAX_TEMPERATURE_F:
        msg = f"{param_name} must be between {MIN_TEMPERATURE_F}°F and {MAX_TEMPERATURE_F}°F, got {temperature}°F"
        raise OmniValidationError(msg)


def _validate_speed(speed: int, param_name: str = "speed") -> None:
    """Validate speed percentage is within acceptable range.

    Args:
        speed: Speed percentage (0-100).
        param_name: Name of the parameter for error messages.

    Raises:
        OmniValidationException: If speed is out of range.
    """
    if not isinstance(speed, int):
        msg = f"{param_name} must be an integer, got {type(speed).__name__}"
        raise OmniValidationError(msg)
    if not MIN_SPEED_PERCENT <= speed <= MAX_SPEED_PERCENT:
        msg = f"{param_name} must be between {MIN_SPEED_PERCENT} and {MAX_SPEED_PERCENT}, got {speed}"
        raise OmniValidationError(msg)


def _validate_id(id_value: int, param_name: str) -> None:
    """Validate an ID is a positive integer.

    Args:
        id_value: The ID value to validate.
        param_name: Name of the parameter for error messages.

    Raises:
        OmniValidationException: If ID is invalid.
    """
    if not isinstance(id_value, int):
        msg = f"{param_name} must be an integer, got {type(id_value).__name__}"
        raise OmniValidationError(msg)
    if id_value < 0:
        msg = f"{param_name} must be non-negative, got {id_value}"
        raise OmniValidationError(msg)


class OmniLogicAPI:
    def __init__(
        self, controller_ip: str, controller_port: int = DEFAULT_CONTROLLER_PORT, response_timeout: float = DEFAULT_RESPONSE_TIMEOUT
    ) -> None:
        """Initialize the OmniLogic API client.

        Args:
            controller_ip: IP address of the OmniLogic controller.
            controller_port: UDP port of the OmniLogic controller (default: 10444).
            response_timeout: Timeout in seconds for receiving responses (default: 5.0).

        Raises:
            OmniValidationException: If parameters are invalid.
        """
        if not controller_ip:
            msg = "controller_ip cannot be empty"
            raise OmniValidationError(msg)
        if not isinstance(controller_port, int) or controller_port <= 0 or controller_port > 65535:
            msg = f"controller_port must be between 1 and 65535, got {controller_port}"
            raise OmniValidationError(msg)
        if not isinstance(response_timeout, (int, float)) or response_timeout <= 0:
            msg = f"response_timeout must be positive, got {response_timeout}"
            raise OmniValidationError(msg)

        self.controller_ip = controller_ip
        self.controller_port = controller_port
        self.response_timeout = response_timeout

    @overload
    async def async_send_message(self, message_type: MessageType, message: str | None, need_response: Literal[True]) -> str: ...

    @overload
    async def async_send_message(self, message_type: MessageType, message: str | None, need_response: Literal[False]) -> None: ...

    async def async_send_message(self, message_type: MessageType, message: str | None, need_response: bool = False) -> str | None:
        """Send a message via the Hayward Omni UDP protocol along with properly handling timeouts and responses.

        Args:
            message_type (MessageType): A selection from MessageType indicating what type of communication you are sending
            message (str | None): The XML body of the message to deliver
            need_response (bool, optional): Should a response be received and returned to the caller. Defaults to False.

        Returns:
            str | None: The response body sent from the Omni if need_response indicates that a response will be sent
        """
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(OmniLogicProtocol, remote_addr=(self.controller_ip, self.controller_port))

        resp: str | None = None
        try:
            if need_response:
                resp = await protocol.send_and_receive(message_type, message)
            else:
                await protocol.send_message(message_type, message)
        finally:
            transport.close()

        return resp

    @overload
    async def async_get_mspconfig(self, raw: Literal[True]) -> str: ...
    @overload
    async def async_get_mspconfig(self, raw: Literal[False]) -> MSPConfig: ...
    @overload
    async def async_get_mspconfig(self) -> MSPConfig: ...
    async def async_get_mspconfig(self, raw: bool = False) -> MSPConfig | str:
        """Retrieve the MSPConfig from the Omni, optionally parse it into a pydantic model.

        Args:
            raw (bool): Do not parse the response into a Pydantic model, just return the raw XML. Defaults to False.

        Returns:
            MSPConfig|str: Either a parsed .models.mspconfig.MSPConfig object or a str depending on arg raw
        """
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "RequestConfiguration"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        resp = await self.async_send_message(MessageType.REQUEST_CONFIGURATION, req_body, True)

        if raw:
            return resp
        return MSPConfig.load_xml(resp)

    @overload
    async def async_get_filter_diagnostics(self, pool_id: int, equipment_id: int, raw: Literal[True]) -> str: ...
    @overload
    async def async_get_filter_diagnostics(self, pool_id: int, equipment_id: int, raw: Literal[False]) -> FilterDiagnostics: ...
    @overload
    async def async_get_filter_diagnostics(self, pool_id: int, equipment_id: int) -> FilterDiagnostics: ...
    @overload
    async def async_get_filter_diagnostics(self, pool_id: int, equipment_id: int, raw: bool) -> FilterDiagnostics | str: ...
    async def async_get_filter_diagnostics(self, pool_id: int, equipment_id: int, raw: bool = False) -> FilterDiagnostics | str:
        """Retrieve filter diagnostics from the Omni, optionally parse it into a pydantic model.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            raw (bool): Do not parse the response into a Pydantic model, just return the raw XML. Defaults to False.

        Returns:
            FilterDiagnostics|str: Either a parsed .models.mspconfig.FilterDiagnostics object or a str depending on arg raw
        """
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "GetUIFilterDiagnosticInfo"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="equipmentId", dataType="int")
        parameter.text = str(equipment_id)

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        resp = await self.async_send_message(MessageType.GET_FILTER_DIAGNOSTIC_INFO, req_body, True)

        if raw:
            return resp
        return FilterDiagnostics.load_xml(resp)

    @overload
    async def async_get_telemetry(self, raw: Literal[True]) -> str: ...
    @overload
    async def async_get_telemetry(self, raw: Literal[False]) -> Telemetry: ...
    @overload
    async def async_get_telemetry(self) -> Telemetry: ...
    async def async_get_telemetry(self, raw: bool = False) -> Telemetry | str:
        """Retrieve the current telemetry data from the Omni, optionally parse it into a pydantic model.

        Returns:
            Telemetry|str: Either a parsed .models.telemetry.Telemetry object or a str depending on arg raw
        """
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "RequestTelemetryData"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        resp = await self.async_send_message(MessageType.GET_TELEMETRY, req_body, True)

        if raw:
            return resp
        return Telemetry.load_xml(resp)

    async def async_set_heater(
        self,
        pool_id: int,
        equipment_id: int,
        temperature: int,
    ) -> None:
        """Set the temperature for a heater on the Omni.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            temperature (int): What temperature to request (must be in Fahrenheit)

        Returns:
            None
        """
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetUIHeaterCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="HeaterID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Temp", dataType="int", unit="F", alias="Data")
        parameter.text = str(temperature)

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.SET_HEATER_COMMAND, req_body, False)

    async def async_set_solar_heater(
        self,
        pool_id: int,
        equipment_id: int,
        temperature: int,
    ) -> None:
        """Set the solar set point for a heater on the Omni.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            temperature (int): What temperature to request (must be in Fahrenheit)

        Returns:
            None
        """
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetUISolarSetPointCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="HeaterID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Temp", dataType="int", unit="F", alias="Data")
        parameter.text = str(temperature)

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.SET_SOLAR_SET_POINT_COMMAND, req_body, False)

    async def async_set_heater_mode(
        self,
        pool_id: int,
        equipment_id: int,
        mode: HeaterMode,
    ) -> None:
        """Set what mode (Heat/Cool/Auto) the heater should use.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            mode (HeaterMode): What mode should the heater operate under

        Returns:
            None
        """
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetUIHeaterModeCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="HeaterID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Mode", dataType="int", alias="Data")
        parameter.text = str(mode.value)

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.SET_HEATER_MODE_COMMAND, req_body, False)

    async def async_set_heater_enable(
        self,
        pool_id: int,
        equipment_id: int,
        enabled: int | bool,
    ) -> None:
        """Send a SetHeaterEnable XML API call to the Hayward Omni pool controller.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            enabled (bool, optional): Turn the heater on (True) or off (False)

        Returns:
            _type_: _description_
        """
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetHeaterEnable"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="HeaterID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Enabled", dataType="bool", alias="Data")
        parameter.text = str(int(enabled))

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.SET_HEATER_ENABLED, req_body, False)

    async def async_set_equipment(
        self,
        pool_id: int,
        equipment_id: int,
        is_on: int | bool,
        is_countdown_timer: bool = False,
        start_time_hours: int = 0,
        start_time_minutes: int = 0,
        end_time_hours: int = 0,
        end_time_minutes: int = 0,
        days_active: int = 0,
        recurring: bool = False,
    ) -> None:
        """Control a piece of equipment, turning it on/off or setting a value (E.g.: filter speed), optionally scheduling it.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            is_on (Union[int,bool]): For most equipment items, True/False to turn on/off.
                For Variable Speed Pumps, you can optionally provide an int from 0-100 to set the speed percentage with 0 being Off.
                The interpretation of value depends on the piece of equipment being targeted.
            is_countdown_timer (bool, optional): For potential future use, included to be "API complete". Defaults to False.
            start_time_hours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            start_time_minutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            end_time_hours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            end_time_minutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            days_active (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            recurring (bool, optional): For potential future use, included to be "API complete". Defaults to False.
        """
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetUIEquipmentCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="equipmentId", dataType="int")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="isOn", dataType="int", alias="Data")
        parameter.text = str(int(is_on))
        parameter = ET.SubElement(parameters_element, "Parameter", name="IsCountDownTimer", dataType="bool")
        parameter.text = str(int(is_countdown_timer))
        parameter = ET.SubElement(parameters_element, "Parameter", name="StartTimeHours", dataType="int")
        parameter.text = str(start_time_hours)
        parameter = ET.SubElement(parameters_element, "Parameter", name="StartTimeMinutes", dataType="int")
        parameter.text = str(start_time_minutes)
        parameter = ET.SubElement(parameters_element, "Parameter", name="EndTimeHours", dataType="int")
        parameter.text = str(end_time_hours)
        parameter = ET.SubElement(parameters_element, "Parameter", name="EndTimeMinutes", dataType="int")
        parameter.text = str(end_time_minutes)
        parameter = ET.SubElement(parameters_element, "Parameter", name="DaysActive", dataType="int")
        parameter.text = str(days_active)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Recurring", dataType="bool")
        parameter.text = str(int(recurring))

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.SET_EQUIPMENT, req_body, False)

    async def async_set_filter_speed(self, pool_id: int, equipment_id: int, speed: int) -> None:
        """Set the speed for a variable speed filter/pump.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            speed (int): Speed value from 0-100 to set the filter to.  A value of 0 will turn the filter off.
        """
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetUIFilterSpeedCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="FilterID", dataType="int", alias="equipment_id")
        parameter.text = str(equipment_id)
        # NOTE: Despite the API calling it RPM here, the speed value is a percentage from 1-100
        parameter = ET.SubElement(parameters_element, "Parameter", name="Speed", dataType="int", unit="RPM", alias="Data")
        parameter.text = str(speed)

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.SET_FILTER_SPEED, req_body, False)

    async def async_set_light_show(
        self,
        pool_id: int,
        equipment_id: int,
        show: LightShows,
        speed: ColorLogicSpeed = ColorLogicSpeed.ONE_TIMES,
        brightness: ColorLogicBrightness = ColorLogicBrightness.ONE_HUNDRED_PERCENT,
        reserved: int = 0,
        is_countdown_timer: bool = False,
        start_time_hours: int = 0,
        start_time_minutes: int = 0,
        end_time_hours: int = 0,
        end_time_minutes: int = 0,
        days_active: int = 0,
        recurring: bool = False,
    ) -> None:
        """Set the desired light show/speed/brightness for a ColorLogic light.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            show (ColorLogicShow): ColorLogicShow to set the light to
            speed (ColorLogicSpeed, optional): Speed to animate the show. Defaults to 4.  0-8 which map to:
            brightness (ColorLogicBrightness, optional): How bright should the light be. Defaults to 4. 0-4 which map to:
            reserved (int, optional): Reserved. Defaults to 0.
            is_countdown_timer (bool, optional): For potential future use, included to be "API complete". Defaults to False.
            start_time_hours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            start_time_minutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            end_time_hours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            end_time_minutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            days_active (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            recurring (bool, optional): For potential future use, included to be "API complete". Defaults to False.
        """
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetStandAloneLightShow"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="LightID", dataType="int", alias="equipment_id")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Show", dataType="byte")
        parameter.text = str(show.value)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Speed", dataType="byte")
        parameter.text = str(speed.value)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Brightness", dataType="byte")
        parameter.text = str(brightness.value)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Reserved", dataType="byte")
        parameter.text = str(reserved)
        parameter = ET.SubElement(parameters_element, "Parameter", name="IsCountDownTimer", dataType="bool")
        parameter.text = str(int(is_countdown_timer))
        parameter = ET.SubElement(parameters_element, "Parameter", name="StartTimeHours", dataType="int")
        parameter.text = str(start_time_hours)
        parameter = ET.SubElement(parameters_element, "Parameter", name="StartTimeMinutes", dataType="int")
        parameter.text = str(start_time_minutes)
        parameter = ET.SubElement(parameters_element, "Parameter", name="EndTimeHours", dataType="int")
        parameter.text = str(end_time_hours)
        parameter = ET.SubElement(parameters_element, "Parameter", name="EndTimeMinutes", dataType="int")
        parameter.text = str(end_time_minutes)
        parameter = ET.SubElement(parameters_element, "Parameter", name="DaysActive", dataType="int")
        parameter.text = str(days_active)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Recurring", dataType="bool")
        parameter.text = str(int(recurring))

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)
        return await self.async_send_message(MessageType.SET_STANDALONE_LIGHT_SHOW, req_body, False)

    async def async_set_chlorinator_enable(self, pool_id: int, enabled: int | bool) -> None:
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetCHLOREnable"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Enabled", dataType="bool", alias="Data")
        parameter.text = str(int(enabled))

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.SET_CHLOR_ENABLED, req_body, False)

    async def async_set_chlorinator_params(
        self,
        pool_id: int,
        equipment_id: int,
        timed_percent: int,
        cell_type: int,
        op_mode: int,
        sc_timeout: int,
        bow_type: int,
        orp_timeout: int,
        cfg_state: int = 3,
    ) -> None:
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetCHLORParams"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="ChlorID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="CfgState", dataType="byte", alias="Data1")
        parameter.text = str(cfg_state)
        parameter = ET.SubElement(parameters_element, "Parameter", name="OpMode", dataType="byte", alias="Data2")
        parameter.text = str(op_mode)
        parameter = ET.SubElement(parameters_element, "Parameter", name="BOWType", dataType="byte", alias="Data3")
        parameter.text = str(bow_type)
        parameter = ET.SubElement(parameters_element, "Parameter", name="CellType", dataType="byte", alias="Data4")
        parameter.text = str(cell_type)
        parameter = ET.SubElement(parameters_element, "Parameter", name="TimedPercent", dataType="byte", alias="Data5")
        parameter.text = str(timed_percent)
        parameter = ET.SubElement(parameters_element, "Parameter", name="SCTimeout", dataType="byte", unit="hour", alias="Data6")
        parameter.text = str(sc_timeout)
        parameter = ET.SubElement(parameters_element, "Parameter", name="ORPTimout", dataType="byte", unit="hour", alias="Data7")
        parameter.text = str(orp_timeout)

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.SET_CHLOR_PARAMS, req_body, False)

    async def async_set_chlorinator_superchlorinate(
        self,
        pool_id: int,
        equipment_id: int,
        enabled: int | bool,
    ) -> None:
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetUISuperCHLORCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="ChlorID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="IsOn", dataType="byte", alias="Data1")
        parameter.text = str(int(enabled))

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.SET_SUPERCHLORINATE, req_body, False)

    async def async_restore_idle_state(self) -> None:
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "RestoreIdleState"

        ET.SubElement(body_element, "Parameters")

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.RESTORE_IDLE_STATE, req_body, False)

    async def async_set_spillover(
        self,
        pool_id: int,
        speed: int,
        is_countdown_timer: bool = False,
        start_time_hours: int = 0,
        start_time_minutes: int = 0,
        end_time_hours: int = 0,
        end_time_minutes: int = 0,
        days_active: int = 0,
        recurring: bool = False,
    ) -> None:
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetUISpilloverCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Speed", dataType="int")
        parameter.text = str(speed)
        parameter = ET.SubElement(parameters_element, "Parameter", name="IsCountDownTimer", dataType="bool")
        parameter.text = str(int(is_countdown_timer))
        parameter = ET.SubElement(parameters_element, "Parameter", name="StartTimeHours", dataType="int")
        parameter.text = str(start_time_hours)
        parameter = ET.SubElement(parameters_element, "Parameter", name="StartTimeMinutes", dataType="int")
        parameter.text = str(start_time_minutes)
        parameter = ET.SubElement(parameters_element, "Parameter", name="EndTimeHours", dataType="int")
        parameter.text = str(end_time_hours)
        parameter = ET.SubElement(parameters_element, "Parameter", name="EndTimeMinutes", dataType="int")
        parameter.text = str(end_time_minutes)
        parameter = ET.SubElement(parameters_element, "Parameter", name="DaysActive", dataType="int")
        parameter.text = str(days_active)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Recurring", dataType="bool")
        parameter.text = str(int(recurring))

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.SET_SPILLOVER, req_body, False)

    async def async_set_group_enable(
        self,
        group_id: int,
        enabled: int | bool,
        is_countdown_timer: bool = False,
        start_time_hours: int = 0,
        start_time_minutes: int = 0,
        end_time_hours: int = 0,
        end_time_minutes: int = 0,
        days_active: int = 0,
        recurring: bool = False,
    ) -> None:
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "RunGroupCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="GroupID", dataType="int")
        parameter.text = str(group_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Data", dataType="int")
        parameter.text = str(int(enabled))
        parameter = ET.SubElement(parameters_element, "Parameter", name="IsCountDownTimer", dataType="bool")
        parameter.text = str(int(is_countdown_timer))
        parameter = ET.SubElement(parameters_element, "Parameter", name="StartTimeHours", dataType="int")
        parameter.text = str(start_time_hours)
        parameter = ET.SubElement(parameters_element, "Parameter", name="StartTimeMinutes", dataType="int")
        parameter.text = str(start_time_minutes)
        parameter = ET.SubElement(parameters_element, "Parameter", name="EndTimeHours", dataType="int")
        parameter.text = str(end_time_hours)
        parameter = ET.SubElement(parameters_element, "Parameter", name="EndTimeMinutes", dataType="int")
        parameter.text = str(end_time_minutes)
        parameter = ET.SubElement(parameters_element, "Parameter", name="DaysActive", dataType="int")
        parameter.text = str(days_active)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Recurring", dataType="bool")
        parameter.text = str(int(recurring))

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.RUN_GROUP_CMD, req_body, False)

    async def async_edit_schedule(
        self,
        equipment_id: int,
        data: int,
        action_id: int,
        start_time_hours: int,
        start_time_minutes: int,
        end_time_hours: int,
        end_time_minutes: int,
        days_active: int,
        is_enabled: bool,
        recurring: bool,
    ) -> None:
        """Edit an existing schedule on the Omni.

        Args:
            equipment_id (int): The schedule's system ID (schedule-system-id from MSPConfig), NOT the equipment-id.
            data (int): The data value for the schedule action (e.g., 50 for 50% speed, 1 for on, 0 for off).
            action_id (int): The action/event ID that will be executed (e.g., 164 for SetUIEquipmentCmd).
                Maps to the 'event' field in the schedule. Common values:
                - 164: SetUIEquipmentCmd (turn equipment on/off or set speed)
                - 308: SetStandAloneLightShow
                - 311: SetUISpilloverCmd
            start_time_hours (int): Hour to start the schedule (0-23). Maps to 'start-hour'.
            start_time_minutes (int): Minute to start the schedule (0-59). Maps to 'start-minute'.
            end_time_hours (int): Hour to end the schedule (0-23). Maps to 'end-hour'.
            end_time_minutes (int): Minute to end the schedule (0-59). Maps to 'end-minute'.
            days_active (int): Bitmask of active days. Maps to 'days-active'.
                1=Monday, 2=Tuesday, 4=Wednesday, 8=Thursday, 16=Friday, 32=Saturday, 64=Sunday
                127=All days (1+2+4+8+16+32+64)
            is_enabled (bool): Whether the schedule is enabled. Maps to 'enabled' (0 or 1).
            recurring (bool): Whether the schedule repeats. Maps to 'recurring' (0 or 1).

        Returns:
            None

        Note:
            The schedule's equipment-id (which equipment is controlled) cannot be changed via this call.
            Only the schedule parameters (timing, data, enabled state) can be modified.
        """
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "EditUIScheduleCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="EquipmentID", dataType="int")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Data", dataType="int")
        parameter.text = str(data)
        parameter = ET.SubElement(parameters_element, "Parameter", name="ActionID", dataType="int")
        parameter.text = str(action_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="StartTimeHours", dataType="int")
        parameter.text = str(start_time_hours)
        parameter = ET.SubElement(parameters_element, "Parameter", name="StartTimeMinutes", dataType="int")
        parameter.text = str(start_time_minutes)
        parameter = ET.SubElement(parameters_element, "Parameter", name="EndTimeHours", dataType="int")
        parameter.text = str(end_time_hours)
        parameter = ET.SubElement(parameters_element, "Parameter", name="EndTimeMinutes", dataType="int")
        parameter.text = str(end_time_minutes)
        parameter = ET.SubElement(parameters_element, "Parameter", name="DaysActive", dataType="int")
        parameter.text = str(days_active)
        parameter = ET.SubElement(parameters_element, "Parameter", name="IsEnabled", dataType="bool")
        parameter.text = str(int(is_enabled))
        parameter = ET.SubElement(parameters_element, "Parameter", name="Recurring", dataType="bool")
        parameter.text = str(int(recurring))

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)

        return await self.async_send_message(MessageType.EDIT_SCHEDULE, req_body, False)
