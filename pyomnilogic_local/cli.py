#!/usr/bin/env python3

import asyncio
import logging
import os
from xml.etree.ElementTree import fromstring as xmlfromstring

from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.models.telemetry import Telemetry

POOL_ID = 7
PUMP_EQUIPMENT_ID = 8
LIGHT_EQUIPMENT_ID = 10


async def async_main() -> None:
    omni = OmniLogicAPI((os.environ.get("OMNILOGIC_HOST", "127.0.0.1"), 10444), 15.0)

    # Some basic calls to run some testing against the library
    # Fetch the MSPConfig data
    # print(await omni.async_get_config())
    # Fetch the current telemetry data
    telem = await omni.async_get_telemetry()
    # print(telem)
    parsed_telem = Telemetry.from_orm(xmlfromstring(telem))
    print(parsed_telem)
    # pprint(parsed_telem.dict())
    # Fetch the current log configuration
    # print(await omni.async_get_log_config())
    # Fetch a list of current alarms
    # print(await omni.async_get_alarm_list())
    # Fetch diagnostic data for a filter pump
    # print(await omni.async_get_filter_diagnostics(POOL_ID, PUMP_EQUIPMENT_ID))

    # Turn a variable speed pump on to 50%
    # print(await omni.async_set_equipment(POOL_ID, PUMP_EQUIPMENT_ID, 50))
    # Turn a variable speed pump on to 75%
    # print(await omni.async_set_filter_speed(POOL_ID, PUMP_EQUIPMENT_ID, 75))
    # Turn the pump off
    # print(await omni.async_set_equipment(POOL_ID, PUMP_EQUIPMENT_ID, False))

    # Activate a light show
    # print(
    #     await omni.async_set_light_show(
    #         POOL_ID, LIGHT_EQUIPMENT_ID, ColorLogicShow.VOODOO_LOUNGE, ColorLogicSpeed.ONE_HALF, ColorLogicBrightness.SIXTY_PERCENT
    #     )
    # )
    # Turn off the light
    # print(await omni.async_set_equipment(POOL_ID, LIGHT_EQUIPMENT_ID, False))


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.DEBUG)
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
