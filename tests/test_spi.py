import sys
import periphery
from .asserts import AssertRaises

if sys.version_info[0] == 3:
    raw_input = input

spi_device = None


def test_arguments():
    print("Starting arguments test...")

    # Invalid mode
    with AssertRaises(ValueError):
        periphery.SPI(spi_device, 4, int(1e6))
    # Invalid bit order
    with AssertRaises(ValueError):
        periphery.SPI(spi_device, 4, int(1e6), bit_order="blah")

    print("Arguments test passed.")


def test_open_close():
    print("Starting open/close test...")

    # Normal open (mode=1, max_speed = 100000)
    spi = periphery.SPI(spi_device, 1, 100000)

    # Confirm fd and defaults
    assert spi.fd > 0
    assert spi.mode == 1
    assert spi.max_speed == 100000
    assert spi.bit_order == "msb"
    assert spi.bits_per_word == 8
    assert spi.extra_flags == 0

    # Not going to try different bit order or bits per word, because not
    # all SPI controllers support them

    # Try modes 0, 1, 2, 3
    spi.mode = 0
    assert spi.mode == 0
    spi.mode = 1
    assert spi.mode == 1
    spi.mode = 2
    assert spi.mode == 2
    spi.mode = 3
    assert spi.mode == 3

    # Try max speeds 100Khz, 500KHz, 1MHz, 2MHz
    spi.max_speed = 100000
    assert spi.max_speed == 100000
    spi.max_speed = 500000
    assert spi.max_speed == 500000
    spi.max_speed = 1000000
    assert spi.max_speed == 1000000
    spi.max_speed = 2e6
    assert spi.max_speed == 2000000

    spi.close()

    print("Open/close test passed.")


def test_loopback():
    print("Starting loopback test...")

    spi = periphery.SPI(spi_device, 0, 100000)

    # Try list transfer
    buf_in = list(range(256)) * 4
    buf_out = spi.transfer(buf_in)
    assert buf_out == buf_in

    # Try bytearray transfer
    buf_in = bytearray(buf_in)
    buf_out = spi.transfer(buf_in)
    assert buf_out == buf_in

    # Try bytes transfer
    buf_in = bytes(bytearray(buf_in))
    buf_out = spi.transfer(buf_in)
    assert buf_out == buf_in

    spi.close()

    print("Loopback test passed.")


def test_interactive():
    print("Starting interactive test...")

    spi = periphery.SPI(spi_device, 0, 100000)

    print("Starting interactive test. Get out your logic analyzer, buddy!")
    raw_input("Press enter to continue...")

    # Mode 0 transfer
    raw_input("Press enter to start transfer...")
    spi.transfer([0x55, 0xaa, 0x0f, 0xf0])
    print("SPI data 0x55, 0xaa, 0x0f, 0xf0")
    assert raw_input("SPI transfer speed <= 100KHz, mode 0 occurred? y/n ") == "y"

    # Mode 1 transfer
    spi.mode = 1
    raw_input("Press enter to start transfer...")
    spi.transfer([0x55, 0xaa, 0x0f, 0xf0])
    print("SPI data 0x55, 0xaa, 0x0f, 0xf0")
    assert raw_input("SPI transfer speed <= 100KHz, mode 1 occurred? y/n ") == "y"

    # Mode 2 transfer
    spi.mode = 2
    raw_input("Press enter to start transfer...")
    spi.transfer([0x55, 0xaa, 0x0f, 0xf0])
    print("SPI data 0x55, 0xaa, 0x0f, 0xf0")
    assert raw_input("SPI transfer speed <= 100KHz, mode 2 occurred? y/n ") == "y"

    # Mode 3 transfer
    spi.mode = 3
    raw_input("Press enter to start transfer...")
    spi.transfer([0x55, 0xaa, 0x0f, 0xf0])
    print("SPI data 0x55, 0xaa, 0x0f, 0xf0")
    assert raw_input("SPI transfer speed <= 100KHz, mode 3 occurred? y/n ") == "y"

    spi.mode = 0

    # 500KHz transfer
    spi.max_speed = 500000
    raw_input("Press enter to start transfer...")
    spi.transfer([0x55, 0xaa, 0x0f, 0xf0])
    print("SPI data 0x55, 0xaa, 0x0f, 0xf0")
    assert raw_input("SPI transfer speed <= 500KHz, mode 0 occurred? y/n ") == "y"

    # 1MHz transfer
    spi.max_speed = 1000000
    raw_input("Press enter to start transfer...")
    spi.transfer([0x55, 0xaa, 0x0f, 0xf0])
    print("SPI data 0x55, 0xaa, 0x0f, 0xf0")
    assert raw_input("SPI transfer speed <= 1MHz, mode 0 occurred? y/n ") == "y"

    spi.close()

    print("Interactive test passed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m tests.test_spi <SPI device>")
        print("")
        print("[1/4] Arguments test: No requirements.")
        print("[2/4] Open/close test: SPI device should be real.")
        print("[3/4] Loopback test: SPI MISO and MOSI should be connected with a wire.")
        print("[4/4] Interactive test: SPI MOSI, CLK, CS should be observed with an oscilloscope or logic analyzer.")
        print("")
        print("Hint: for Raspberry Pi 3, enable SPI0 with:")
        print("   $ echo \"dtparam=spi=on\" | sudo tee -a /boot/config.txt")
        print("   $ sudo reboot")
        print("Use pins SPI0 MOSI (header pin 19), SPI0 MISO (header pin 21), SPI0 SCLK (header pin 23),")
        print("connect a loopback between MOSI and MISO, and run this test with:")
        print("    python -m tests.test_spi /dev/spidev0.0")
        print("")
        sys.exit(1)

    spi_device = sys.argv[1]

    print("Starting SPI tests...")

    test_arguments()
    test_open_close()
    test_loopback()
    test_interactive()

    print("All SPI tests passed.")
