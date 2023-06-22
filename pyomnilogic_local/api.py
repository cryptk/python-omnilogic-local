from __future__ import annotations

import asyncio
import logging
from typing import Literal, overload
import xml.etree.ElementTree as ET

from .models.filter_diagnostics import FilterDiagnostics
from .models.mspconfig import MSPConfig
from .models.telemetry import Telemetry
from .models.util import to_pydantic
from .protocol import OmniLogicProtocol
from .types import (
    ColorLogicBrightness,
    ColorLogicShow,
    ColorLogicSpeed,
    HeaterMode,
    MessageType,
)

_LOGGER = logging.getLogger(__name__)


class OmniLogicAPI:
    def __init__(self, controller_ip: str, controller_port: int, response_timeout: float) -> None:
        self.controller_ip = controller_ip
        self.controller_port = controller_port
        self.response_timeout = response_timeout
        self._loop = asyncio.get_running_loop()
        self._protocol_factory = OmniLogicProtocol

    @overload
    async def async_send_message(self, message_type: MessageType, message: str | None, need_response: Literal[True]) -> str:
        ...

    @overload
    async def async_send_message(self, message_type: MessageType, message: str | None, need_response: Literal[False]) -> None:
        ...

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

    async def async_get_alarm_list(self) -> str:
        """Retrieve a list of alarms from the Omni.

        Returns:
            str: An XML body indicating any alarms that are present
        """
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "GetAllAlarmList"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.GET_ALARM_LIST, req_body, True)

    @to_pydantic(pydantic_type=MSPConfig)
    async def async_get_config(self) -> str:
        """Retrieve the MSPConfig from the Omni, optionally parse it into a pydantic model.

        Args:
            raw (bool): Do not parse the response into a Pydantic model, just return the raw XML. Defaults to False.

        Returns:
            MSPConfig|str: Either a parsed .models.mspconfig.MSPConfig object or a str depending on arg raw
        """
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "RequestConfiguration"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.REQUEST_CONFIGURATION, req_body, True)

    @to_pydantic(pydantic_type=FilterDiagnostics)
    async def async_get_filter_diagnostics(self, pool_id: int, equipment_id: int) -> str:
        """Retrieve filter diagnostics from the Omni, optionally parse it into a pydantic model.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address

        Returns:
            FilterDiagnostics|str: Either a parsed .models.mspconfig.FilterDiagnostics object or a str depending on arg raw
        """
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "GetUIFilterDiagnosticInfo"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="equipmentId", dataType="int")
        parameter.text = str(equipment_id)

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.GET_FILTER_DIAGNOSTIC_INFO, req_body, True)

    async def async_get_log_config(self) -> str:
        """Retrieve the logging configuration from the Omni.

        Returns:
            str: An XML body describing the logging configuration
        """
        return await self.async_send_message(MessageType.REQUEST_LOG_CONFIG, None, True)

    @to_pydantic(pydantic_type=Telemetry)
    async def async_get_telemetry(self) -> str:
        """Retrieve the current telemetry data from the Omni, optionally parse it into a pydantic model.

        Returns:
            Telemetry|str: Either a parsed .models.telemetry.Telemetry object or a str depending on arg raw
        """
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "RequestTelemetryData"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.GET_TELEMETRY, req_body, True)

    async def async_set_heater(self, pool_id: int, equipment_id: int, temperature: int, unit: str) -> None:
        """Set the temperature for a heater on the Omni

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            temperature (int): What temperature to request
            unit (str): The temperature unit to use (either F or C)

        Returns:
            None
        """
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetUIHeaterCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="HeaterID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Temp", dataType="int", unit=unit, alias="Data")
        parameter.text = str(temperature)

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.SET_HEATER_COMMAND, req_body, False)

    async def async_set_solar_heater(self, pool_id: int, equipment_id: int, temperature: int, unit: str) -> None:
        """Set the solar set point for a heater on the Omni.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            temperature (int): What temperature to request
            unit (str): The temperature unit to use (either F or C)

        Returns:
            None
        """
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetUISolarSetPointCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="HeaterID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Temp", dataType="int", unit=unit, alias="Data")
        parameter.text = str(temperature)

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.SET_SOLAR_SET_POINT_COMMAND, req_body, False)

    async def async_set_heater_mode(self, pool_id: int, equipment_id: int, mode: HeaterMode) -> None:
        """Set what mode (Heat/Cool/Auto) the heater should use.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            mode (HeaterMode): What mode should the heater operate under

        Returns:
            None
        """
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetUIHeaterModeCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="HeaterID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Mode", dataType="int", alias="Data")
        parameter.text = str(mode.value)

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.SET_HEATER_MODE_COMMAND, req_body, False)

    async def async_set_heater_enable(self, pool_id: int, equipment_id: int, enabled: int | bool) -> None:
        """async_set_heater_enable handles sending a SetHeaterEnable XML API call to the Hayward Omni pool controller

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            enabled (bool, optional): Turn the heater on (True) or off (False)

        Returns:
            _type_: _description_
        """
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetHeaterEnable"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="HeaterID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Enabled", dataType="bool", alias="Data")
        parameter.text = str(int(enabled))

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

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
            startTimeHours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            startTimeMinutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            endTimeHours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            endTimeMinutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            daysActive (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            recurring (bool, optional): For potential future use, included to be "API complete". Defaults to False.
        """
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

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

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.SET_EQUIPMENT, req_body, False)

    async def async_set_filter_speed(self, pool_id: int, equipment_id: int, speed: int) -> None:
        """Set the speed for a variable speed filter/pump.

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            speed (int): Speed value from 0-100 to set the filter to.  A value of 0 will turn the filter off.
        """
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

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

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.SET_FILTER_SPEED, req_body, False)

    async def async_set_light_show(
        self,
        pool_id: int,
        equipment_id: int,
        show: ColorLogicShow,
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
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

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

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")
        return await self.async_send_message(MessageType.SET_STANDALONE_LIGHT_SHOW, req_body, False)

    async def async_set_chlorinator_enable(self, pool_id: int, enabled: int | bool) -> None:
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetCHLOREnable"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="Enabled", dataType="bool", alias="Data")
        parameter.text = str(int(enabled))

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.SET_CHLOR_ENABLED, req_body, False)

    async def async_set_chlorinator_params(
        self,
        pool_id: int,
        equipment_id: int,
        timed_percent: int,
        cfg_state: int = 3,
        op_mode: int = 1,
        bow_type: int = 0,
        cell_type: int = 4,
        sc_timeout: int = 24,
        orp_timeout: int = 24,
    ) -> None:
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

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

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.SET_CHLOR_PARAMS, req_body, False)

    async def async_set_chlorinator_superchlorinate(self, pool_id: int, equipment_id: int, enabled: int | bool) -> None:
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "SetUISuperCHLORCmd"

        parameters_element = ET.SubElement(body_element, "Parameters")
        parameter = ET.SubElement(parameters_element, "Parameter", name="poolId", dataType="int")
        parameter.text = str(pool_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="ChlorID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipment_id)
        parameter = ET.SubElement(parameters_element, "Parameter", name="IsOn", dataType="byte", alias="Data1")
        parameter.text = str(int(enabled))

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.SET_SUPERCHLORINATE, req_body, False)

    async def async_restore_idle_state(self) -> None:
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "RestoreIdleState"

        ET.SubElement(body_element, "Parameters")

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.RESTORE_IDLE_STATE, req_body, False)
