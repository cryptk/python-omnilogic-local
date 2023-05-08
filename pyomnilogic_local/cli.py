#!/usr/bin/env python3

from pyomnilogic_local import OmniLogicAPI
import logging
import asyncio
import os

async def async_main():

    omni = OmniLogicAPI((os.environ.get("OMNILOGIC_HOST"), 10444), 5.0)

    # Some basic calls to run some testing against the library
    poolId = 7
    pumpEquipmentId = 8
    lightEquipmentId = 10

    # print(await omni.asyncGetConfig())
    print(await omni.asyncGetTelemetry())
    print(await omni.asyncSetEquipment(poolId, lightEquipmentId, False))
    while True:
        await asyncio.sleep(0.25)
        print(await omni.asyncGetTelemetry())
    # print(await omni.asyncGetLogConfig())
    # print(await omni.asyncGetAlarmList())

    # Turn a variable speed pump on to 50%
    # print(await omni.asyncSetEquipment(poolId, pumpEquipmentId, 50))
    # Turn a variable speed pump on to 75%
    # print(await omni.asyncSetFilterSpeed(poolId, pumpEquipmentId, 75))
    # Turn the pump off
    # print(await omni.asyncSetEquipment(poolId, pumpEquipmentId, 50))

    # Activate a light show
    # print(await omni.asyncSetLightShow(
    #   poolId,
    #   lightEquipmentId,
    #   ColorLogicShow.VOODOO_LOUNGE,
    #   ColorLogicSpeed.ONE_HALF,
    #   ColorLogicBrightness.SIXTY_PERCENT
    # ))
    # Turn off the light
    print(await omni.asyncSetEquipment(poolId, lightEquipmentId, 1))
    print(await omni.asyncGetTelemetry())

    # print(await omni.asyncGetFilterDiagnostics(poolId, pumpEquipmentId))

def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.DEBUG)
    asyncio.run(async_main())

if __name__ == "__main__":
    main()