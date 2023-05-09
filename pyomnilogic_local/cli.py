#!/usr/bin/env python3

import asyncio
import logging
import os

from pyomnilogic_local import OmniLogicAPI


async def async_main():
    omni = OmniLogicAPI((os.environ.get("OMNILOGIC_HOST"), 10444), 5.0)

    # Some basic calls to run some testing against the library
    pool_id = 7  # pylint: disable=unused-variable
    pump_equipment_id = 8  # pylint: disable=unused-variable
    light_equipment_id = 10  # pylint: disable=unused-variable

    print(await omni.async_get_config())
    print(await omni.async_get_telemetry())

    print(await omni.async_get_log_config())
    print(await omni.async_get_alarm_list())

    # Turn a variable speed pump on to 50%
    # print(await omni.async_set_equipment(pool_id, pump_equipment_id, 50))
    # Turn a variable speed pump on to 75%
    # print(await omni.async_set_filter_speed(pool_id, pump_equipment_id, 75))
    # Turn the pump off
    # print(await omni.async_set_equipment(pool_id, pump_equipment_id, 50))

    # Activate a light show
    # print(await omni.async_set_light_show(
    #   pool_id,
    #   light_equipment_id,
    #   ColorLogicShow.VOODOO_LOUNGE,
    #   ColorLogicSpeed.ONE_HALF,
    #   ColorLogicBrightness.SIXTY_PERCENT
    # ))
    # Turn off the light
    # print(await omni.async_set_equipment(pool_id, light_equipment_id, 1))
    # print(await omni.async_get_telemetry())

    print(await omni.async_get_filter_diagnostics(pool_id, pump_equipment_id))


def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.DEBUG)
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
