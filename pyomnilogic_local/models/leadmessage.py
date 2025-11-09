from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .const import XML_NS

# Example Lead Message XML:
#
# <?xml.version="1.0" encoding="UTF-8"?>
# <Response xmlns="http://nextgen.hayward.com/api">
#     <Name>LeadMessage</Name>
#     <Parameters>
#         <Parameter name="SourceOpId" dataType="int">1003</Parameter>
#         <Parameter name="MsgSize" dataType="int">3709</Parameter>
#         <Parameter name="MsgBlockCount" dataType="int">4</Parameter>
#         <Parameter name="Type" dataType="int">0</Parameter>
#     </Parameters>
# </Response>


class LeadMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_op_id: int = Field(alias="SourceOpId")
    msg_size: int = Field(alias="MsgSize")
    msg_block_count: int = Field(alias="MsgBlockCount")
    type: int = Field(alias="Type")

    @model_validator(mode="before")
    @classmethod
    def parse_xml_element(cls, data: Any) -> dict[str, Any]:
        """Parse XML Element into dict format for Pydantic validation."""
        if isinstance(data, Element):
            # Parse the Parameter elements from the XML
            result = {}
            for param in data.findall(".//api:Parameter", XML_NS):
                if name := param.get("name"):
                    result[name] = int(param.text) if param.text else 0
            return result
        return data
