from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.models.mspconfig import MSPConfig
from pyomnilogic_local.models.telemetry import Telemetry


async def async_get_mspconfig(omni: OmniLogicAPI, raw: bool = False) -> MSPConfig:
    mspconfig: MSPConfig
    mspconfig = await omni.async_get_config(raw=raw)
    return mspconfig


async def async_get_telemetry(omni: OmniLogicAPI, raw: bool = False) -> Telemetry:
    telemetry: Telemetry
    telemetry = await omni.async_get_telemetry(raw=raw)
    return telemetry
