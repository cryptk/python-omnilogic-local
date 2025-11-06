from __future__ import annotations

from pydantic import ConfigDict, computed_field
from pydantic_xml import BaseXmlModel, attr, element, wrapped

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


class LeadMessageParameter(BaseXmlModel, tag="Parameter", ns="api", nsmap=XML_NS):
    """Individual parameter in lead message."""

    name: str = attr()
    value: int


class LeadMessage(BaseXmlModel, tag="Response", ns="api", nsmap=XML_NS):
    """Lead message containing protocol parameters.

    Lead messages are sent at the start of communication to establish
    protocol parameters like message size and block count.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = element(tag="Name")
    parameters: list[LeadMessageParameter] = wrapped("Parameters", element(tag="Parameter", default_factory=list))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def source_op_id(self) -> int:
        """Extract SourceOpId from parameters."""
        return next((p.value for p in self.parameters if p.name == "SourceOpId"), 0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def msg_size(self) -> int:
        """Extract MsgSize from parameters."""
        return next((p.value for p in self.parameters if p.name == "MsgSize"), 0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def msg_block_count(self) -> int:
        """Extract MsgBlockCount from parameters."""
        return next((p.value for p in self.parameters if p.name == "MsgBlockCount"), 0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def type(self) -> int:
        """Extract Type from parameters."""
        return next((p.value for p in self.parameters if p.name == "Type"), 0)
