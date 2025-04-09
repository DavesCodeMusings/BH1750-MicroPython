# Read ambient light level from BH1750 sensor in Hi-Res One-Time mode

from machine import Pin, SoftI2C
from micropython import const
from time import sleep_ms

# Values for ESP32 Devkit V1 (30-pin board with four corner mounting holes)
# Adjust as needed for other boards.
I2C_CLOCK = const(22)
I2C_DATA = const(21)
I2C_ADDR = const(0x23)

# How much compensation for the sensor's dome?
DOME_CORRECTION = const(2.75)

# BH1750 opcodes
POWER_ON = const(0b_0000_0001)
ONE_TIME_HRES = const(0b_0010_0000)

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))
i2c.writeto(I2C_ADDR, POWER_ON.to_bytes())
i2c.writeto(I2C_ADDR, ONE_TIME_HRES.to_bytes())
sleep_ms(180)
result = i2c.readfrom(I2C_ADDR, 2)
lux = int.from_bytes(result) / 1.2
if DOME_CORRECTION:
    lux = lux * DOME_CORRECTION

print("Lux reading:", round(lux))
