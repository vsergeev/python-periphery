import sys
import periphery
from .asserts import AssertRaises

if sys.version_info[0] == 3:
    raw_input = input

i2c_devpath1 = None
i2c_devpath2 = None
i2c_eeprom_addr = None

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
    i2c = periphery.I2C(i2c_devpath1)
    assert i2c.fd > 0

    # Close I2C
    i2c.close()

    print("Open/close test passed.")

def test_loopback():
    print("Starting loopback test...")

    # "Loopback" plan
    # 1. Read EEPROM via sysfs
    # 2. Read EEPROM via I2C
    # 3. Compare data

    # Read EEPROM via sysfs
    sysfs_path = "/sys/bus/i2c/devices/%s-00%02x/eeprom" % (i2c_devpath1[-1], i2c_eeprom_addr)
    with open(sysfs_path, "rb") as f:
        eeprom_data = f.read(256)

    # Read EEPROM via I2C
    data = bytearray()
    i2c = periphery.I2C(i2c_devpath1)
    for addr in range(0, 256):
        msgs = [periphery.I2C.Message([0x00, addr]), periphery.I2C.Message([0x00], read=True)]
        i2c.transfer(i2c_eeprom_addr, msgs)
        data.append(msgs[1].data[0])

    # Compare data
    assert eeprom_data == data

    # Try bytes read
    msgs = [periphery.I2C.Message(b"\x00\x00"), periphery.I2C.Message(b"\x00", read=True)]
    i2c.transfer(i2c_eeprom_addr, msgs)
    assert isinstance(msgs[1].data, bytes)
    assert bytearray(msgs[1].data)[0] == data[0]

    # Try bytearray read
    msgs = [periphery.I2C.Message(bytearray([0x00, 0x00])), periphery.I2C.Message(bytearray([0x00]), read=True)]
    i2c.transfer(i2c_eeprom_addr, msgs)
    assert isinstance(msgs[1].data, bytearray)
    assert msgs[1].data[0] == data[0]

    i2c.close()

    print("Loopback test passed.")

def test_interactive():
    print("Starting interactive test...")

    # Open device 2
    i2c = periphery.I2C(i2c_devpath2)

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
    if len(sys.argv) < 4:
        print("Usage: python -m tests.test_i2c <i2c device 1> <i2c device 2> <i2c eeprom address>")
        print("")
        print(" i2c device 1        i2c device path with EEPROM on bus")
        print(" i2c device 2        i2c device path for observation with logic analyzer / oscilloscope")
        print(" i2c eeprom address  address of EEPROM on i2c device 1 bus")
        print("")
        print("Hint: for BeagleBone Black, use onboard EEPROM on /dev/i2c-0 and")
        print("I2C1 (SCL=P9.24, SDA=P9.26) on /dev/i2c-2, and run this test:")
        print("    python -m tests.test_i2c /dev/i2c-0 /dev/i2c-2 0x50")
        sys.exit(1)

    i2c_devpath1 = sys.argv[1]
    i2c_devpath2 = sys.argv[2]
    i2c_eeprom_addr = int(sys.argv[3], 0)

    print("Starting I2C tests...")

    test_arguments()
    test_open_close()
    test_loopback()
    test_interactive()

    print("All I2C tests passed.")

