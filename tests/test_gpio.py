import sys
import periphery
from .asserts import AssertRaises

if sys.version_info[0] == 3:
    raw_input = input

pin_input = None
pin_output = None

def test_arguments():
    print("Starting arguments test...")

    # Invalid open types
    with AssertRaises(TypeError):
        periphery.GPIO("abc", "out")
    with AssertRaises(TypeError):
        periphery.GPIO(100, 100)
    # Invalid direction
    with AssertRaises(ValueError):
        periphery.GPIO(100, "blah")

    print("Arguments test passed.")

def test_open_close():
    print("Starting open/close test...")

    # Open non-existent GPIO (export should fail with EINVAL)
    with AssertRaises(periphery.GPIOError):
        periphery.GPIO(9999, "in")

    # Open legitimate GPIO
    gpio = periphery.GPIO(pin_output, "in")
    assert gpio.pin == pin_output
    assert gpio.fd > 0

    # Set direction out, check direction out, check value low
    gpio.direction = "out"
    assert gpio.direction == "out"
    assert gpio.read() == False
    # Set direction low, check direction out, check value low
    gpio.direction = "low"
    assert gpio.direction == "out"
    assert gpio.read() == False
    # Set direction high, check direction out, check value high
    gpio.direction = "high"
    assert gpio.direction == "out"
    assert gpio.read() == True
    # Set direction in, check direction in
    gpio.direction = "in"
    assert gpio.direction == "in"

    # Set invalid direction
    with AssertRaises(ValueError):
        gpio.direction = "blah"
    # Set invalid edge
    with AssertRaises(ValueError):
        gpio.edge = "blah"

    # Check interrupt edge support
    assert gpio.supports_interrupts == True

    # Set edge none, check edge none
    gpio.edge = "none"
    assert gpio.edge == "none"
    # Set edge rising, check edge rising
    gpio.edge = "rising"
    assert gpio.edge == "rising"
    # Set edge falling, check edge falling
    gpio.edge = "falling"
    assert gpio.edge == "falling"
    # Set edge both, check edge both
    gpio.edge = "both"
    assert gpio.edge == "both"
    # Set edge none, check edge none
    gpio.edge = "none"
    assert gpio.edge == "none"

    gpio.close()

    print("Open/close test passed.")

def test_loopback():
    print("Starting loopback test...")

    # Open in and out pins
    gpio_in = periphery.GPIO(pin_input, "in")
    gpio_out = periphery.GPIO(pin_output, "out")

    # Drive out low, check in low
    print("Drive out low, check in low")
    gpio_out.write(False)
    assert gpio_in.read() == False

    # Drive out high, check in high
    print("Drive out high, check in high")
    gpio_out.write(True)
    assert gpio_in.read() == True

    # Check poll falling (1->0) interrupt
    print("Check poll faliing 1 -> 0 interrupt")
    gpio_in.edge = "falling"
    gpio_out.write(False)
    assert gpio_in.poll(0.1) == True
    assert gpio_in.read() == False

    # Check poll rising 0 -> 1 interrupt
    print("Check poll faliing 0 -> 1 interrupt")
    gpio_in.edge = "rising"
    gpio_out.write(True)
    assert gpio_in.poll(0.1) == True
    assert gpio_in.read() == True

    # Check poll timeout
    assert gpio_in.poll(1) == False

    gpio_in.close()
    gpio_out.close()

    print("Loopback test passed.")

def test_interactive():
    print("Starting interactive test...")

    gpio = periphery.GPIO(pin_output, "out")

    print("Starting interactive test. Get out your multimeter, buddy!")
    raw_input("Press enter to continue...")

    # Drive GPIO out low
    gpio.write(False)
    assert raw_input("GPIO out is low? y/n ") == "y"

    # Drive GPIO out high
    gpio.write(True)
    assert raw_input("GPIO out is high? y/n ") == "y"

    # Drive GPIO out low
    gpio.write(False)
    assert raw_input("GPIO out is low? y/n ") == "y"

    gpio.close()

    print("Interactive test passed.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m tests.test_gpio <gpio1> <gpio2>")
        print("")
        print("  gpio1      gpio #1 (connected in to gpio #2)")
        print("  gpio2      gpio #2 (connected in to gpio #1)")
        print("")
        print("Hint: for BeagleBone Black, connect a wire between")
        print("GPIO 66 (P8.7) and GPIO 67 (P8.8), then run this test with:")
        print("    python -m tests.test_gpio 66 67")
        sys.exit(1)

    pin_input = int(sys.argv[1])
    pin_output = int(sys.argv[2])

    print("Starting MMIO tests...")

    test_arguments()
    test_open_close()
    test_loopback()
    test_interactive()

    print("All MMIO tests passed.")


