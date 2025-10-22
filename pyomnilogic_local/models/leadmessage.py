from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .const import XML_NS


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
