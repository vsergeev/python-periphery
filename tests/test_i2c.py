import os
import sys

import periphery
from .test import ptest, pokay, passert, AssertRaises

if sys.version_info[0] == 3:
    raw_input = input


i2c_devpath = None


def test_arguments():
    ptest()

    # Open with invalid type
    with AssertRaises("open invalid type", TypeError):
        periphery.I2C(123)


def test_open_close():
    ptest()

    # Open non-existent device
    with AssertRaises("non-existent device", periphery.I2CError):
        periphery.I2C("/foo/bar")

    # Open legitimate device
    i2c = periphery.I2C(i2c_devpath)
    passert("fd >= 0", i2c.fd >= 0)

    # Close I2C
    i2c.close()


def test_loopback():
    ptest()
    # No general way to do a loopback test for I2C without a real component, skipping...


def test_interactive():
    ptest()

    # Open device 2
    i2c = periphery.I2C(i2c_devpath)

    print("")
    print("Starting interactive test. Get out your logic analyzer, buddy!")
    raw_input("Press enter to continue...")

    # Check tostring
    print("I2C description: {}".format(str(i2c)))
    passert("interactive success", raw_input("I2C description looks ok? y/n ") == "y")

    # There isn't much we can do without assuming a device on the other end,
    # because I2C needs an acknowledgement bit on each transferred byte.
    #
    # But we can send a transaction and expect it to time out.

    # S [ 0x7a W ] [0xaa] [0xbb] [0xcc] [0xdd] NA
    messages = [periphery.I2C.Message([0xaa, 0xbb, 0xcc, 0xdd])]

    raw_input("Press enter to start transfer...")

    # Transfer to non-existent device
    with AssertRaises("transfer to non-existent device", periphery.I2CError):
        i2c.transfer(0x7a, messages)

    i2c.close()

    success = raw_input("I2C transfer occurred? y/n ")
    passert("interactive success", success == "y")


if __name__ == "__main__":
    if os.environ.get("CI") == "true":
        test_arguments()
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Usage: python -m tests.test_i2c <i2c device>")
        print("")
        print("[1/4] Arguments test: No requirements.")
        print("[2/4] Open/close test: I2C device should be real.")
        print("[3/4] Loopback test: No test.")
        print("[4/4] Interactive test: I2C bus should be observed with an oscilloscope or logic analyzer.")
        print("")
        print("Hint: for Raspberry Pi 3, enable I2C1 with:")
        print("   $ echo \"dtparam=i2c_arm=on\" | sudo tee -a /boot/config.txt")
        print("   $ sudo reboot")
        print("Use pins I2C1 SDA (header pin 2) and I2C1 SCL (header pin 3),")
        print("and run this test with:")
        print("    python -m tests.test_i2c /dev/i2c-1")
        print("")
        sys.exit(1)

    i2c_devpath = sys.argv[1]

    test_arguments()
    pokay("Arguments test passed.")
    test_open_close()
    pokay("Open/close test passed.")
    test_loopback()
    pokay("Loopback test passed.")
    test_interactive()
    pokay("Interactive test passed.")

    pokay("All tests passed!")
