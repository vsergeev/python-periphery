import os
import sys
import time

import periphery
from .test import ptest, pokay, passert, AssertRaises

if sys.version_info[0] == 3:
    raw_input = input


serial_device = None


def test_arguments():
    ptest()

    # Invalid data bits
    with AssertRaises("invalid databits", ValueError):
        periphery.Serial("/dev/ttyS0", 115200, databits=4)
    with AssertRaises("invalid databits", ValueError):
        periphery.Serial("/dev/ttyS0", 115200, databits=9)
    # Invalid parity
    with AssertRaises("invalid parity", ValueError):
        periphery.Serial("/dev/ttyS0", 115200, parity="blah")
    # Invalid stop bits
    with AssertRaises("invalid stop bits", ValueError):
        periphery.Serial("/dev/ttyS0", 115200, stopbits=0)
    with AssertRaises("invalid stop bits", ValueError):
        periphery.Serial("/dev/ttyS0", 115200, stopbits=3)

    # Everything else is fair game, although termios might not like it.


def test_open_close():
    ptest()

    serial = periphery.Serial(serial_device, 115200)

    # Confirm default settings
    passert("fd > 0", serial.fd > 0)
    passert("baudrate is 115200", serial.baudrate == 115200)
    passert("databits is 8", serial.databits == 8)
    passert("parity is none", serial.parity == "none")
    passert("stopbits is 1", serial.stopbits == 1)
    passert("xonxoff is False", serial.xonxoff == False)
    passert("rtscts is False", serial.rtscts == False)
    passert("vmin is 0", serial.vmin == 0)
    passert("vtime is 0", serial.vtime == 0)

    # Change some stuff and check that it changed
    serial.baudrate = 4800
    passert("baudrate is 4800", serial.baudrate == 4800)
    serial.baudrate = 9600
    passert("baudrate is 9600", serial.baudrate == 9600)
    serial.databits = 7
    passert("databits is 7", serial.databits == 7)
    serial.parity = "odd"
    passert("parity is odd", serial.parity == "odd")
    serial.stopbits = 2
    passert("stopbits is 2", serial.stopbits == 2)
    serial.xonxoff = True
    passert("xonxoff is True", serial.xonxoff == True)
    # Test serial port may not support rtscts
    serial.vmin = 50
    passert("vmin is 50", serial.vmin == 50)
    serial.vtime = 15.3
    passert("vtime is 15.3", abs(serial.vtime - 15.3) < 0.1)

    serial.close()


def test_loopback():
    ptest()

    lorem_ipsum = b"Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

    serial = periphery.Serial(serial_device, 115200)

    # Test write/flush/read with bytes write
    print("Write, flush, read lorem ipsum with bytes type")
    passert("wrote lorem ipsum bytes", serial.write(lorem_ipsum) == len(lorem_ipsum))
    serial.flush()
    buf = serial.read(len(lorem_ipsum), timeout=3)
    passert("compare readback lorem ipsum", buf == lorem_ipsum)

    # Test write/flush/read with bytearray write
    print("Write, flush, read lorem ipsum with bytearray type")
    passert("wrote lorem ipsum bytearray", serial.write(bytearray(lorem_ipsum)) == len(lorem_ipsum))
    serial.flush()
    buf = serial.read(len(lorem_ipsum), timeout=3)
    passert("compare readback lorem ipsum", buf == lorem_ipsum)

    # Test write/flush/read with list write
    print("Write, flush, read lorem ipsum with list type")
    passert("write lorem ipsum list", serial.write(list(bytearray(lorem_ipsum))) == len(lorem_ipsum))
    serial.flush()
    buf = serial.read(len(lorem_ipsum), timeout=3)
    passert("compare readback lorem ipsum", buf == lorem_ipsum)

    # Test poll/write/flush/poll/input waiting/read
    print("Write, flush, poll, input waiting, read lorem ipsum")
    passert("poll timed out", serial.poll(0.5) == False)
    passert("write lorem ipsum", serial.write(lorem_ipsum) == len(lorem_ipsum))
    serial.flush()
    passert("poll succeeded", serial.poll(0.5) == True)
    periphery.sleep_ms(500)
    passert("input waiting is lorem ipsum size", serial.input_waiting() == len(lorem_ipsum))
    buf = serial.read(len(lorem_ipsum))
    passert("compare readback lorem ipsum", buf == lorem_ipsum)

    # Test non-blocking poll
    print("Check non-blocking poll")
    passert("non-blocking poll is False", serial.poll(0) == False)

    # Test a very large read-write (likely to exceed internal buffer size (~4096))
    print("Write, flush, read large buffer")
    lorem_hugesum = b"\xaa" * (4096 * 3)
    passert("wrote lorem hugesum", serial.write(lorem_hugesum) == len(lorem_hugesum))
    serial.flush()
    buf = serial.read(len(lorem_hugesum), timeout=3)
    passert("compare readback lorem hugesum", buf == lorem_hugesum)

    # Test read timeout
    print("Check read timeout")
    tic = time.time()
    passert("read timed out", serial.read(4096 * 3, timeout=2) == b"")
    toc = time.time()
    passert("time elapsed", (toc - tic) > 1)

    # Test non-blocking read
    print("Check non-blocking read")
    tic = time.time()
    passert("read non-blocking is empty", serial.read(4096 * 3, timeout=0) == b"")
    toc = time.time()
    # Assuming we weren't context switched out for a second
    passert("almost no time elapsed", int(toc - tic) == 0)

    # Test blocking read with vmin=5 termios timeout
    print("Check blocking read with vmin termios timeout")
    serial.vmin = 5
    passert("write 5 bytes of lorem ipsum", serial.write(lorem_ipsum[0:5]) == 5)
    serial.flush()
    buf = serial.read(len(lorem_ipsum))
    passert("compare readback partial lorem ipsum", buf == lorem_ipsum[0:5])

    # Test blocking read with vmin=5, vtime=2 termios timeout
    print("Check blocking read with vmin + vtime termios timeout")
    serial.vtime = 2
    passert("write 3 bytes of lorem ipsum", serial.write(lorem_ipsum[0:3]) == 3)
    serial.flush()
    tic = time.time()
    buf = serial.read(len(lorem_ipsum))
    toc = time.time()
    passert("compare readback partial lorem ipsum", buf == lorem_ipsum[0:3])
    passert("time elapsed", (toc - tic) > 1)

    serial.close()


def test_interactive():
    ptest()

    buf = b"Hello World!"

    serial = periphery.Serial(serial_device, 4800)

    print("Starting interactive test. Get out your logic analyzer, buddy!")
    raw_input("Press enter to continue...")

    # Check tostring
    print("Serial description: {}".format(str(serial)))
    passert("interactive success", raw_input("Serial description looks ok? y/n ") == "y")

    serial.baudrate = 4800
    raw_input("Press enter to start transfer...")
    passert("serial write", serial.write(buf) == len(buf))
    passert("interactive success", raw_input("Serial transfer baudrate 4800, 8n1 occurred? y/n ") == "y")

    serial.baudrate = 9600
    raw_input("Press enter to start transfer...")
    passert("serial write", serial.write(buf) == len(buf))
    passert("interactive success", raw_input("Serial transfer baudrate 9600, 8n1 occurred? y/n ") == "y")

    serial.baudrate = 115200
    raw_input("Press enter to start transfer...")
    passert("serial write", serial.write(buf) == len(buf))
    passert("interactive success", raw_input("Serial transfer baudrate 115200, 8n1 occurred? y/n ") == "y")

    serial.close()


if __name__ == "__main__":
    if os.environ.get("CI") == "true":
        test_arguments()
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Usage: python -m tests.test_serial <serial port device>")
        print("")
        print("[1/4] Arguments test: No requirements.")
        print("[2/4] Open/close test: Serial port device should be real.")
        print("[3/4] Loopback test: Serial TX and RX should be connected with a wire.")
        print("[4/4] Interactive test: Serial TX should be observed with an oscilloscope or logic analyzer.")
        print("")
        print("Hint: for Raspberry Pi 3, enable UART0 with:")
        print("   $ echo \"dtoverlay=pi3-disable-bt\" | sudo tee -a /boot/config.txt")
        print("   $ sudo systemctl disable hciuart")
        print("   $ sudo reboot")
        print("   (Note that this will disable Bluetooth)")
        print("Use pins UART0 TXD (header pin 8) and UART0 RXD (header pin 10),")
        print("connect a loopback between TXD and RXD, and run this test with:")
        print("    python -m tests.test_serial /dev/ttyAMA0")
        print("")
        sys.exit(1)

    serial_device = sys.argv[1]

    test_arguments()
    pokay("Arguments test passed.")
    test_open_close()
    pokay("Open/close test passed.")
    test_loopback()
    pokay("Loopback test passed.")
    test_interactive()
    pokay("Interactive test passed.")

    pokay("All tests passed!")
