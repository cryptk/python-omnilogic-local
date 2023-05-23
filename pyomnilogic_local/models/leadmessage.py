from __future__ import annotations

from pydantic import BaseModel, Field

from .util import ParameterGetter


class LeadMessage(BaseModel):
    source_op_id: int = Field(alias="SourceOpId")
    msg_size: int = Field(alias="MsgSize")
    msg_block_count: int = Field(alias="MsgBlockCount")
    type: int = Field(alias="Type")

    class Config:
        orm_mode = True
        getter_dict = ParameterGetter
