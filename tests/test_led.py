import os
import sys
import time

import periphery
from .test import ptest, pokay, passert, AssertRaises

if sys.version_info[0] == 3:
    raw_input = input


led_name = None


def test_arguments():
    ptest()

    # Invalid open types
    with AssertRaises("invalid open types", TypeError):
        periphery.LED("abc", "out")
    with AssertRaises("invalid open types", TypeError):
        periphery.LED(100, 100)


def test_open_close():
    ptest()

    # Open non-existent LED
    with AssertRaises("non-existent led", LookupError):
        periphery.LED("invalid_led_XXX", 0)

    # Open legitimate LED
    led = periphery.LED(led_name, 0)
    passert("property name", led.name == led_name)
    passert("fd >= 0", led.fd >= 0)
    passert("max_brightness > 0", led.max_brightness > 0)

    # Set brightness to True, check brightness
    led.write(True)
    time.sleep(0.01)
    passert("brightness is max", led.read() == led.max_brightness)

    # Set brightness to False, check brightness
    led.write(False)
    time.sleep(0.01)
    passert("brightness is zero", led.read() == 0)

    # Set brightness to 1, check brightness
    led.write(1)
    time.sleep(0.01)
    passert("brightness is non-zero", led.read() >= 1)

    # Set brightness to 0, check brightness
    led.write(0)
    time.sleep(0.01)
    passert("brightness is zero", led.read() == 0)

    # Set brightness to 1, check brightness
    led.brightness = 1
    time.sleep(0.01)
    passert("brightness is non-zero", led.brightness >= 1)

    # Set brightness to 0, check brightness
    led.brightness = 0
    time.sleep(0.01)
    passert("brightness is zero", led.brightness == 0)

    led.close()


def test_loopback():
    ptest()
    # No general way to do a loopback test for I2C without a real component, skipping...


def test_interactive():
    ptest()

    led = periphery.LED(led_name, False)

    raw_input("Press enter to continue...")

    # Check tostring
    print("LED description: {}".format(str(led)))
    passert("interactive success", raw_input("LED description looks ok? y/n ") == "y")

    # Turn LED off
    led.write(False)
    passert("interactive success", raw_input("LED is off? y/n ") == "y")

    # Turn LED on
    led.write(True)
    passert("interactive success", raw_input("LED is on? y/n ") == "y")

    # Turn LED off
    led.write(False)
    passert("interactive success", raw_input("LED is off? y/n ") == "y")

    # Turn LED on
    led.write(True)
    passert("interactive success", raw_input("LED is on? y/n ") == "y")

    led.close()


if __name__ == "__main__":
    if os.environ.get("CI") == "true":
        test_arguments()
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Usage: python -m tests.test_led <LED name>")
        print("")
        print("[1/4] Arguments test: No requirements.")
        print("[2/4] Open/close test: LED should be real.")
        print("[3/4] Loopback test: No test.")
        print("[4/4] Interactive test: LED should be observed.")
        print("")
        print("Hint: for Raspberry Pi 3, disable triggers for led1:")
        print("    $ echo none > /sys/class/leds/led1/trigger")
        print("Observe led1 (red power LED), and run this test:")
        print("    python -m tests.test_led led1")
        print("")
        sys.exit(1)

    led_name = sys.argv[1]

    test_arguments()
    pokay("Arguments test passed.")
    test_open_close()
    pokay("Open/close test passed.")
    test_loopback()
    pokay("Loopback test passed.")
    test_interactive()
    pokay("Interactive test passed.")

    pokay("All tests passed!")
