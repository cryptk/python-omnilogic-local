#!/usr/bin/env python3

import asyncio
import logging
import os

from pyomnilogic_local.api import OmniLogicAPI

# from pyomnilogic_local.models.telemetry import Telemetry


POOL_ID = 7
PUMP_EQUIPMENT_ID = 8
LIGHT_EQUIPMENT_ID = 10
HEATER_EQUIPMENT_ID = 18


async def async_main() -> None:
    omni = OmniLogicAPI(os.environ.get("OMNILOGIC_HOST", "127.0.0.1"), 10444, 5.0)

    # Some basic calls to run some testing against the library
    # Fetch the MSPConfig data
    config = await omni.async_get_config()
    print(config)
    # parsed_config = MSPConfig.load_xml(config)

    # Fetch the current telemetry data
    telem = await omni.async_get_telemetry()
    print(telem)
    # parsed_telem = Telemetry.load_xml(xml=telem)

    # Fetch a list of current alarms
    # print(await omni.async_get_alarm_list())

    # Fetch diagnostic data for a filter pump
    # print(await omni.async_get_filter_diagnostics(POOL_ID, PUMP_EQUIPMENT_ID))

    # Fetch logging configuration
    # print(await omni.async_get_log_config())

    # Adjust the heater temperature
    # await omni.async_set_heater(POOL_ID, HEATER_EQUIPMENT_ID, 85, "F")

    # Turn the heater on and off
    # await omni.async_set_heater_enable(POOL_ID, HEATER_EQUIPMENT_ID, True)
    # await omni.async_set_heater_enable(POOL_ID, HEATER_EQUIPMENT_ID, False)

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


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.DEBUG)
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
