import asyncio
import logging
import random
import struct
import time
from typing import Union
import xml.etree.ElementTree as ET
import zlib

from .omnilogicTypes import (
    MessageType,
    ColorLogicSpeed,
    ColorLogicShow,
    ColorLogicBrightness,
)


class OmniLogicRequest:
    HEADER_FORMAT = "!LQ4sLBBBB"

    def __init__(self, msgId, msgType: MessageType, extraData="", clientType=1):
        self.msgId = msgId
        self.msgType = msgType
        self.clientType = clientType
        self.extraData = bytes(extraData, "utf-8")
        # self.extraData = extraData

        self.version = "1.19".encode("ascii")

    def toBytes(self):
        retval = struct.pack(
            OmniLogicRequest.HEADER_FORMAT,
            self.msgId,  # Msg id
            int(time.time_ns() / (10**9)),  # Timestamp
            bytes(self.version),  # version string
            self.msgType.value,  # OpID/msgType
            self.clientType,  # Client type
            0,  # reserved
            0,  # compressed
            0,  # reserved
        )
        # logging.debug(retval+self.extraData)
        return retval + self.extraData

    @staticmethod
    def fromBytes(data):
        # split the header and data
        header = data[0:24]
        rdata = data[24:]

        msgId, tstamp, vers, msgType, clientType, res1, compressed, res3 = struct.unpack(OmniLogicRequest.HEADER_FORMAT, header)
        return msgId, tstamp, vers, MessageType(msgType), clientType, res1, compressed, res3, rdata


class OmniLogicAPI:
    def __init__(self, controllerIpAndPort, responseTimeout):
        self.controllerIpAndPort = controllerIpAndPort
        self.responseTimeout = responseTimeout

    async def asyncGetAlarmList(self):
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(OmniLogicProtocol, remote_addr=self.controllerIpAndPort)

        try:
            return await asyncio.wait_for(protocol.getAlarmList(), self.responseTimeout)
        finally:
            transport.close()

    async def asyncGetConfig(self):
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(OmniLogicProtocol, remote_addr=self.controllerIpAndPort)

        try:
            return await asyncio.wait_for(protocol.getConfig(), self.responseTimeout)
        finally:
            transport.close()

    async def asyncGetFilterDiagnostics(self, poolId: int, equipmentId: int):
        """getDiagnostics handles sending a GetUIFilterDiagnosticInfo XML API call to the Hayward Omni pool controller

        Args:
            poolId (int): The Pool/BodyOfWater ID that you want to address
            equipmentId (int): Which equipmentID within that Pool to address

        Returns:
            _type_: _description_
        """
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(OmniLogicProtocol, remote_addr=self.controllerIpAndPort)

        try:
            return await asyncio.wait_for(protocol.getFilterDiagnostics(poolId, equipmentId), self.responseTimeout)
        finally:
            transport.close()

    async def asyncGetLogConfig(self):
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(OmniLogicProtocol, remote_addr=self.controllerIpAndPort)

        try:
            return await asyncio.wait_for(protocol.getLogConfig(), self.responseTimeout)
        finally:
            transport.close()

    async def asyncGetTelemetry(self):
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(OmniLogicProtocol, remote_addr=self.controllerIpAndPort)

        try:
            return await asyncio.wait_for(protocol.getTelemetry(), self.responseTimeout)
        finally:
            transport.close()

    # pylint: disable=too-many-arguments,too-many-locals
    async def asyncSetEquipment(
        self,
        poolId: int,
        equipmentId: int,
        isOn: Union[int, bool],
        isCountDownTimer: bool = False,
        startTimeHours: int = 0,
        startTimeMinutes: int = 0,
        endTimeHours: int = 0,
        endTimeMinutes: int = 0,
        daysActive: int = 0,
        recurring: bool = False,
    ):
        """setEquipment handles sending a SetUIEquipmentCmd XML API call to the Hayward Omni pool controller

        Args:
            poolId (int): The Pool/BodyOfWater ID that you want to address
            equipmentId (int): Which equipmentID within that Pool to address
            isOn (Union[int,bool]): For most equipment items, True/False to turn on/off.
                For Variable Speed Pumps, you can optionally provide an int from 0-100 to set the speed percentage with 0 being Off.
            isCountDownTimer (bool, optional): For potential future use, included to be "API complete". Defaults to False.
            startTimeHours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            startTimeMinutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            endTimeHours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            endTimeMinutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            daysActive (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            recurring (bool, optional): For potential future use, included to be "API complete". Defaults to False.
        """
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(OmniLogicProtocol, remote_addr=self.controllerIpAndPort)

        try:
            return await asyncio.wait_for(
                protocol.setEquipment(
                    poolId,
                    equipmentId,
                    isOn,
                    isCountDownTimer,
                    startTimeHours,
                    startTimeMinutes,
                    endTimeHours,
                    endTimeMinutes,
                    daysActive,
                    recurring,
                ),
                self.responseTimeout,
            )
        finally:
            transport.close()

    async def asyncSetFilterSpeed(self, poolId: int, equipmentId: int, speed: int):
        """setFilterSpeed handles sending a SetUIFilterSpeedCmd XML API call to the Hayward Omni pool controller

        Args:
            poolId (int): The Pool/BodyOfWater ID that you want to address
            equipmentId (int): Which equipmentID within that Pool to address
            speed (int): Speed value from 0-100 to set the filter to.  A value of 0 will turn the filter off.
        """
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(OmniLogicProtocol, remote_addr=self.controllerIpAndPort)

        try:
            return await asyncio.wait_for(protocol.setFilterSpeed(poolId, equipmentId, speed), self.responseTimeout)
        finally:
            transport.close()

    async def asyncSetLightShow(
        self,
        poolId: int,
        equipmentId: int,
        show: ColorLogicShow,
        speed: ColorLogicSpeed = ColorLogicSpeed.ONE_TIMES,
        brightness: ColorLogicBrightness = ColorLogicBrightness.ONE_HUNDRED_PERCENT,
        reserved: int = 0,
        isCountDownTimer: bool = False,
        startTimeHours: int = 0,
        startTimeMinutes: int = 0,
        endTimeHours: int = 0,
        endTimeMinutes: int = 0,
        daysActive: int = 0,
        recurring: bool = False,
    ):
        """setLightShow handles sending a SetStandAloneLightShow XML API call to the Hayward Omni pool controller

        Args:
            poolId (int): The Pool/BodyOfWater ID that you want to address
            equipmentId (int): Which equipmentID within that Pool to address
            show (ColorLogicShow): ColorLogicShow to set the light to
            speed (ColorLogicSpeed, optional): Speed to animate the show. Defaults to 4.  0-8 which map to:
            brightness (ColorLogicBrightness, optional): How bright should the light be. Defaults to 4. 0-4 which map to:
            reserved (int, optional): Reserved. Defaults to 0.
            isCountDownTimer (bool, optional): For potential future use, included to be "API complete". Defaults to False.
            startTimeHours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            startTimeMinutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            endTimeHours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            endTimeMinutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            daysActive (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            recurring (bool, optional): For potential future use, included to be "API complete". Defaults to False.
        """

        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(OmniLogicProtocol, remote_addr=self.controllerIpAndPort)

        try:
            return await asyncio.wait_for(
                protocol.setLightShow(
                    poolId,
                    equipmentId,
                    show,
                    speed,
                    brightness,
                    reserved,
                    isCountDownTimer,
                    startTimeHours,
                    startTimeMinutes,
                    endTimeHours,
                    endTimeMinutes,
                    daysActive,
                    recurring,
                ),
                self.responseTimeout,
            )
        finally:
            transport.close()


class OmniLogicProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.dataQueue = asyncio.Queue()
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        if exc:
            raise exc

    def datagram_received(self, data, addr):
        msgId, _, _, msgType, _, _, compressed, _, data = OmniLogicRequest.fromBytes(data)
        self.dataQueue.put_nowait((msgId, msgType, compressed, data))

    def error_received(self, exc):
        raise exc

    async def _sendRequest(self, msgType, extraData=""):
        logging.debug("Sending Message Type: %s, Request Body: %s", msgType.name, extraData)

        # Good security practice, random msgId's.
        msgId = random.randrange(2**32)

        # If we are speaking the XML API, it seems like we need clientType 0, otherwise we need clientType 1
        clientType = 0 if extraData != "" else 1

        # The Hayward API terminates it's messages with a null character
        extraData += "\x00" if extraData != "" else ""

        request = OmniLogicRequest(msgId, msgType, extraData, clientType)

        self.transport.sendto(request.toBytes())

        # Wait for the ACK
        recMsgId = -1
        while recMsgId != msgId:
            recMsgId, msgType, _, _ = await self.dataQueue.get()

    def _sendAck(self, msgId):

        bodyElement = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})
        nameElement = ET.SubElement(bodyElement, "Name")
        nameElement.text = "Ack"

        reqBody = ET.tostring(bodyElement, xml_declaration=True, encoding="unicode")
        # TODO: Why is this method sending the request itself rather than using self._sendRequest like everything else?
        request = OmniLogicRequest(msgId, MessageType.XML_ACK, reqBody, 0)

        self.transport.sendto(request.toBytes())

    async def _receiveFile(self):
        # wait for the initial packet.
        msgId, msgType, compressed, data = await self.dataQueue.get()

        self._sendAck(msgId)

        # Check if the 23rd bit of the header (compressed bit) was a 1
        # There are also some messages that are ALWAYS compressed although they do not return a 1 in their LeadMessage
        msgCompressed = compressed == 1 or msgType in [MessageType.MSP_TELEMETRY_UPDATE]

        # If the response is too large, the controller will send a LeadMessage indicating how many follow-up messages will be sent
        if msgType == MessageType.MSP_LEADMESSAGE:
            # Parse XML
            root = ET.fromstring(data[:-1])  # strip trailing \x00
            blockCount = int(root.findall(".//*[@name='MsgBlockCount']")[0].text)

            # Wait for the block data data
            retval = b""
            # If we received a LeadMessage, continue to receive messages until we have all of our data
            for _ in range(blockCount):
                msgId, msgType, compressed, data = await self.dataQueue.get()
                self._sendAck(msgId)
                # remove an 8 byte header to get to the payload data
                retval += data[8:]
        # If we did not receive a LeadMessage, but the message is compressed anyway...
        elif msgCompressed:
            retval = data
        # A short response, no LeadMessage and no compression...
        else:
            retval = data[8:]

        # Decompress the returned data if necessary
        if msgCompressed:
            compBytes = bytes.fromhex(retval.hex())
            retval = zlib.decompress(compBytes)

        # return retval
        return retval.decode("utf-8")

    async def getTelemetry(self):
        bodyElement = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        nameElement = ET.SubElement(bodyElement, "Name")
        nameElement.text = "RequestTelemetryData"

        reqBody = ET.tostring(bodyElement, xml_declaration=True, encoding="unicode")
        await self._sendRequest(MessageType.GET_TELEMETRY, reqBody)

        # Now receive the file
        data = await self._receiveFile()
        return data

    async def getAlarmList(self):
        bodyElement = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        nameElement = ET.SubElement(bodyElement, "Name")
        nameElement.text = "GetAllAlarmList"

        reqBody = ET.tostring(bodyElement, xml_declaration=True, encoding="unicode")
        await self._sendRequest(MessageType.GET_ALARM_LIST, reqBody)

        data = await self._receiveFile()
        return data

    async def getConfig(self):
        bodyElement = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        nameElement = ET.SubElement(bodyElement, "Name")
        nameElement.text = "RequestConfiguration"

        reqBody = ET.tostring(bodyElement, xml_declaration=True, encoding="unicode")
        await self._sendRequest(MessageType.REQUEST_CONFIGURATION, reqBody)

        data = await self._receiveFile()
        return data

    async def getFilterDiagnostics(self, poolId: int, equipmentId: int):
        """getDiagnostics handles sending a GetUIFilterDiagnosticInfo XML API call to the Hayward Omni pool controller

        Args:
            poolId (int): The Pool/BodyOfWater ID that you want to address
            equipmentId (int): Which equipmentID within that Pool to address

        Returns:
            _type_: _description_
        """
        bodyElement = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        nameElement = ET.SubElement(bodyElement, "Name")
        nameElement.text = "GetUIFilterDiagnosticInfo"
        parametersElement = ET.SubElement(bodyElement, "Parameters")
        parameter = ET.SubElement(parametersElement, "Parameter", name="PoolID", dataType="int")
        parameter.text = str(poolId)
        parameter = ET.SubElement(parametersElement, "Parameter", name="EquipmentID", dataType="int")
        parameter.text = str(equipmentId)

        reqBody = ET.tostring(bodyElement, xml_declaration=True, encoding="unicode")
        await self._sendRequest(MessageType.GET_FILTER_DIAGNOSTIC_INFO, reqBody)

        data = await self._receiveFile()
        return data

    async def getLogConfig(self):
        await self._sendRequest(MessageType.REQUEST_LOG_CONFIG)

        data = await self._receiveFile()
        return data

    async def setEquipment(
        self,
        poolId: int,
        equipmentId: int,
        isOn: Union[int, bool],
        isCountDownTimer: bool = False,
        startTimeHours: int = 0,
        startTimeMinutes: int = 0,
        endTimeHours: int = 0,
        endTimeMinutes: int = 0,
        daysActive: int = 0,
        recurring: bool = False,
    ):
        """setEquipment handles sending a SetUIEquipmentCmd XML API call to the Hayward Omni pool controller
        Args:
            poolId (int): The Pool/BodyOfWater ID that you want to address
            equipmentId (int): Which equipmentID within that Pool to address
            isOn (Union[int,bool]): For most equipment items, True/False to turn on/off.
                For Variable Speed Pumps, you can optionally provide an int from 0-100 to set the speed percentage with 0 being Off.
            isCountDownTimer (bool, optional): For potential future use, included to be "API complete". Defaults to False.
            startTimeHours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            startTimeMinutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            endTimeHours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            endTimeMinutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            daysActive (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            recurring (bool, optional): For potential future use, included to be "API complete". Defaults to False.
        """
        bodyElement = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        nameElement = ET.SubElement(bodyElement, "Name")
        nameElement.text = "SetUIEquipmentCmd"

        parametersElement = ET.SubElement(bodyElement, "Parameters")
        parameter = ET.SubElement(parametersElement, "Parameter", name="PoolID", dataType="int")
        parameter.text = str(poolId)
        parameter = ET.SubElement(parametersElement, "Parameter", name="EquipmentID", dataType="int")
        parameter.text = str(equipmentId)
        parameter = ET.SubElement(parametersElement, "Parameter", name="IsOn", dataType="int")
        parameter.text = str(int(isOn))
        parameter = ET.SubElement(parametersElement, "Parameter", name="IsCountDownTimer", dataType="bool")
        parameter.text = str(int(isCountDownTimer))
        parameter = ET.SubElement(parametersElement, "Parameter", name="StartTimeHours", dataType="int")
        parameter.text = str(startTimeHours)
        parameter = ET.SubElement(parametersElement, "Parameter", name="StartTimeMinutes", dataType="int")
        parameter.text = str(startTimeMinutes)
        parameter = ET.SubElement(parametersElement, "Parameter", name="EndTimeHours", dataType="int")
        parameter.text = str(endTimeHours)
        parameter = ET.SubElement(parametersElement, "Parameter", name="EndTimeMinutes", dataType="int")
        parameter.text = str(endTimeMinutes)
        parameter = ET.SubElement(parametersElement, "Parameter", name="DaysActive", dataType="int")
        parameter.text = str(daysActive)
        parameter = ET.SubElement(parametersElement, "Parameter", name="Recurring", dataType="bool")
        parameter.text = str(int(recurring))

        reqBody = ET.tostring(bodyElement, xml_declaration=True, encoding="unicode")
        await self._sendRequest(MessageType.SET_EQUIPMENT, reqBody)

    async def setFilterSpeed(self, poolId: int, equipmentId: int, speed: int):
        """setFilterSpeed handles sending a SetUIFilterSpeedCmd XML API call to the Hayward Omni pool controller
        Args:
            poolId (int): The Pool/BodyOfWater ID that you want to address
            equipmentId (int): Which equipmentID within that Pool to address
            speed (int): Speed value from 0-100 to set the filter to.  A value of 0 will turn the filter off.
        """
        bodyElement = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        nameElement = ET.SubElement(bodyElement, "Name")
        nameElement.text = "SetUIFilterSpeedCmd"

        parametersElement = ET.SubElement(bodyElement, "Parameters")
        parameter = ET.SubElement(parametersElement, "Parameter", name="PoolID", dataType="int")
        parameter.text = str(poolId)
        parameter = ET.SubElement(parametersElement, "Parameter", name="FilterID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipmentId)
        # NOTE: Despite the API calling it RPM here, the speed value is a percentage from 1-100
        parameter = ET.SubElement(parametersElement, "Parameter", name="Speed", dataType="int", unit="RPM", alias="Data")
        parameter.text = str(speed)

        reqBody = ET.tostring(bodyElement, xml_declaration=True, encoding="unicode")
        await self._sendRequest(MessageType.SET_FILTER_SPEED, reqBody)

    async def setLightShow(
        self,
        poolId: int,
        equipmentId: int,
        show: ColorLogicShow,
        speed: ColorLogicSpeed = ColorLogicSpeed.ONE_TIMES,
        brightness: ColorLogicBrightness = ColorLogicBrightness.ONE_HUNDRED_PERCENT,
        reserved: int = 0,
        isCountDownTimer: bool = False,
        startTimeHours: int = 0,
        startTimeMinutes: int = 0,
        endTimeHours: int = 0,
        endTimeMinutes: int = 0,
        daysActive: int = 0,
        recurring: bool = False,
    ):
        """setLightShow handles sending a SetStandAloneLightShow XML API call to the Hayward Omni pool controller

        Args:
            poolId (int): The Pool/BodyOfWater ID that you want to address
            equipmentId (int): Which equipmentID within that Pool to address
            show (ColorLogicShow): ColorLogicShow to set the light to
            speed (ColorLogicSpeed, optional): Speed to animate the show. Defaults to 4.  0-8 which map to:
            brightness (ColorLogicBrightness, optional): How bright should the light be. Defaults to 4. 0-4 which map to:
            reserved (int, optional): Reserved. Defaults to 0.
            isCountDownTimer (bool, optional): For potential future use, included to be "API complete". Defaults to False.
            startTimeHours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            startTimeMinutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            endTimeHours (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            endTimeMinutes (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            daysActive (int, optional): For potential future use, included to be "API complete". Defaults to 0.
            recurring (bool, optional): For potential future use, included to be "API complete". Defaults to False.
        """
        bodyElement = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})

        nameElement = ET.SubElement(bodyElement, "Name")
        nameElement.text = "SetStandAloneLightShow"

        parametersElement = ET.SubElement(bodyElement, "Parameters")
        parameter = ET.SubElement(parametersElement, "Parameter", name="PoolID", dataType="int")
        parameter.text = str(poolId)
        parameter = ET.SubElement(parametersElement, "Parameter", name="LightID", dataType="int", alias="EquipmentID")
        parameter.text = str(equipmentId)
        parameter = ET.SubElement(parametersElement, "Parameter", name="Show", dataType="byte")
        parameter.text = str(show.value)
        parameter = ET.SubElement(parametersElement, "Parameter", name="Speed", dataType="byte")
        parameter.text = str(speed.value)
        parameter = ET.SubElement(parametersElement, "Parameter", name="Brightness", dataType="byte")
        parameter.text = str(brightness.value)
        parameter = ET.SubElement(parametersElement, "Parameter", name="Reserved", dataType="byte")
        parameter.text = str(reserved)
        parameter = ET.SubElement(parametersElement, "Parameter", name="IsCountDownTimer", dataType="bool")
        parameter.text = str(int(isCountDownTimer))
        parameter = ET.SubElement(parametersElement, "Parameter", name="StartTimeHours", dataType="int")
        parameter.text = str(startTimeHours)
        parameter = ET.SubElement(parametersElement, "Parameter", name="StartTimeMinutes", dataType="int")
        parameter.text = str(startTimeMinutes)
        parameter = ET.SubElement(parametersElement, "Parameter", name="EndTimeHours", dataType="int")
        parameter.text = str(endTimeHours)
        parameter = ET.SubElement(parametersElement, "Parameter", name="EndTimeMinutes", dataType="int")
        parameter.text = str(endTimeMinutes)
        parameter = ET.SubElement(parametersElement, "Parameter", name="DaysActive", dataType="int")
        parameter.text = str(daysActive)
        parameter = ET.SubElement(parametersElement, "Parameter", name="Recurring", dataType="bool")
        parameter.text = str(int(recurring))

        reqBody = ET.tostring(bodyElement, xml_declaration=True, encoding="unicode")
        await self._sendRequest(MessageType.SET_STANDALONE_LIGHT_SHOW, reqBody)


class OmniLogicException(Exception):
    pass

# TODO: remove this
class LoginException(OmniLogicException):
    pass