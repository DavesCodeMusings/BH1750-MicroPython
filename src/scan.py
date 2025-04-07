# Scan for I2C devices and print addresses found

from machine import Pin, SoftI2C

# Values for ESP32 Devkit V1 (30-pin board with four corner mounting holes)
# Adjust as needed for other boards.
I2C_CLOCK = 22
I2C_DATA = 21

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))

print('Scanning i2c bus...')
devices = i2c.scan()

if (len(devices) == 0):
    print("No i2c device found!")
else:
    print("Devices found:", len(devices))
    for address in devices:  
        print("Address:", hex(address))
