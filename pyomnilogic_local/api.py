import asyncio
import logging
import random
import struct
import time
from typing import Union
import xml.etree.ElementTree as ET
import zlib

from .types import ColorLogicBrightness, ColorLogicShow, ColorLogicSpeed, MessageType


class OmniLogicRequest:
    HEADER_FORMAT = "!LQ4sLBBBB"

    def __init__(self, msg_id, msg_type: MessageType, extra_data="", client_type=1):
        self.msg_id = msg_id
        self.msg_type = msg_type
        self.client_type = client_type
        self.extra_data = bytes(extra_data, "utf-8")
        # self.extra_data = extra_data

        self.version = "1.19".encode("ascii")

    def to_bytes(self):
        retval = struct.pack(
            OmniLogicRequest.HEADER_FORMAT,
            self.msg_id,  # Msg id
            int(time.time_ns() / (10**9)),  # Timestamp
            bytes(self.version),  # version string
            self.msg_type.value,  # OpID/msgType
            self.client_type,  # Client type
            0,  # reserved
            0,  # compressed
            0,  # reserved
        )
        # logging.debug(retval+self.extra_data)
        return retval + self.extra_data

    @staticmethod
    def from_bytes(data):
        # split the header and data
        header = data[0:24]
        rdata = data[24:]

        msg_id, tstamp, vers, msg_type, client_type, res1, compressed, res3 = struct.unpack(OmniLogicRequest.HEADER_FORMAT, header)
        return msg_id, tstamp, vers, MessageType(msg_type), client_type, res1, compressed, res3, rdata


class OmniLogicAPI:
    def __init__(self, controller_ip_and_port, response_timeout):
        self.controller_ip_and_port = controller_ip_and_port
        self.response_timeout = response_timeout
        self._loop = asyncio.get_running_loop()
        self._protocol_factory = OmniLogicProtocol

    async def _get_endpoint(self):
        return await self._loop.create_datagram_endpoint(self._protocol_factory, remote_addr=self.controller_ip_and_port)

    async def async_get_alarm_list(self):
        transport, protocol = await self._get_endpoint()

        try:
            return await asyncio.wait_for(protocol.get_alarm_list(), self.response_timeout)
        finally:
            transport.close()

    async def async_get_config(self):
        transport, protocol = await self._get_endpoint()

        try:
            return await asyncio.wait_for(protocol.get_config(), self.response_timeout)
        finally:
            transport.close()

    async def async_get_filter_diagnostics(self, pool_id: int, equipment_id: int):
        """async_get_filter_diagnostics handles sending a GetUIFilterDiagnosticInfo XML API call to the Hayward Omni pool controller

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address

        Returns:
            _type_: _description_
        """
        transport, protocol = await self._get_endpoint()

        try:
            return await asyncio.wait_for(protocol.get_filter_diagnostics(pool_id, equipment_id), self.response_timeout)
        finally:
            transport.close()

    async def async_get_log_config(self):
        transport, protocol = await self._get_endpoint()

        try:
            return await asyncio.wait_for(protocol.get_log_config(), self.response_timeout)
        finally:
            transport.close()

    async def async_get_telemetry(self):
        transport, protocol = await self._get_endpoint()

        try:
            return await asyncio.wait_for(protocol.get_telemetry(), self.response_timeout)
        finally:
            transport.close()

    async def async_set_heater(self, pool_id: int, equipment_id: int, temperature: int, unit: str):
        """async_set_heater handles sending a SetUIHeaterCmd XML API call to the Hayward Omni pool controller

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            temperature (int): What temperature to request
            unit (str): The temperature unit to use (either F or C)

        Returns:
            _type_: _description_
        """
        transport, protocol = await self._get_endpoint()

        try:
            return await asyncio.wait_for(
                protocol.set_heater(pool_id, equipment_id, temperature, unit),
                self.response_timeout,
            )
        finally:
            transport.close()

    async def async_set_heater_enable(self, pool_id: int, equipment_id: int, enabled: Union[int, bool]):
        """async_set_heater_enable handles sending a SetHeaterEnable XML API call to the Hayward Omni pool controller

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            enabled (bool, optional): Turn the heater on (True) or off (False)

        Returns:
            _type_: _description_
        """
        transport, protocol = await self._get_endpoint()

        try:
            return await asyncio.wait_for(
                protocol.set_heater_enable(pool_id, equipment_id, enabled),
                self.response_timeout,
            )
        finally:
            transport.close()

    # pylint: disable=too-many-arguments,too-many-locals
    async def async_set_equipment(
        self,
        pool_id: int,
        equipment_id: int,
        is_on: Union[int, bool],
        is_countdown_timer: bool = False,
        start_time_hours: int = 0,
        start_time_minutes: int = 0,
        end_time_hours: int = 0,
        end_time_minutes: int = 0,
        days_active: int = 0,
        recurring: bool = False,
    ):
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
        transport, protocol = await self._get_endpoint()

        try:
            return await asyncio.wait_for(
                protocol.set_equipment(
                    pool_id,
                    equipment_id,
                    is_on,
                    is_countdown_timer,
                    start_time_hours,
                    start_time_minutes,
                    end_time_hours,
                    end_time_minutes,
                    days_active,
                    recurring,
                ),
                self.response_timeout,
            )
        finally:
            transport.close()

    async def async_set_filter_speed(self, pool_id: int, equipment_id: int, speed: int):
        """async_set_filter_speed handles sending a SetUIFilterSpeedCmd XML API call to the Hayward Omni pool controller

        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            speed (int): Speed value from 0-100 to set the filter to.  A value of 0 will turn the filter off.
        """
        transport, protocol = await self._get_endpoint()

        try:
            return await asyncio.wait_for(protocol.set_filter_speed(pool_id, equipment_id, speed), self.response_timeout)
        finally:
            transport.close()

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
    ):
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

        transport, protocol = await self._get_endpoint()

        try:
            return await asyncio.wait_for(
                protocol.set_light_show(
                    pool_id,
                    equipment_id,
                    show,
                    speed,
                    brightness,
                    reserved,
                    is_countdown_timer,
                    start_time_hours,
                    start_time_minutes,
                    end_time_hours,
                    end_time_minutes,
                    days_active,
                    recurring,
                ),
                self.response_timeout,
            )
        finally:
            transport.close()


class OmniLogicProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.data_queue = asyncio.Queue()
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        if exc:
            raise exc

    def datagram_received(self, data, addr):
        msg_id, _, _, msg_type, _, _, compressed, _, data = OmniLogicRequest.from_bytes(data)
        self.data_queue.put_nowait((msg_id, msg_type, compressed, data))

    def error_received(self, exc):
        raise exc

    async def _send_request(self, msg_type, extra_data="", msg_id=None):
        logging.debug("Sending Message Type: %s, Request Body: %s", msg_type.name, extra_data)

        # If we aren't sending a specific msg_id, lets randomize it
        if not msg_id:
            msg_id = random.randrange(2**32)

        # If we are speaking the XML API, it seems like we need client_type 0, otherwise we need client_type 1
        client_type = 0 if extra_data != "" else 1

        # The Hayward API terminates it's messages with a null character
        extra_data += "\x00" if extra_data != "" else ""

        request = OmniLogicRequest(msg_id, msg_type, extra_data, client_type)

        self.transport.sendto(request.to_bytes())

        # If we are the ones sending the ACK, we do not expect a response
        if msg_type not in [MessageType.XML_ACK, MessageType.ACK]:
            rec_msg_id = -1
            while rec_msg_id != msg_id:
                rec_msg_id, msg_type, _, _ = await self.data_queue.get()

    async def _send_ack(self, msg_id):
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})
        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "Ack"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")
        await self._send_request(MessageType.XML_ACK, req_body, msg_id)

    async def _receive_file(self):
        # wait for the initial packet.
        msg_id, msg_type, compressed, data = await self.data_queue.get()

        await self._send_ack(msg_id)

        # Check if the 23rd bit of the header (compressed bit) was a 1
        # There are also some messages that are ALWAYS compressed although they do not return a 1 in their LeadMessage
        msg_compressed = compressed == 1 or msg_type in [MessageType.MSP_TELEMETRY_UPDATE]

        # If the response is too large, the controller will send a LeadMessage indicating how many follow-up messages will be sent
        if msg_type == MessageType.MSP_LEADMESSAGE:
            # Parse XML
            root = ET.fromstring(data[:-1])  # strip trailing \x00
            block_count = int(root.findall(".//*[@name='MsgBlockCount']")[0].text)

            # Wait for the block data data
            retval = b""
            # If we received a LeadMessage, continue to receive messages until we have all of our data
            for _ in range(block_count):
                msg_id, msg_type, compressed, data = await self.data_queue.get()
                await self._send_ack(msg_id)
                # remove an 8 byte header to get to the payload data
                retval += data[8:]
        # If we did not receive a LeadMessage, but the message is compressed anyway...
        elif msg_compressed:
            retval = data
        # A short response, no LeadMessage and no compression...
        else:
            retval = data[8:]

        # Decompress the returned data if necessary
        if msg_compressed:
            comp_bytes = bytes.fromhex(retval.hex())
            retval = zlib.decompress(comp_bytes)

        # return retval
        return retval.decode("utf-8")

    async def get_telemetry(self):
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "RequestTelemetryData"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")
        await self._send_request(MessageType.GET_TELEMETRY, req_body)

        # Now receive the file
        data = await self._receive_file()
        return data

    async def get_alarm_list(self):
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "GetAllAlarmList"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")
        await self._send_request(MessageType.GET_ALARM_LIST, req_body)

        data = await self._receive_file()
        return data

    async def get_config(self):
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "RequestConfiguration"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")
        await self._send_request(MessageType.REQUEST_CONFIGURATION, req_body)

        data = await self._receive_file()
        return data

    async def get_filter_diagnostics(self, pool_id: int, equipment_id: int):
        """getDiagnostics handles sending a GetUIFilterDiagnosticInfo XML API call to the Hayward Omni pool controller

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
        await self._send_request(MessageType.GET_FILTER_DIAGNOSTIC_INFO, req_body)

        data = await self._receive_file()
        return data

    async def get_log_config(self):
        await self._send_request(MessageType.REQUEST_LOG_CONFIG)

        data = await self._receive_file()
        return data

    async def set_heater_enable(
        self,
        pool_id: int,
        equipment_id: int,
        enabled: Union[int, bool],
    ):
        """set_heater_enabled handles sending a SetHeaterEnable XML API call to the Hayward Omni pool controller

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
        await self._send_request(MessageType.SET_HEATER_ENABLED, req_body)

    async def set_heater(
        self,
        pool_id: int,
        equipment_id: int,
        temperature: int,
        unit: str,
    ):
        """set_heater handles sending a SetUIHeaterCmd XML API call to the Hayward Omni pool controller

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
        await self._send_request(MessageType.SET_EQUIPMENT, req_body)

    # pylint: disable=too-many-arguments,too-many-locals
    async def set_equipment(
        self,
        pool_id: int,
        equipment_id: int,
        is_on: Union[int, bool],
        is_countdown_timer: bool = False,
        start_time_hours: int = 0,
        start_time_minutes: int = 0,
        end_time_hours: int = 0,
        end_time_minutes: int = 0,
        days_active: int = 0,
        recurring: bool = False,
    ):
        """setEquipment handles sending a SetUIEquipmentCmd XML API call to the Hayward Omni pool controller
        Args:
            pool_id (int): The Pool/BodyOfWater ID that you want to address
            equipment_id (int): Which equipment_id within that Pool to address
            is_on (Union[int,bool]): For most equipment items, True/False to turn on/off.
                For Variable Speed Pumps, you can optionally provide an int from 0-100 to set the speed percentage with 0 being Off.
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
        await self._send_request(MessageType.SET_EQUIPMENT, req_body)

    async def set_filter_speed(self, pool_id: int, equipment_id: int, speed: int):
        """setFilterSpeed handles sending a SetUIFilterSpeedCmd XML API call to the Hayward Omni pool controller
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
        await self._send_request(MessageType.SET_FILTER_SPEED, req_body)

    # pylint: disable=too-many-arguments,too-many-locals
    async def set_light_show(
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
    ):
        """setLightShow handles sending a SetStandAloneLightShow XML API call to the Hayward Omni pool controller

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
        await self._send_request(MessageType.SET_STANDALONE_LIGHT_SHOW, req_body)


class OmniLogicException(Exception):
    pass
