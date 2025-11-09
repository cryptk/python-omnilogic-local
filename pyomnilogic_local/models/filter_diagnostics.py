from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from xmltodict import parse as xml_parse

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

    name: str = Field(alias="Name")
    parameters: list[FilterDiagnosticsParameter] = Field(alias="Parameters")

    def get_param_by_name(self, name: str) -> int:
        return next(param.value for param in self.parameters if param.name == name)

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
        return FilterDiagnostics.model_validate(data["Response"])
