from __future__ import annotations

from pydantic import ConfigDict
from pydantic_xml import BaseXmlModel, attr, element, wrapped

from .const import XML_NS

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


class FilterDiagnosticsParameter(BaseXmlModel, tag="Parameter", ns="api", nsmap=XML_NS):
    """Individual diagnostic parameter with name, type, and value."""

    model_config = ConfigDict(from_attributes=True)

    name: str = attr()
    data_type: str = attr(name="dataType")
    value: int


class FilterDiagnostics(BaseXmlModel, tag="Response", ns="api", nsmap=XML_NS):
    """Filter diagnostics response containing diagnostic parameters.

    The XML structure has a Parameters wrapper element containing Parameter children:
    <Response>
        <Name>FilterDiagnostics</Name>
        <Parameters>
            <Parameter name="..." dataType="...">value</Parameter>
            ...
        </Parameters>
    </Response>
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = element(tag="Name")
    parameters: list[FilterDiagnosticsParameter] = wrapped("Parameters", element(tag="Parameter", default_factory=list))

    def get_param_by_name(self, name: str) -> int:
        """Get parameter value by name.

        Args:
            name: Name of the parameter to retrieve

        Returns:
            The integer value of the parameter

        Raises:
            IndexError: If parameter name not found
        """
        return [param.value for param in self.parameters if param.name == name][0]

    @staticmethod
    def load_xml(xml: str) -> FilterDiagnostics:
        """Load filter diagnostics from XML string.

        Args:
            xml: XML string containing filter diagnostics data

        Returns:
            Parsed FilterDiagnostics instance
        """
        return FilterDiagnostics.from_xml(xml)
