# python-periphery [![Build Status](https://travis-ci.org/vsergeev/python-periphery.svg?branch=master)](https://travis-ci.org/vsergeev/python-periphery) [![Docs Status](https://readthedocs.org/projects/python-periphery/badge/)](https://python-periphery.readthedocs.io/en/latest/) [![GitHub release](https://img.shields.io/github/release/vsergeev/python-periphery.svg?maxAge=7200)](https://github.com/vsergeev/python-periphery) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/vsergeev/python-periphery/blob/master/LICENSE)

## Linux Peripheral I/O (GPIO, LED, PWM, SPI, I2C, MMIO, Serial) with Python 2 & 3

python-periphery is a pure Python library for GPIO, LED, PWM, SPI, I2C, MMIO, and Serial peripheral I/O interface access in userspace Linux. It is useful in embedded Linux environments (including Raspberry Pi, BeagleBone, etc. platforms) for interfacing with external peripherals. python-periphery is compatible with Python 2 and Python 3, is written in pure Python, and is MIT licensed.

Using Lua or C? Check out the [lua-periphery](https://github.com/vsergeev/lua-periphery) and [c-periphery](https://github.com/vsergeev/c-periphery) projects.

Contributed libraries: [java-periphery](https://github.com/sgjava/java-periphery), [dart_periphery](https://github.com/pezi/dart_periphery)

## Installation

With pip:
``` text
pip install python-periphery
```

With easy_install:
``` text
easy_install python-periphery
```

With setup.py:
``` text
git clone https://github.com/vsergeev/python-periphery.git
cd python-periphery
python setup.py install
```

## Examples

### GPIO

``` python
from periphery import GPIO

# Open GPIO /dev/gpiochip0 line 10 with input direction
gpio_in = GPIO("/dev/gpiochip0", 10, "in")
# Open GPIO /dev/gpiochip0 line 12 with output direction
gpio_out = GPIO("/dev/gpiochip0", 12, "out")

value = gpio_in.read()
gpio_out.write(not value)

gpio_in.close()
gpio_out.close()
```

[Go to GPIO documentation.](https://python-periphery.readthedocs.io/en/latest/gpio.html)

### LED

``` python
from periphery import LED

# Open LED "led0" with initial state off
led0 = LED("led0", False)
# Open LED "led1" with initial state on
led1 = LED("led1", True)

value = led0.read()
led1.write(value)

# Set custom brightness level
led1.write(led1.max_brightness / 2)

led0.close()
led1.close()
```

[Go to LED documentation.](https://python-periphery.readthedocs.io/en/latest/led.html)

### PWM

``` python
from periphery import PWM

# Open PWM chip 0, channel 10
pwm = PWM(0, 10)

# Set frequency to 1 kHz
pwm.frequency = 1e3
# Set duty cycle to 75%
pwm.duty_cycle = 0.75

pwm.enable()

# Change duty cycle to 50%
pwm.duty_cycle = 0.50

pwm.close()
```

[Go to PWM documentation.](https://python-periphery.readthedocs.io/en/latest/pwm.html)

### SPI

``` python
from periphery import SPI

# Open spidev1.0 with mode 0 and max speed 1MHz
spi = SPI("/dev/spidev1.0", 0, 1000000)

data_out = [0xaa, 0xbb, 0xcc, 0xdd]
data_in = spi.transfer(data_out)

print("shifted out [0x{:02x}, 0x{:02x}, 0x{:02x}, 0x{:02x}]".format(*data_out))
print("shifted in  [0x{:02x}, 0x{:02x}, 0x{:02x}, 0x{:02x}]".format(*data_in))

spi.close()
```

[Go to SPI documentation.](https://python-periphery.readthedocs.io/en/latest/spi.html)

### I2C

``` python
from periphery import I2C

# Open i2c-0 controller
i2c = I2C("/dev/i2c-0")

# Read byte at address 0x100 of EEPROM at 0x50
msgs = [I2C.Message([0x01, 0x00]), I2C.Message([0x00], read=True)]
i2c.transfer(0x50, msgs)
print("0x100: 0x{:02x}".format(msgs[1].data[0]))

i2c.close()
```

[Go to I2C documentation.](https://python-periphery.readthedocs.io/en/latest/i2c.html)

### MMIO

``` python
from periphery import MMIO

# Open am335x real-time clock subsystem page
rtc_mmio = MMIO(0x44E3E000, 0x1000)

# Read current time
rtc_secs = rtc_mmio.read32(0x00)
rtc_mins = rtc_mmio.read32(0x04)
rtc_hrs = rtc_mmio.read32(0x08)

print("hours: {:02x} minutes: {:02x} seconds: {:02x}".format(rtc_hrs, rtc_mins, rtc_secs))

rtc_mmio.close()

# Open am335x control module page
ctrl_mmio = MMIO(0x44E10000, 0x1000)

# Read MAC address
mac_id0_lo = ctrl_mmio.read32(0x630)
mac_id0_hi = ctrl_mmio.read32(0x634)

print("MAC address: {:04x}{:08x}".format(mac_id0_lo, mac_id0_hi))

ctrl_mmio.close()
```

[Go to MMIO documentation.](https://python-periphery.readthedocs.io/en/latest/mmio.html)

### Serial

``` python
from periphery import Serial

# Open /dev/ttyUSB0 with baudrate 115200, and defaults of 8N1, no flow control
serial = Serial("/dev/ttyUSB0", 115200)

serial.write(b"Hello World!")

# Read up to 128 bytes with 500ms timeout
buf = serial.read(128, 0.5)
print("read {:d} bytes: _{:s}_".format(len(buf), buf))

serial.close()
```

[Go to Serial documentation.](https://python-periphery.readthedocs.io/en/latest/serial.html)

## Documentation

Documentation is hosted at [https://python-periphery.readthedocs.io](https://python-periphery.readthedocs.io).

To build documentation locally with Sphinx, run:

```
cd docs
make html
```

Sphinx will produce the HTML documentation in `docs/_build/html/`.

Run `make help` to see other output targets (LaTeX, man, text, etc.).

## Testing

The tests located in the [tests](tests/) folder may be run under Python to test the correctness and functionality of python-periphery. Some tests require interactive probing (e.g. with an oscilloscope), the installation of a physical loopback, or the existence of a particular device on a bus. See the usage of each test for more details on the required setup.

## License

python-periphery is MIT licensed. See the included [LICENSE](LICENSE) file.

