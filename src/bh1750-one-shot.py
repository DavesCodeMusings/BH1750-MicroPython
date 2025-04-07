# Read ambient light level from BH1750 sensor in Hi-Res One-Time mode

from micropython import const


class BH1750:
    POWER_ON = const(0b0000_0001)
    ONE_TIME_HRES = const(0b0010_0000)
    MEASUREMENT_TIME_mS = const(180)

    def __init__(self, i2c, addr=0x23, dome=True):
        self._i2c = i2c
        self._i2c_addr = addr
        self._diffusion_dome = dome

    def measure(self):
        self._i2c.writeto(self._i2c_addr, BH1750.POWER_ON.to_bytes())
        self._i2c.writeto(self._i2c_addr, BH1750.ONE_TIME_HRES.to_bytes())

    def illumination(self):
        result = self._i2c.readfrom(self._i2c_addr, 2)
        lux = round(int.from_bytes(result) / 1.2)
        if self._diffusion_dome:
            lux = round(lux * 2.75)
        return lux


def demo():
    from machine import Pin, SoftI2C
    from time import sleep_ms

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
    lux = bh1750.illumination()
    print("Lux:", lux)


if __name__ == "__main__":
    demo()
