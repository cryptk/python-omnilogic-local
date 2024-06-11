#!/usr/bin/env python3

import asyncio
import logging
import os

from pyomnilogic_local.api import OmniLogicAPI

from .models.filter_diagnostics import FilterDiagnostics
from .models.mspconfig import MSPConfig
from .models.telemetry import Telemetry

POOL_ID = 7
PUMP_EQUIPMENT_ID = 8
LIGHT_EQUIPMENT_ID = 10
HEATER_EQUIPMENT_ID = 18
RELAY_SYSTEM_ID = 13


async def async_main() -> None:
    filter_diags: FilterDiagnostics  # pylint: disable=unused-variable # noqa: F842
    mspconfig: MSPConfig
    telem: Telemetry

    omni = OmniLogicAPI(os.environ.get("OMNILOGIC_HOST", "127.0.0.1"), 10444, 5.0)
    get_raw = os.environ.get("OMNILOGIC_RAW", False)

    # Some basic calls to run some testing against the library

    # Fetch the MSPConfig data
    mspconfig = await omni.async_get_config(raw=get_raw)  # pylint: disable=unexpected-keyword-arg

    # Fetch the current telemetry data
    telem = await omni.async_get_telemetry(raw=get_raw)  # pylint: disable=unexpected-keyword-arg

    # Fetch a list of current alarms
    # print(await omni.async_get_alarm_list())

    # Fetch diagnostic data for a filter pump
    # filter_diags = await omni.async_get_filter_diagnostics(POOL_ID, PUMP_EQUIPMENT_ID, raw=get_raw)

    print(mspconfig)
    print(telem)
    # print(filter_diags)

    # Decode the filter display revision
    # b1=chr(filter_diags.get_param_by_name("DisplayFWRevisionB1"))
    # b2=chr(filter_diags.get_param_by_name("DisplayFWRevisionB2"))
    # b3=chr(filter_diags.get_param_by_name("DisplayFWRevisionB3"))
    # b4=chr(filter_diags.get_param_by_name("DisplayFWRevisionB4"))
    # b5 and b6 are whitespace and a null terminator
    # b5=chr(filter_diags.get_param_by_name("DisplayFWRevisionB5"))
    # b6=chr(filter_diags.get_param_by_name("DisplayFWRevisionB6"))
    # print(f"{b1}{b2}.{b3}.{b4}")
    # Decode the filter power consumption (don't do this, it's returned already decoded in the telemetry)
    # p1=filter_diags.get_param_by_name("PowerMSB")
    # p2=filter_diags.get_param_by_name("PowerLSB")
    # The f-string below converts the bytes to hex and displays them.  Just get this value from the telemetry, it's easier
    # print(f"{p1:x}{p2:x}")

    # Fetch logging configuration
    # print(await omni.async_get_log_config())

    # Adjust the heater temperature
    # await omni.async_set_heater(POOL_ID, HEATER_EQUIPMENT_ID, 85, "F")

    # Turn the heater on and off
    # await omni.async_set_heater_enable(POOL_ID, HEATER_EQUIPMENT_ID, True)
    # await omni.async_set_heater_enable(POOL_ID, HEATER_EQUIPMENT_ID, False)

    # Adjust solar heater set point
    # await omni.async_set_solar_heater(POOL_ID, HEATER_EQUIPMENT_ID, 90, "F")

    # Set the heater to heat/cool/auto
    # await omni.async_set_heater_mode(POOL_ID, HEATER_EQUIPMENT_ID, HeaterMode.HEAT)
    # await omni.async_set_heater_mode(POOL_ID, HEATER_EQUIPMENT_ID, HeaterMode.COOL)
    # await omni.async_set_heater_mode(POOL_ID, HEATER_EQUIPMENT_ID, HeaterMode.AUTO)

    # Turn a variable speed pump on to 50%
    # await omni.async_set_filter_speed(POOL_ID, PUMP_EQUIPMENT_ID, 50)
    # Turn the pump off
    # await omni.async_set_equipment(POOL_ID, PUMP_EQUIPMENT_ID, False)

    # Activate a light show
    # await omni.async_set_light_show(
    #     POOL_ID, LIGHT_EQUIPMENT_ID, ColorLogicShow.TRANQUILITY, ColorLogicSpeed.ONE_TIMES, ColorLogicBrightness.ONE_HUNDRED_PERCENT
    # )
    # Turn the light on/off
    # await omni.async_set_equipment(POOL_ID, LIGHT_EQUIPMENT_ID, True)
    # await omni.async_set_equipment(POOL_ID, LIGHT_EQUIPMENT_ID, False)

    # Turn a relay on/off
    # await omni.async_set_equipment(POOL_ID, RELAY_SYSTEM_ID, True)
    # await omni.async_set_equipment(POOL_ID, RELAY_SYSTEM_ID, False)


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.DEBUG)
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
