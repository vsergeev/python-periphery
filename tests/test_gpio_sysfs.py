import os
import sys
import threading
import time

import periphery
from .test import ptest, pokay, passert, AssertRaises

if sys.version_info[0] == 3:
    raw_input = input
    import queue
else:
    import Queue as queue


line_input = None
line_output = None


def test_arguments():
    ptest()

    # Invalid open types
    with AssertRaises("invalid open types", TypeError):
        periphery.GPIO("abc", "out")
    with AssertRaises("invalid open types", TypeError):
        periphery.GPIO(100, 100)
    # Invalid direction
    with AssertRaises("invalid direction", ValueError):
        periphery.GPIO(100, "blah")



def test_open_close():
    ptest()

    # Open non-existent GPIO (export should fail with EINVAL)
    with AssertRaises("non-existent GPIO", periphery.GPIOError):
        periphery.GPIO(9999, "in")

    # Open legitimate GPIO
    gpio = periphery.GPIO(line_output, "in")
    passert("property line", gpio.line == line_output)
    passert("direction is in", gpio.direction == "in")
    passert("fd >= 0", gpio.fd >= 0)

    # Set invalid direction
    with AssertRaises("set invalid direction", ValueError):
        gpio.direction = "blah"
    # Set invalid edge
    with AssertRaises("set invalid edge", ValueError):
        gpio.edge = "blah"
    # Unsupported property bias
    with AssertRaises("unsupported property bias", NotImplementedError):
        _ = gpio.bias
    with AssertRaises("unsupported property bias", NotImplementedError):
        gpio.bias = "pull_up"
    # Unsupported property drive
    with AssertRaises("unsupported property drive", NotImplementedError):
        _ = gpio.drive
    with AssertRaises("unsupported property drive", NotImplementedError):
        gpio.drive = "open_drain"
    # Unsupported proprety
    with AssertRaises("unsupported property chip_fd", NotImplementedError):
        _ = gpio.chip_fd
    # Unsupported method
    with AssertRaises("unsupported method", NotImplementedError):
        gpio.read_event()

    # Set direction out, check direction out, check value low
    gpio.direction = "out"
    passert("direction is out", gpio.direction == "out")
    passert("value is low", gpio.read() == False)
    # Set direction low, check direction out, check value low
    gpio.direction = "low"
    passert("direction is out", gpio.direction == "out")
    passert("value is low", gpio.read() == False)
    # Set direction high, check direction out, check value high
    gpio.direction = "high"
    passert("direction is out", gpio.direction == "out")
    passert("ivalue is high", gpio.read() == True)

    # Set inverted true, check inverted
    gpio.inverted = True
    passert("inverted is True", gpio.inverted == True)
    # Set inverted false, check inverted
    gpio.inverted = False
    passert("inverted is False", gpio.inverted == False)

    # Set direction in, check direction in
    gpio.direction = "in"
    passert("direction is in", gpio.direction == "in")

    # Set edge none, check edge none
    gpio.edge = "none"
    passert("edge is none", gpio.edge == "none")
    # Set edge rising, check edge rising
    gpio.edge = "rising"
    passert("edge is rising", gpio.edge == "rising")
    # Set edge falling, check edge falling
    gpio.edge = "falling"
    passert("edge is falling", gpio.edge == "falling")
    # Set edge both, check edge both
    gpio.edge = "both"
    passert("edge is both", gpio.edge == "both")
    # Set edge none, check edge none
    gpio.edge = "none"
    passert("edge is none", gpio.edge == "none")

    gpio.close()


def test_loopback():
    ptest()

    # Open in and out lines
    gpio_in = periphery.GPIO(line_input, "in")
    gpio_out = periphery.GPIO(line_output, "out")

    # Drive out low, check in low
    print("Drive out low, check in low")
    gpio_out.write(False)
    passert("value is low", gpio_in.read() == False)

    # Drive out high, check in high
    print("Drive out high, check in high")
    gpio_out.write(True)
    passert("value is high", gpio_in.read() == True)

    # Wrapper for running poll() in a thread
    def threaded_poll(gpio, timeout):
        ret = queue.Queue()

        def f():
            ret.put(gpio.poll(timeout))

        thread = threading.Thread(target=f)
        thread.start()
        return ret

    # Check poll falling 1 -> 0 interrupt
    print("Check poll falling 1 -> 0 interrupt")
    gpio_in.edge = "falling"
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(0.5)
    gpio_out.write(False)
    passert("gpio_in polled True", poll_ret.get() == True)
    passert("value is low", gpio_in.read() == False)

    # Check poll rising 0 -> 1 interrupt
    print("Check poll rising 0 -> 1 interrupt")
    gpio_in.edge = "rising"
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(0.5)
    gpio_out.write(True)
    passert("gpio_in polled True", poll_ret.get() == True)
    passert("value is high", gpio_in.read() == True)

    # Set edge to both
    gpio_in.edge = "both"

    # Check poll falling 1 -> 0 interrupt
    print("Check poll falling 1 -> 0 interrupt")
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(0.5)
    gpio_out.write(False)
    passert("gpio_in polled True", poll_ret.get() == True)
    passert("value is low", gpio_in.read() == False)

    # Check poll rising 0 -> 1 interrupt
    print("Check poll rising 0 -> 1 interrupt")
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(0.5)
    gpio_out.write(True)
    passert("gpio_in polled True", poll_ret.get() == True)
    passert("value is high", gpio_in.read() == True)

    # Check poll timeout
    print("Check poll timeout")
    passert("gpio_in polled False", gpio_in.poll(1) == False)

    # Check poll falling 1 -> 0 interrupt with the poll_multiple() API
    print("Check poll falling 1 -> 0 interrupt with poll_multiple()")
    gpio_out.write(False)
    gpios_ready = periphery.GPIO.poll_multiple([gpio_in], 1)
    passert("gpios ready is gpio_in", gpios_ready == [gpio_in])
    passert("value is low", gpio_in.read() == False)

    # Check poll rising 0 -> 1 interrupt with the poll_multiple() API
    print("Check poll rising 0 -> 1 interrupt with poll_multiple()")
    gpio_out.write(True)
    gpios_ready = periphery.GPIO.poll_multiple([gpio_in], 1)
    passert("gpios ready is gpio_in", gpios_ready == [gpio_in])
    passert("value is high", gpio_in.read() == True)

    # Check poll timeout
    print("Check poll timeout with poll_multiple()")
    gpios_ready = periphery.GPIO.poll_multiple([gpio_in], 1)
    passert("gpios ready is empty", gpios_ready == [])

    gpio_in.close()
    gpio_out.close()


def test_interactive():
    ptest()

    gpio = periphery.GPIO(line_output, "out")

    print("Starting interactive test. Get out your multimeter, buddy!")
    raw_input("Press enter to continue...")

    # Check tostring
    print("GPIO description: {}".format(str(gpio)))
    passert("interactive success", raw_input("GPIO description looks ok? y/n ") == "y")

    # Drive GPIO out low
    gpio.write(False)
    passert("interactive success", raw_input("GPIO out is low? y/n ") == "y")

    # Drive GPIO out high
    gpio.write(True)
    passert("interactive success", raw_input("GPIO out is high? y/n ") == "y")

    # Drive GPIO out low
    gpio.write(False)
    passert("interactive success", raw_input("GPIO out is low? y/n ") == "y")

    gpio.close()


if __name__ == "__main__":
    if os.environ.get("CI") == "true":
        test_arguments()
        sys.exit(0)

    if len(sys.argv) < 3:
        print("Usage: python -m tests.test_gpio <GPIO #1> <GPIO #2>")
        print("")
        print("[1/4] Argument test: No requirements.")
        print("[2/4] Open/close test: GPIO #2 should be real.")
        print("[3/4] Loopback test: GPIOs #1 and #2 should be connected with a wire.")
        print("[4/4] Interactive test: GPIO #2 should be observed with a multimeter.")
        print("")
        print("Hint: for Raspberry Pi 3,")
        print("Use GPIO 17 (header pin 11) and GPIO 27 (header pin 13),")
        print("connect a loopback between them, and run this test with:")
        print("    python -m tests.test_gpio_sysfs 17 27")
        print("")
        sys.exit(1)

    line_input = int(sys.argv[1])
    line_output = int(sys.argv[2])

    test_arguments()
    pokay("Arguments test passed.")
    test_open_close()
    pokay("Open/close test passed.")
    test_loopback()
    pokay("Loopback test passed.")
    test_interactive()
    pokay("Interactive test passed.")

    pokay("All tests passed!")
