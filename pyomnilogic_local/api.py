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
from .types import ColorLogicBrightness, ColorLogicShow, ColorLogicSpeed, MessageType

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
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(OmniLogicProtocol, remote_addr=(self.controller_ip, self.controller_port))

        resp: str | None = None
        try:
            if need_response:
                resp = await asyncio.wait_for(protocol.send_and_receive(message_type, message), self.response_timeout)
            else:
                await asyncio.wait_for(protocol.send_message(message_type, message), self.response_timeout)
        finally:
            transport.close()

        return resp

    async def async_get_alarm_list(self) -> str:
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "GetAllAlarmList"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.GET_ALARM_LIST, req_body, True)

    @to_pydantic(pydantic_type=MSPConfig)
    async def async_get_config(self) -> str:
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "RequestConfiguration"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.REQUEST_CONFIGURATION, req_body, True)

    @to_pydantic(pydantic_type=FilterDiagnostics)
    async def async_get_filter_diagnostics(self, pool_id: int, equipment_id: int) -> str:
        """async_get_filter_diagnostics handles sending a GetUIFilterDiagnosticInfo XML API call to the Hayward Omni pool controller

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address

        Returns:
            _type_: _description_
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
        return await self.async_send_message(MessageType.REQUEST_LOG_CONFIG, None, True)

    @to_pydantic(pydantic_type=Telemetry)
    async def async_get_telemetry(self) -> str:
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "RequestTelemetryData"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")

        return await self.async_send_message(MessageType.GET_TELEMETRY, req_body, True)

    async def async_set_heater(self, pool_id: int, equipment_id: int, temperature: int, unit: str) -> None:
        """async_set_heater handles sending a SetUIHeaterCmd XML API call to the Hayward Omni pool controller

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            temperature (int): What temperature to request
            unit (str): The temperature unit to use (either F or C)

        Returns:
            _type_: _description_
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
        """async_set_heater handles sending a SetUIHeaterCmd XML API call to the Hayward Omni pool controller

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            temperature (int): What temperature to request
            unit (str): The temperature unit to use (either F or C)

        Returns:
            _type_: _description_
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
        """async_set_equipment handles sending a SetUIEquipmentCmd XML API call to the Hayward Omni pool controller

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            is_on (Union[int,bool]): For most equipment items, True/False to turn on/off.
                For Variable Speed Pumps, you can optionally provide an int from 0-100 to set the speed percentage with 0 being Off.
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
        parameter = ET.SubElement(parameters_element, "Parameter", name="isOn", dataType="int")
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
        """async_set_filter_speed handles sending a SetUIFilterSpeedCmd XML API call to the Hayward Omni pool controller

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
        """async_set_light_show handles sending a SetStandAloneLightShow XML API call to the Hayward Omni pool controller

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
