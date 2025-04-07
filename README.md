# I2C Development with MicroPython and the BH1750
This project is both a device driver and an I2C tutorial -- a destination and a journey. The destination is a MicroPython module for reading the BH1750 ambient light sensor. The journey is showing step by step how to create your own driver for an Inter-Integrated Circuit (I2C) communication enabled device.

> If all you want is the device driver, do `mip install github:DavesCodeMusings/BH1750-MicroPython`

## Why the BH1750?
I wanted a device to communicate light readings to my home automation system. It's easy enough to find a tutorial on wiring a photoresistor to a microcontroller's analog to digital converter and then calibrate what reading constitutes dark and what indicates light. But the inexpensive BH1750 can read illumination and provide a result in Lux, a standard SI unit, via the I2C bus.

I also knew there were [other MicroPython libraries for the BH1750](https://github.com/flrrth/pico-bh1750) and even an [ESPHome option](https://esphome.io/components/sensor/bh1750.html). In case I got stuck along my journey of creating my own, I'd have something to fall back on.

But it turns out I2C is not too tough. The trick is understanding how to provide configuration parameters to the device and interpreting the data it returns. For that, we'll use the device's [datasheet](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6165/bh1750fvi-e.pdf). But first, let's get the hardware hooked up.

## Wiring to a Microcontroller
I'm using an ESP32 Devkit v1. It's the one with 30-pins and four corner mounting holes that's known to be a bit too wide for convenient breadboarding. But it's cheap and plentiful, and I'm skipping the breadboard to attach dupont connectors directly to pin headers, so it works.

For this ESP32 board, the pinout shows GPIO22 as the I2C clock and GPIO23 as the I2C data. I'll attach these to the similarly named connections on the BH1750.

The only other connections on the BH1750 are Vcc, GND, and ADDR, for power, ground, and address selection, respectively. The Vcc goes to the ESP32's 3.3V pin, GND goes to GND, and ADDR is attached to another GND pin to pull it low.

## Setting up the I2C Bus in MicroPython
If you've ever used an I2C device in MicroPython, you're probably familar with the following bit of code.

```py
from machine import Pin, SoftI2C

I2C_CLOCK = 22
I2C_DATA = 21

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))
```

This sets up the I2C bus using the clock and data GPIOs provided by the ESP32 devkit v1's pinout diagram.

## Scanning for the Device
When communicating with I2C devices, we need to know the device's address. We can either turn to the datasheet for this information or we can simply scan the I2C bus to see if any devices respond.

To do that, the bit of code below can be added after the I2C setup.

```py
print('Scanning i2c bus...')
devices = i2c.scan()

if (len(devices) == 0):
    print("No i2c device found!")
else:
    print("Devices found:", len(devices))
    for address in devices:  
        print("Address:", hex(address))
```

> The entire program is available as [scan.py](src/scan.py) in the /src directory of this repository.

If everything is wired up correctly, you should see output like what's shown below.

```
Scanning i2c bus...
Devices found: 1
Address: 0x23
```

Take note of the address. And if you see _No i2c device found_, check your wiring before moving on.

## How to Take a Light Reading?
With the device wired up and recognized by the I2C bus scan, we're ready to start taking light readings. But how?

For that, we turn to the datasheet. In the document, under the heading of Measurement Procedure, there is a flow chart that shows the procedure. It starts with application of power and ground to the device and goes from there.

Here are the steps:

1. Send a Power On command
2. Send a Measurement command
3. Wait for the measurement
4. Read the result

> The device returns to a Power Off state automatically after taking a measurement, so there's no need for a step 5.

Let's take a look at each of the steps in detail.

### Sending a Power On command
This seems a little silly sending a Power On command as the first step after supplying Vcc and GND to the device. But, reading the datasheet shows the device will start up in Power Down mode when Vcc is first applied. So we need to turn it on first.

Under the Instruction Set heading in the datasheet, we see a opcodes (labled as opecodes in a typographical error.) These will tell us what needs to be sent to instruct the device to do certain tasks.

The first opcode (0000_0000) is the Power Down instruction. We can skip that, because we already know the device starts in Power Down mode.

The second opcode (0000_0001) is Power On. Bingo! That's the one we want for this first step.

Sending the opcode is pretty easy using MicroPython's I2C class method `writeto()`.

We already created an instance of the class with the line `i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))` at the beginning of our program. So all we have to do is use `i2c.writeto()` with the proper parameters.

The [documentation for writeto()](https://docs.micropython.org/en/latest/library/machine.I2C.html#machine.I2C.writeto) says it needs an address and a buffer. It can take some additional parameters, but there's no need to go beyond the default values for what we want to do.

We know the address from running the I2C bus scan. It's 0x23 (and will stay 0x23 unless we change the connection on the ADDR wire for the device.) What we don't have is a buffer. What the heck is a buffer anyway?

In our case, the buffer in question is just a bytes object containing the Power On command we want to send. We can get a bytes object using MicroPython's `to_bytes()` method.

Let's review our code thus far and remove the portion that does the scanning.

We're back to this:

```py
from machine import Pin, SoftI2C

I2C_CLOCK = 22
I2C_DATA = 21

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))
```

Now let's add in the device address as a constant, a constant to represent the Power On opcode, and the`write_to()` method that brings it all together.

```py
from machine import Pin, SoftI2C
from mycropython import const

# Values for ESP32 Devkit V1 (30-pin board with four corner mounting holes)
# Adjust as needed for other boards.
I2C_CLOCK = const(22)
I2C_DATA = const(21)
I2C_ADDR = cont(0x23)

# BH1750 opcodes
POWER_ON = const(0b_0000_0001)

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))
i2c.writeto(I2C_ADDR, POWER_ON.to_bytes())
```

You can run it just to make sure there are no errors, but it won't do anything much. We have to send a Measurement command for anthing exciting to happen.

### Sending a Measurement command
Going back to the BH1750 datasheet's flow chart for a moment, we'll see a decision point. The choices are One Time Measurement or Continuous Measurement. We'll configure for one-time and high resolution readings. In the Instruction Set opcode table, this is called One Time H-Resolution Mode, and the opcode is 0010_0000.

To take a One Time H-Resolution reading, we simply send the opcode using the same `writeto()` method we used to send the Power On command.

```
ONE_TIME_HRES = const(0b_0010_0000)
i2c.writeto(I2C_ADDR, ONE_TIME_HRES.to_bytes())
```

According to the datasheet, using H-Resolution mode gives reading is units of One Lux. A little farther down, it's also noted that H-Resolution mode is recommended for good noise rejection.

Here's the code so far.

```py
from machine import Pin, SoftI2C
from mycropython import const

# Values for ESP32 Devkit V1 (30-pin board with four corner mounting holes)
# Adjust as needed for other boards.
I2C_CLOCK = const(22)
I2C_DATA = const(21)
I2C_ADDR = cont(0x23)

# BH1750 opcodes
POWER_ON = const(0b_0000_0001)
ONE_TIME_HRES = const(0b_0010_0000)

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))
i2c.writeto(I2C_ADDR, POWER_ON.to_bytes())
i2c.writeto(I2C_ADDR, ONE_TIME_HRES.to_bytes())
```

After sending the command, all we have to do is wait for the device to take a measurement.

### Waiting for the Measurement
This step should not be surprising. If you've ever used a sensor device, they almost always need some time to do their job. The venerable DHT22 takes about two seconds. The BH1750 datasheet says it can take a One-Time H-Resolution Mode measurement in 120 mS. Pretty fast.

120mS is also a _typical_ wait time. A closer look at the datasheet's Electrical Characteristics table shows the H-Resolution Mode
Measurement Time can be up to 180mS. So we need to wait 180mS. Pretty easy with the addition of a call to `sleep_ms()`.

Here's the code with the addition of the wait time.

```py
from machine import Pin, SoftI2C
from mycropython import const
from time import sleep_ms

# Values for ESP32 Devkit V1 (30-pin board with four corner mounting holes)
# Adjust as needed for other boards.
I2C_CLOCK = const(22)
I2C_DATA = const(21)
I2C_ADDR = cont(0x23)

# BH1750 opcodes
POWER_ON = const(0b_0000_0001)
ONE_TIME_HRES = const(0b_0010_0000)

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))
i2c.writeto(I2C_ADDR, POWER_ON.to_bytes())
i2c.writeto(I2C_ADDR, ONE_TIME_HRES.to_bytes())
sleep_ms(180)
```

After 180mS of patience, we can get our measurement.

### Reading the result
The I2C bus is bi-directional. We don't need any special setup to read from it. All it takes is another class method. We'll be using `readfrom()` and passing in parameters for the I2C address and the number of bytes we're expecting. The datasheet says a 2-byte value will be returned, so our next statement will be `result = i2c.readfrom(I2C_ADDR, 2)`

With that line added, the code now looks like this:

```py
from machine import Pin, SoftI2C
from mycropython import const
from time import sleep_ms

# Values for ESP32 Devkit V1 (30-pin board with four corner mounting holes)
# Adjust as needed for other boards.
I2C_CLOCK = const(22)
I2C_DATA = const(21)
I2C_ADDR = cont(0x23)

# BH1750 opcodes
POWER_ON = const(0b_0000_0001)
ONE_TIME_HRES = const(0b_0010_0000)

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))
i2c.writeto(I2C_ADDR, POWER_ON.to_bytes())
i2c.writeto(I2C_ADDR, ONE_TIME_HRES.to_bytes())
sleep_ms(180)
result = i2c.readfrom(I2C_ADDR, 2)
```

If we wanted to print the result, we could use `print("Result:", result.hex())`, but believe it or not, the result would not be in units of Lux. More about that follows.

## Adjusting for Measurement Accuracy
Turning again to the Electrical Characteristics table of the datasheet, we see a row labeled Measurement Accuracy. In the rightmost column we see, Sensor Out / Actual Lux. And in the middle columns of the table we see the number 1.2 as a typical limit.

Farther down in the Measurement Sequence Examples, we see 1.2 mentioned again. This time it's in a note saying to divide the returned result by 1.2 to get units of Lux. So we need to do that.

But we can just go dividing a buffer by a floating-point number. Trying that will give an error. First we need to convert the bytes buffer to a number, specifically an integer, because that's what is returned. We can do this using `int.from_bytes(result)`. Then we can divide by 1.2 and do any other math operations we want.

So in the end, the adjustment looks like this:

```py
lux = round(int.from_bytes(result) / 1.2)
```

Taking all the code into account, we now have what's shown below.

```py
from machine import Pin, SoftI2C
from mycropython import const
from time import sleep_ms

# Values for ESP32 Devkit V1 (30-pin board with four corner mounting holes)
# Adjust as needed for other boards.
I2C_CLOCK = const(22)
I2C_DATA = const(21)
I2C_ADDR = cont(0x23)

# BH1750 opcodes
POWER_ON = const(0b_0000_0001)
ONE_TIME_HRES = const(0b_0010_0000)

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))
i2c.writeto(I2C_ADDR, POWER_ON.to_bytes())
i2c.writeto(I2C_ADDR, ONE_TIME_HRES.to_bytes())
sleep_ms(180)
result = i2c.readfrom(I2C_ADDR, 2)
lux = round(int.from_bytes(result) / 1.2)

print("Lux reading:", lux)
```

Indoors on a clear day, with the sensor pointed toward a north facing window, I got this:

```
Lux reading: 165
```

With the sensor toward the center of the room, pointed upward, I got a 70 Lux reading.

## Accounting for the Dome
The BH1750 I purchased is encased in a white hemispherical dome. This is supposed to help diffuse the incoming light and make the angle of incidence less of a factor in the reading. But, it also reduces the ammount of light coming in. While not critical for my application, I was curious about how much of an effect the dome has.

It turns out [someone else on the internet](https://thecavepearlproject.org/2024/08/10/using-a-bh1750-lux-sensor-to-measure-par/) was curious about this too, and geek out way harder on it than I did.

To make a long blog post short, 110 Lux reported by a sensor with no dome was reported as 40 Lux with the dome. That's a reduction factor of 2.75x because of the dome.

I also used [Lux meter app](https://play.google.com/store/apps/details?id=com.doggoapps.luxlight) on my phone to do a quick and dirty comparison. My phone varied wildly with even a slight change of angle. I got readings from the Lux Meter app of 90 to 150 vs 76 from the domed sensor. So with my crude methods, it was a factor of about 2x.

Because I have no idea what the quality of the light sensor is for my phone, I'm more inclined to go with the 2.75x factor found by the author comparing the same sensor both with and without a dome.

For the code, I could have a boolean variable `DIFFUSION_DOME` to determine if the correction should be made or not.

Adding that to the code so far would give what's shown below.

```py
from machine import Pin, SoftI2C
from mycropython import const
from time import sleep_ms

# Values for ESP32 Devkit V1 (30-pin board with four corner mounting holes)
# Adjust as needed for other boards.
I2C_CLOCK = const(22)
I2C_DATA = const(21)
I2C_ADDR = cont(0x23)

# Does the sensor have a dome?
DIFFUSION_DOME = const(True)

# BH1750 opcodes
POWER_ON = const(0b_0000_0001)
ONE_TIME_HRES = const(0b_0010_0000)

i2c = SoftI2C(scl=Pin(I2C_CLOCK), sda=Pin(I2C_DATA))
i2c.writeto(I2C_ADDR, POWER_ON.to_bytes())
i2c.writeto(I2C_ADDR, ONE_TIME_HRES.to_bytes())
sleep_ms(180)
result = i2c.readfrom(I2C_ADDR, 2)
lux = round(int.from_bytes(result) / 1.2)
if DIFFUSION_DOME:
    lux = round(lux * 2.75)

print("Lux reading:", lux)
```

> Also available in the repository as [read_lux.py](src/read_lux.py)

## What's the Significance of the Readings?
There's a [Wikipedia article on Lux](https://en.wikipedia.org/wiki/Lux) that features a table of Lux levels with comparisons to various environents. It ranges from less than 1 Lux for a moonlit night to 100,000 Lux for full, direct daylight. I'm interested in using the sensor for home automation.

Currently, I have some smart plug attached lamps that are scheduled to come on at sunset. So I measured the Lux reported by my BH1750 sensor, in the same position, at sunset as reported by the local weather web site. The BH1750, with dome compensation, measured 14 Lux. The lamp controlled by home automation came on a few seconds later, but did very little to affect the BH1750's reading.

So now I know the indoor light level at sunset, the time at which I've decided I should have the lights come on, is 14 Lux. So what?

My goal for havng an ambient light sensor is to integrate with home automation to turn on lights when it's dark, but not necessarily sunset. Think overcast rainy days. And as the MycroPython program stands now, all that's left is sending the data to the home automation system.

That's something I've worked out with my [BTHome-MicroPython](https://github.com/DavesCodeMusings/BTHome-MicroPython), so I won't rehash it here. But at the beginning of this journey, I promised you a MicroPython module. 

## Writing a MicroPython Module for the BH1750
Creating a driver module for the device consists of taking the existing code and chopping it up into methods that are part of a class representing the BH1750 sensor. Why go to the trouble of creating a class? Theoretically, there could be multiple BH1750 sensors attached to a single microcontroller. The BH1750 can use one of two available addresses and the ESP32 can handle more than one I2C bus. So it makes sense to track the I2C bus and address, as well as diffusion dome or not, in a class instance's properties.

Let's start by looking at the finished product and then point out the differences to the original program.

```py
from micropython import const


class BH1750:
    POWER_ON = const(0b_0000_0001)
    ONE_TIME_HRES = const(0b_0010_0000)
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
```

What's been done above is to take the original program and rearrange the constants and program logic into class variables and methods. Most notably, the sending of Power On and Measurement commands has been placed inside a method called `measure()`, while the reading of the resulting Lux measurement is in the method called `illumination()`

The names of the methods were insprired by the naming of [MicroPython DHT22](https://docs.micropython.org/en/latest/esp32/quickref.html#dht-driver) methods. But rather than temperature and humidity, we have only illumination.

But what's missing inside the class is any reference to the `sleep_ms(180)`. We know it'ss required from reading the BH1750 datasheet. So why is it missing?

The answer to that is for flexibility. Calling `sleep_ms(180)` will cause the program to do nothing for 180 mS. Okay, so what?

Imagine the BH1750 is attached to a microcontroller that uses Bluetooth Low Energy (BLE) to communicate its Lux readings. MicroPython Bluetooth is asynchronous. Doing nothing for 180 mS isn't really compatible with asynchronous program execution.

By splitting the sending of commands from the reading of results, and pulling the sleep_ms function out from the middle of it, we're giving the user a choice. You can call `time.sleep_ms()` and do nothing for 180 mS, or you can `await asyncio.sleep_ms()` and let another async task execute while you wait. And just to make things easier, there's a class variable MEASUREMENT_TIME_mS that removes the burden of remembering just how many milliseconds to wait.

In other changes, we've also moved the setup of the I2C bus outside of the class and into the `demo()` subroutine. This facilitates the idea of possibley having multiple BH1750 sensors attached to a single microcontroller.

Finally, we make the `demo()` subroutine's execution conditional upon whether the file is executed outright or imported as a module. If it's imported, the demo is skipped. So we get the flexibility of running it standalone, without having to code up a `main.py` or similar, but we can also use it as a module without any changes to the code.

## Next Steps
The goal of creating my own I2C device driver has been realized. Now, my plan is to combine this with my [BTHome-MicroPython](https://github.com/DavesCodeMusings/BTHome-MicroPython) project and construct a Bluetooth Low Energy (BLE) beacon that sends ambient light levels to my Home Assistant automation system.

If you made it this far, I hope you got some useful information out of it.
