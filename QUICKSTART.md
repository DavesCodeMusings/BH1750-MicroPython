# Quickstart Guide
If all you're interested in is a BH1750 driver to take Lux measurements on demand, this will show you how.

First, install the driver with `mpremote mip install github:DavesCodeMusings/BH1750-MicroPython`

Then, depending on if you're using asyncio or not, choose one of the code samples below to use as your main.py.

## Async
```
from machine import Pin, SoftI2C
from micropython import const
import asyncio
from bh1750_one_shot import BH1750

# Values for ESP32 Devkit V1 (30-pin board with four corner mounting holes)
# Adjust as needed for other boards.
I2C_CLOCK = const(22)
I2C_DATA = const(21)

# Does the sensor have a dome?
DIFFUSION_DOME = const(True)

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))
bh1750 = BH1750(i2c, dome=DIFFUSION_DOME)
lux = 0


async def read_sensor():
    global lux
    while True:
        bh1750.measure()
        await asyncio.sleep_ms(BH1750.MEASUREMENT_TIME_mS)
        lux = bh1750.illuminance()
        await asyncio.sleep(5)  # Helps mitigate sensor self-heating


async def communicate_readings():
    while True:
        await asyncio.sleep(10)
        print("Lux:", lux)


async def main():
    task1 = asyncio.create_task(read_sensor())
    task2 = asyncio.create_task(communicate_readings())
    await asyncio.gather(task1, task2)


asyncio.run(main())
```

## Non-Async

```
from machine import Pin, SoftI2C
from micropython import const
from time import sleep_ms
from bh1750_one_shot import BH1750

# Values for ESP32 Devkit V1 (30-pin board with four corner mounting holes)
# Adjust as needed for other boards.
I2C_CLOCK = const(22)
I2C_DATA = const(21)

# Does the sensor have a dome?
DIFFUSION_DOME = const(True)

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))
bh1750 = BH1750(i2c, dome=DIFFUSION_DOME)
bh1750.measure()
sleep_ms(BH1750.MEASUREMENT_TIME_mS)
lux = bh1750.illuminance()
print("Lux:", lux)
```
