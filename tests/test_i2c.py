import sys
import periphery
from .asserts import AssertRaises

if sys.version_info[0] == 3:
    raw_input = input

i2c_devpath = None


def test_arguments():
    print("Starting arguments test...")

    # Open with invalid type
    with AssertRaises(TypeError):
        periphery.I2C(123)

    print("Arguments test passed.")


def test_open_close():
    print("Starting open/close test...")

    # Open non-existent device
    with AssertRaises(periphery.I2CError):
        periphery.I2C("/foo/bar")

    # Open legitimate device
    i2c = periphery.I2C(i2c_devpath)
    assert i2c.fd > 0

    # Close I2C
    i2c.close()

    print("Open/close test passed.")


def test_loopback():
    print("Starting loopback test...")

    print("No general way to do a loopback test for I2C without a real component, skipping...")

    print("Loopback test passed.")


def test_interactive():
    print("Starting interactive test...")

    # Open device 2
    i2c = periphery.I2C(i2c_devpath)

    print("")
    print("Starting interactive test. Get out your logic analyzer, buddy!")
    raw_input("Press enter to continue...")

    # There isn't much we can do without assuming a device on the other end,
    # because I2C needs an acknowledgement bit on each transferred byte.
    #
    # But we can send a transaction and expect it to time out.

    # S [ 0x7a W ] [0xaa] [0xbb] [0xcc] [0xdd] NA
    messages = [periphery.I2C.Message([0xaa, 0xbb, 0xcc, 0xdd])]

    raw_input("Press enter to start transfer...")

    # Transfer to non-existent device
    with AssertRaises(periphery.I2CError):
        i2c.transfer(0x7a, messages)

    i2c.close()

    success = raw_input("I2C transfer occurred? y/n ")
    assert success == "y"

    print("Interactive test passed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m tests.test_i2c <i2c device>")
        print("")
        print(" i2c device          i2c device path for observation with an oscilloscope or logic analyzer")
        print("")
        print("Hint: for BeagleBone Black, use")
        print("I2C1 (SCL=P9.24, SDA=P9.26) on /dev/i2c-2, and run this test:")
        print("    python -m tests.test_i2c /dev/i2c-2")
        sys.exit(1)

    i2c_devpath = sys.argv[1]

    print("Starting I2C tests...")

    test_arguments()
    test_open_close()
    test_loopback()
    test_interactive()

    print("All I2C tests passed.")
