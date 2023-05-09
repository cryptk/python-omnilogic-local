#!/usr/bin/env python3

import asyncio
import logging
import os

from pyomnilogic_local import OmniLogicAPI


async def async_main():
    omni = OmniLogicAPI((os.environ.get("OMNILOGIC_HOST"), 10444), 5.0)

    # Some basic calls to run some testing against the library
    pool_id = 7
    pump_equipment_id = 8
    light_equipment_id = 10

    print(await omni.async_get_config())
    print(await omni.async_get_telemetry())

    # print(await omni.asyncGetLogConfig())
    # print(await omni.asyncGetAlarmList())

    # Turn a variable speed pump on to 50%
    # print(await omni.asyncSetEquipment(pool_id, pump_equipment_id, 50))
    # Turn a variable speed pump on to 75%
    # print(await omni.asyncSetFilterSpeed(pool_id, pump_equipment_id, 75))
    # Turn the pump off
    # print(await omni.asyncSetEquipment(pool_id, pump_equipment_id, 50))

    # Activate a light show
    # print(await omni.asyncSetLightShow(
    #   pool_id,
    #   light_equipment_id,
    #   ColorLogicShow.VOODOO_LOUNGE,
    #   ColorLogicSpeed.ONE_HALF,
    #   ColorLogicBrightness.SIXTY_PERCENT
    # ))
    # Turn off the light
    # print(await omni.asyncSetEquipment(pool_id, light_equipment_id, 1))
    # print(await omni.asyncGetTelemetry())

    # print(await omni.asyncGetFilterDiagnostics(pool_id, pump_equipment_id))


def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.DEBUG)
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
