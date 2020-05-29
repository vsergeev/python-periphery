import os
import sys
import time

import periphery
from .test import ptest, pokay, passert, AssertRaises

if sys.version_info[0] == 3:
    raw_input = input


PAGE_SIZE = 4096
CONTROL_MODULE_BASE = 0x44e10000
USB_VID_PID_OFFSET = 0x7f4
USB_VID_PID = 0x04516141
RTCSS_BASE = 0x44e3e000
RTC_SCRATCH2_REG_OFFSET = 0x68
RTC_KICK0R_REG_OFFSET = 0x6C
RTC_KICK1R_REG_OFFSET = 0x70


def test_arguments():
    ptest()


def test_open_close():
    ptest()

    # Open aligned base
    mmio = periphery.MMIO(CONTROL_MODULE_BASE, PAGE_SIZE)
    # Check properties
    passert("property base", mmio.base == CONTROL_MODULE_BASE)
    passert("property size", mmio.size == PAGE_SIZE)
    # Try to write immutable properties
    with AssertRaises("write immutable", AttributeError):
        mmio.base = 1000
    with AssertRaises("write immutable", AttributeError):
        mmio.size = 1000
    mmio.close()

    # Open unaligned base
    mmio = periphery.MMIO(CONTROL_MODULE_BASE + 123, PAGE_SIZE)
    # Check properties
    passert("property base", mmio.base == CONTROL_MODULE_BASE + 123)
    passert("property size", mmio.size == PAGE_SIZE)
    # Read out of bounds
    with AssertRaises("read 1 byte over", ValueError):
        mmio.read32(PAGE_SIZE - 3)
    with AssertRaises("read 2 bytes over", ValueError):
        mmio.read32(PAGE_SIZE - 2)
    with AssertRaises("read 3 bytes over", ValueError):
        mmio.read32(PAGE_SIZE - 1)
    with AssertRaises("read 4 bytes over", ValueError):
        mmio.read32(PAGE_SIZE)
    mmio.close()


def test_loopback():
    ptest()

    # Open control module
    mmio = periphery.MMIO(CONTROL_MODULE_BASE, PAGE_SIZE)

    # Read and compare USB VID/PID with read32()
    passert("compare USB VID/PID", mmio.read32(USB_VID_PID_OFFSET) == USB_VID_PID)
    # Read and compare USB VID/PID with bytes read
    data = mmio.read(USB_VID_PID_OFFSET, 4)
    data = bytearray(data)
    passert("compare byte 1", data[0] == USB_VID_PID & 0xff)
    passert("compare byte 2", data[1] == (USB_VID_PID >> 8) & 0xff)
    passert("compare byte 3", data[2] == (USB_VID_PID >> 16) & 0xff)
    passert("compare byte 4", data[3] == (USB_VID_PID >> 24) & 0xff)

    mmio.close()

    # Open RTC subsystem
    mmio = periphery.MMIO(RTCSS_BASE, PAGE_SIZE)

    # Disable write protection
    mmio.write32(RTC_KICK0R_REG_OFFSET, 0x83E70B13)
    mmio.write32(RTC_KICK1R_REG_OFFSET, 0x95A4F1E0)

    # Write/Read RTC Scratch2 Register
    mmio.write32(RTC_SCRATCH2_REG_OFFSET, 0xdeadbeef)
    passert("compare write 32-bit uint and readback", mmio.read32(RTC_SCRATCH2_REG_OFFSET) == 0xdeadbeef)

    # Write/Read RTC Scratch2 Register with bytes write
    mmio.write(RTC_SCRATCH2_REG_OFFSET, b"\xaa\xbb\xcc\xdd")
    data = mmio.read(RTC_SCRATCH2_REG_OFFSET, 4)
    passert("compare write 4-byte bytes and readback", data == b"\xaa\xbb\xcc\xdd")

    # Write/Read RTC Scratch2 Register with bytearray write
    mmio.write(RTC_SCRATCH2_REG_OFFSET, bytearray(b"\xbb\xcc\xdd\xee"))
    data = mmio.read(RTC_SCRATCH2_REG_OFFSET, 4)
    passert("compare write 4-byte bytearray and readback", data == b"\xbb\xcc\xdd\xee")

    # Write/Read RTC Scratch2 Register with list write
    mmio.write(RTC_SCRATCH2_REG_OFFSET, [0xcc, 0xdd, 0xee, 0xff])
    data = mmio.read(RTC_SCRATCH2_REG_OFFSET, 4)
    passert("compare write 4-byte list and readback", data == b"\xcc\xdd\xee\xff")

    # Write/Read RTC Scratch2 Register with 16-bit write
    mmio.write16(RTC_SCRATCH2_REG_OFFSET, 0xaabb)
    passert("compare write 16-bit uint and readback", mmio.read16(RTC_SCRATCH2_REG_OFFSET) == 0xaabb)

    # Write/Read RTC Scratch2 Register with 8-bit write
    mmio.write8(RTC_SCRATCH2_REG_OFFSET, 0xab)
    passert("compare write 8-bit uint and readback", mmio.read8(RTC_SCRATCH2_REG_OFFSET) == 0xab)

    mmio.close()


def test_interactive():
    ptest()

    mmio = periphery.MMIO(RTCSS_BASE, PAGE_SIZE)

    # Check tostring
    print("MMIO description: {}".format(str(mmio)))
    passert("interactive success", raw_input("MMIO description looks ok? y/n ") == "y")

    print("Waiting for seconds ones digit to reset to 0...\n")

    # Wait until seconds low go to 0, so we don't have to deal with
    # overflows in comparing times
    tic = time.time()
    while mmio.read32(0x00) & 0xf != 0:
        periphery.sleep(1)
        passert("less than 12 seconds elapsed", (time.time() - tic) < 12)

    # Compare passage of OS time with RTC time

    tic = time.time()
    rtc_tic = mmio.read32(0x00) & 0xf

    bcd2dec = lambda x: 10 * ((x >> 4) & 0xf) + (x & 0xf)

    print("Date: {:04d}-{:02d}-{:02d}".format(2000 + bcd2dec(mmio.read32(0x14)), bcd2dec(mmio.read32(0x10)), bcd2dec(mmio.read32(0x0c))))
    print("Time: {:02d}:{:02d}:{:02d}".format(bcd2dec(mmio.read32(0x08) & 0x7f), bcd2dec(mmio.read32(0x04)), bcd2dec(mmio.read32(0x00))))

    periphery.sleep(3)

    print("Date: {:04d}-{:02d}-{:02d}".format(2000 + bcd2dec(mmio.read32(0x14)), bcd2dec(mmio.read32(0x10)), bcd2dec(mmio.read32(0x0c))))
    print("Time: {:02d}:{:02d}:{:02d}".format(bcd2dec(mmio.read32(0x08) & 0x7f), bcd2dec(mmio.read32(0x04)), bcd2dec(mmio.read32(0x00))))

    toc = time.time()
    rtc_toc = mmio.read32(0x00) & 0xf

    passert("real time elapsed", (toc - tic) > 2)
    passert("rtc time elapsed", (rtc_toc - rtc_tic) > 2)

    mmio.close()


if __name__ == "__main__":
    if os.environ.get("CI") == "true":
        test_arguments()
        sys.exit(0)

    print("WARNING: This test suite assumes a BeagleBone Black (AM335x) host!")
    print("Other systems may experience unintended and dire consequences!")
    raw_input("Press enter to continue!")

    test_arguments()
    pokay("Arguments test passed.")
    test_open_close()
    pokay("Open/close test passed.")
    test_loopback()
    pokay("Loopback test passed.")
    test_interactive()
    pokay("Interactive test passed.")

    pokay("All tests passed!")
