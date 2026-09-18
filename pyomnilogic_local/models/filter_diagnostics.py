from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, ValidationError
from xmltodict import parse as xml_parse

from pyomnilogic_local.models.exceptions import OmniParsingError

# Example Filter Diagnostics XML:
#
# <?xml version="1.0" encoding="UTF-8" ?>
# <Response xmlns="http://nextgen.hayward.com/api">
#     <Name>GetUIFilterDiagnosticInfoRsp</Name>
#     <Parameters>
#         <Parameter name="PoolID" dataType="int">7</Parameter>
#         <Parameter name="EquipmentID" dataType="int">8</Parameter>
#         <Parameter name="PowerLSB" dataType="byte">133</Parameter>
#         <Parameter name="PowerMSB" dataType="byte">4</Parameter>
#         <Parameter name="ErrorStatus" dataType="byte">0</Parameter>
#         <Parameter name="DisplayFWRevisionB1" dataType="byte">49</Parameter>
#         <Parameter name="DisplayFWRevisionB2" dataType="byte">48</Parameter>
#         <Parameter name="DisplayFWRevisionB3" dataType="byte">49</Parameter>
#         <Parameter name="DisplayFWRevisionB4" dataType="byte">53</Parameter>
#         <Parameter name="DisplayFWRevisionB5" dataType="byte">32</Parameter>
#         <Parameter name="DisplayFWRevisionB6" dataType="byte">0</Parameter>
#         <Parameter name="DriveFWRevisionB1" dataType="byte">48</Parameter>
#         <Parameter name="DriveFWRevisionB2" dataType="byte">48</Parameter>
#         <Parameter name="DriveFWRevisionB3" dataType="byte">55</Parameter>
#         <Parameter name="DriveFWRevisionB4" dataType="byte">48</Parameter>
#         <Parameter name="DriveFWRevisionB5" dataType="byte">32</Parameter>
#         <Parameter name="DriveFWRevisionB6" dataType="byte">0</Parameter>
#     </Parameters>
# </Response>


class FilterDiagnosticsParameter(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(alias="@name")
    data_type: str = Field(alias="@dataType")
    value: int = Field(alias="#text")


class FilterDiagnosticsParameters(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parameter: list[FilterDiagnosticsParameter] = Field(alias="Parameter")


class FilterDiagnostics(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    _raw: str = PrivateAttr(default="")

    name: str = Field(alias="Name")
    parameters: list[FilterDiagnosticsParameter] = Field(alias="Parameters")

    def get_param_by_name(self, name: str) -> int:
        return next(param.value for param in self.parameters if param.name == name)

    def _decode_revision(self, prefix: str) -> str:
        bytes_ = []
        for index in range(1, 7):
            param_name = f"{prefix}B{index}"
            try:
                byte_val = self.get_param_by_name(param_name)
            except StopIteration:
                break
            if byte_val == 0:
                break
            bytes_.append(byte_val)
        if not bytes_:
            return ""
        raw = bytes(bytes_).decode("ascii", errors="ignore").strip()
        if re.fullmatch(r"\d{4}", raw):
            return f"{raw[:2]}.{raw[2]}.{raw[3]}"

        compact = raw.lstrip("0") or raw
        if re.fullmatch(r"\d{2}[A-Za-z]", compact):
            return f"{compact[0]}.{compact[1:]}"

        return raw

    @property
    def power_watts(self) -> int:
        """Current power draw in watts computed from MSB/LSB fields."""
        lsb = self.get_param_by_name("PowerLSB")
        msb = self.get_param_by_name("PowerMSB")
        return (msb << 8) | lsb

    @property
    def drive_firmware_revision(self) -> str:
        """Drive firmware revision string, if present in diagnostics payload."""
        return self._decode_revision("DriveFWRevision")

    @property
    def display_firmware_revision(self) -> str:
        """Display firmware revision string, if present in diagnostics payload."""
        return self._decode_revision("DisplayFWRevision")

    @property
    def error_status(self) -> int:
        """Raw error status code reported by controller diagnostics."""
        return self.get_param_by_name("ErrorStatus")

    @property
    def error_summary(self) -> str:
        """Friendly error summary for diagnostics."""
        return "No errors detected" if self.error_status == 0 else f"Error status code {self.error_status}"

    @staticmethod
    def load_xml(xml: str) -> FilterDiagnostics:
        data = xml_parse(
            xml,
            # Some things will be lists or not depending on if a pool has more than one of that piece of equipment.  Here we are coercing
            # everything that *could* be a list into a list to make the parsing more consistent.
            force_list=("Parameter"),
        )
        # The XML nests the Parameter entries under a Parameters entry, this is annoying to work with.  Here we are adjusting the data to
        # remove that extra level in the data
        data["Response"]["Parameters"] = data["Response"]["Parameters"]["Parameter"]
        try:
            instance = FilterDiagnostics.model_validate(data["Response"])
            instance._raw = xml
        except ValidationError as exc:
            msg = f"Failed to parse Filter Diagnostics: {exc}"
            raise OmniParsingError(msg) from exc
        else:
            return instance
