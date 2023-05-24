#!/usr/bin/env python3

import asyncio
import logging
import os
from pprint import pprint

from pyomnilogic_local.api import OmniLogicAPI

# from pyomnilogic_local.models.telemetry import Telemetry
from pyomnilogic_local.models.mspconfig import MSPConfig

POOL_ID = 7
PUMP_EQUIPMENT_ID = 8
LIGHT_EQUIPMENT_ID = 10


async def async_main() -> None:
    omni = OmniLogicAPI((os.environ.get("OMNILOGIC_HOST", "127.0.0.1"), 10444), 15.0)

    # Some basic calls to run some testing against the library
    # Fetch the MSPConfig data
    config = await omni.async_get_config()
    print(config)
    parsed_config = MSPConfig.load_xml(config)
    pprint(parsed_config)
    # print(parsed_config)
    # print(parsed_config.backyard[0].bow[0].filter[0])
    # print(parsed_config.backyard[0].bow[0].filter[0].test())
    # Fetch the current telemetry data
    # telem = await omni.async_get_telemetry()
    # print(telem)
    # parsed_telem = Telemetry.load_xml(xml=telem)
    # print(parsed_telem.dict())
    # print()
    # print(parsed_telem.get_telem_by_systemid(18))
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
