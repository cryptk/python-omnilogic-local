from __future__ import annotations

from pydantic import BaseModel, Field
from xmltodict import parse as xml_parse


class FilterDiagnosticsParameter(BaseModel):
    name: str = Field(alias="@name")
    dataType: str = Field(alias="@dataType")
    value: int = Field(alias="#text")


class FilterDiagnosticsParameters(BaseModel):
    parameter: list[FilterDiagnosticsParameter] = Field(alias="Parameter")


class FilterDiagnostics(BaseModel):
    name: str = Field(alias="Name")
    # parameters: FilterDiagnosticsParameters = Field(alias="Parameters")
    parameters: list[FilterDiagnosticsParameter] = Field(alias="Parameters")

    class Config:
        orm_mode = True

    def get_param_by_name(self, name: str) -> int:
        return [param.value for param in self.parameters if param.name == name][0]  # pylint: disable=not-an-iterable

    @staticmethod
    def load_xml(xml: str) -> FilterDiagnostics:
        data = xml_parse(
            xml,
            # Some things will be lists or not depending on if a pool has more than one of that piece of equipment.  Here we are coercing
            # everything that *could* be a list into a list to make the parsing more consistent.
            force_list=("Parameter", "Parameters"),
        )
        # The XML nests the Parameter entries under a Parameters entry, this is annoying to work with.  Here we are adjusting the data to
        # remove that extra level in the data
        data["Response"]["Parameters"] = data["Response"]["Parameters"]["Parameter"]
        return FilterDiagnostics.parse_obj(data["Response"])
