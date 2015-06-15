import sys
import time
import periphery
from .asserts import AssertRaises

if sys.version_info[0] == 3:
    raw_input = input

serial_device = None

def test_arguments():
    print("Starting arguments test...")

    # Invalid data bits
    with AssertRaises(ValueError):
        periphery.Serial(serial_device, 115200, databits=4)
    with AssertRaises(ValueError):
        periphery.Serial(serial_device, 115200, databits=9)
    # Invalid parity
    with AssertRaises(ValueError):
        periphery.Serial(serial_device, 115200, parity="blah")
    # Invalid stopb bits
    with AssertRaises(ValueError):
        periphery.Serial(serial_device, 115200, stopbits=0)
    with AssertRaises(ValueError):
        periphery.Serial(serial_device, 115200, stopbits=3)

    # Everything else is fair game, although termios might not like it.

    print("Arguments test passed.")

def test_open_close():
    print("Starting open/close test...")

    serial = periphery.Serial(serial_device, 115200)

    # Confirm default settings
    assert serial.fd > 0
    assert serial.baudrate == 115200
    assert serial.databits == 8
    assert serial.parity == "none"
    assert serial.stopbits == 1
    assert serial.xonxoff == False
    assert serial.rtscts == False

    # Change some stuff and check that it changed
    serial.baudrate = 4800
    assert serial.baudrate == 4800
    serial.baudrate = 9600
    assert serial.baudrate == 9600
    serial.databits = 7
    assert serial.databits == 7
    serial.parity = "odd"
    assert serial.parity == "odd"
    serial.stopbits = 2
    assert serial.stopbits == 2
    serial.xonxoff = True
    assert serial.xonxoff == True
    # Test serial port may not support rtscts

    serial.close()

    print("Open/close test passed.")

def test_loopback():
    print("Starting loopback test...")

    lorem_ipsum = b"Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

    serial = periphery.Serial(serial_device, 115200)

    # Test write/flush/read with bytes write
    assert serial.write(lorem_ipsum) == len(lorem_ipsum)
    serial.flush()
    buf = serial.read(len(lorem_ipsum))
    assert buf == lorem_ipsum

    # Test write/flush/read with bytearray write
    assert serial.write(bytearray(lorem_ipsum)) == len(lorem_ipsum)
    serial.flush()
    buf = serial.read(len(lorem_ipsum))
    assert buf == lorem_ipsum

    # Test write/flush/read with list write
    assert serial.write(list(bytearray(lorem_ipsum))) == len(lorem_ipsum)
    serial.flush()
    buf = serial.read(len(lorem_ipsum))
    assert buf == lorem_ipsum

    # Test poll/write/flush/poll/input waiting/read
    assert serial.poll(0.5) == False
    assert serial.write(lorem_ipsum) == len(lorem_ipsum)
    serial.flush()
    assert serial.poll(0.5) == True
    periphery.sleep_ms(500)
    assert serial.input_waiting() == len(lorem_ipsum)
    buf = serial.read(len(lorem_ipsum))
    assert buf == lorem_ipsum

    # Test non-blocking poll
    assert serial.poll(0) == False

    # Test a very large read-write (likely to exceed internal buffer size (~4096))
    lorem_hugesum = b"\xaa"*(4096*3)
    assert serial.write(lorem_hugesum) == len(lorem_hugesum)
    serial.flush()
    buf = serial.read(len(lorem_hugesum))
    assert buf == lorem_hugesum

    # Test read timeout
    tic = time.time()
    assert serial.read(4096*3, timeout=2) == b""
    toc = time.time()
    assert (toc-tic) > 1

    # Test non-blocking read
    tic = time.time()
    assert serial.read(4096*3, timeout=0) == b""
    toc = time.time()
    # Assuming we weren't context switched out for a second and weren't on
    # a thin time boundary ;)
    assert int(toc-tic) == 0

    serial.close()

    print("Loopback test passed.")

def test_interactive():
    print("Starting interactive test...")

    buf = b"Hello World!"

    serial = periphery.Serial(serial_device, 4800)

    print("Starting interactive test. Get out your logic analyzer, buddy!")
    raw_input("Press enter to continue...")

    serial.baudrate = 4800
    raw_input("Press enter to start transfer...")
    assert serial.write(buf) == len(buf)
    assert raw_input("Serial transfer baudrate 4800, 8n1 occurred? y/n ") == "y"

    serial.baudrate = 9600
    raw_input("Press enter to start transfer...")
    assert serial.write(buf) == len(buf)
    assert raw_input("Serial transfer baudrate 9600, 8n1 occurred? y/n ") == "y"

    serial.baudrate = 115200
    raw_input("Press enter to start transfer...")
    assert serial.write(buf) == len(buf)
    assert raw_input("Serial transfer baudrate 115200, 8n1 occurred? y/n ") == "y"

    serial.close()

    print("Interactive test passed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m tests.test_serial <serial device>")
        print("")
        print("  serial device  serial device with TX/RX loopback installed")
        print("")
        print("Hint: for BeagleBone Black, export UART4 to /dev/ttyO4 with:")
        print("    echo BB-UART4 > /sys/devices/bone_capemgr.9/slots")
        print("to enable UART4 (TX=P9.13 RX=P9.11).")
        print("Connect a wire between TX and RX, then run this test:")
        print("    python -m tests.test_serial /dev/ttyO4")
        sys.exit(1)

    serial_device = sys.argv[1]

    print("Starting Serial tests...")

    test_arguments()
    test_open_close()
    test_loopback()
    test_interactive()

    print("All Serial tests passed.")

