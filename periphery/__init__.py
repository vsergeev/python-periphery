__version__ = "1.0.0"
"Module version string"

version = (1,0,0)
"Module version tuple"

import time

def sleep(seconds):
    time.sleep(seconds)

def sleep_ms(milliseconds):
    time.sleep(milliseconds / 1000.0)

def sleep_us(microseconds):
    time.sleep(microseconds / 1000000.0)

from periphery.gpio import GPIO, GPIOException
from periphery.spi import SPI, SPIException
from periphery.i2c import I2C, I2CException
from periphery.mmio import MMIO, MMIOException
from periphery.serial import Serial, SerialException

