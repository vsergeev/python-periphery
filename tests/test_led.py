import sys
import periphery
from .asserts import AssertRaises

if sys.version_info[0] == 3:
    raw_input = input

led_name = None


def test_arguments():
    print("Starting arguments test...")

    # Invalid open types
    with AssertRaises(TypeError):
        periphery.LED("abc", "out")
    with AssertRaises(TypeError):
        periphery.LED(100, 100)

    print("Arguments test passed.")


def test_open_close():
    print("Starting open/close test...")

    # Open non-existent LED (export should fail with EINVAL)
    with AssertRaises(ValueError):
        periphery.LED("invalid_led_XXX", 0)

    # Open legitimate LED
    led = periphery.LED(led_name, 0)
    assert led.name == led_name
    assert led.fd > 0
    assert led.max_brightness > 0

    # Set brightness to 1, check brightness
    led.write(1)
    assert led.read() == 1

    # Set brightness to 0, check brightness
    led.write(0)
    assert led.read() == 0

    # Set brightness to 1, check brightness
    led.brightness = 1
    assert led.brightness == 1

    # Set brightness to 0, check brightness
    led.brightness = 0
    assert led.brightness == 0

    # Set brightness to True, check brightness
    led.write(True)
    assert led.read() == led.max_brightness

    # Set brightness to False, check brightness
    led.write(False)
    assert led.read() == 0

    led.close()

    print("Open/close test passed.")


def test_interactive():
    print("Starting interactive test...")

    led = periphery.LED(led_name, False)

    raw_input("Press enter to continue...")

    # Turn LED off
    led.write(False)
    assert raw_input("LED is off? y/n ") == "y"

    # Turn LED on
    led.write(True)
    assert raw_input("LED is on? y/n ") == "y"

    # Turn LED off
    led.write(False)
    assert raw_input("LED is off? y/n ") == "y"

    led.close()

    print("Interactive test passed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m tests.test_led <led name>")
        print("")
        print("Hint: for BeagleBone Black, use LED beaglebone:green:usr0,")
        print("and run this test:")
        print("    python -m tests.test_led beaglebone:green:usr0")
        sys.exit(1)

    led_name = sys.argv[1]

    print("Starting LED tests...")

    test_arguments()
    test_open_close()
    test_interactive()

    print("All LED tests passed.")
