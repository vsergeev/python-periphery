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


path = None
line_input = None
line_output = None


def test_arguments():
    ptest()

    # Invalid open types
    with AssertRaises("invalid open types", TypeError):
        periphery.GPIO(1, 1, "in")
    with AssertRaises("invalid open types", TypeError):
        periphery.GPIO("abc", 2.3, "in")
    with AssertRaises("invalid open types", TypeError):
        periphery.GPIO("abc", 1, 1)
    # Invalid direction
    with AssertRaises("invalid direction", ValueError):
        periphery.GPIO("abc", 1, "blah")


def test_open_close():
    ptest()

    # Open non-existent GPIO (export should fail with EINVAL)
    with AssertRaises("non-existent GPIO", periphery.GPIOError):
        periphery.GPIO(path, 9999, "in")

    # Open legitimate GPIO
    gpio = periphery.GPIO(path, line_output, "in")
    passert("property line", gpio.line == line_output)
    passert("direction is in", gpio.direction == "in")
    passert("fd >= 0", gpio.fd >= 0)
    passert("chip_fd >= 0", gpio.chip_fd >= 0)

    # Check default label
    passert("property label", gpio.label == "periphery")

    # Set invalid direction
    with AssertRaises("set invalid direction", ValueError):
        gpio.direction = "blah"
    # Set invalid edge
    with AssertRaises("set invalid edge", ValueError):
        gpio.edge = "blah"
    # Set invalid bias
    with AssertRaises("set invalid bias", ValueError):
        gpio.bias = "blah"
    # Set invalid drive
    with AssertRaises("set invalid drive", ValueError):
        gpio.drive = "blah"

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
    passert("value is high", gpio.read() == True)

    # Set drive open drain, check drive open drain
    gpio.drive = "open_drain"
    passert("drive is open drain", gpio.drive == "open_drain")
    # Set drive open source, check drive open source
    gpio.drive = "open_source"
    passert("drive is open drain", gpio.drive == "open_source")
    # Set drive default, check drive default
    gpio.drive = "default"
    passert("drive is default", gpio.drive == "default")

    # Set inverted true, check inverted true
    gpio.inverted = True
    passert("inverted is True", gpio.inverted == True)
    # Set inverted false, check inverted false
    gpio.inverted = False
    passert("inverted is False", gpio.inverted == False)

    # Attempt to set interrupt edge on output GPIO
    with AssertRaises("set interrupt edge on output GPIO", periphery.GPIOError):
        gpio.edge = "rising"
    # Attempt to read event on output GPIO
    with AssertRaises("read event on output GPIO", periphery.GPIOError):
        gpio.read_event()

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

    # Set bias pull up, check bias pull up
    gpio.bias = "pull_up"
    passert("bias is pull up", gpio.bias == "pull_up")
    # Set bias pull down, check bias pull down
    gpio.bias = "pull_down"
    passert("bias is pull down", gpio.bias == "pull_down")
    # Set bias disable, check bias disable
    gpio.bias = "disable"
    passert("bias is disable", gpio.bias == "disable")
    # Set bias default, check bias default
    gpio.bias = "default"
    passert("bias is default", gpio.bias == "default")

    # Attempt to set drive on input GPIO
    with AssertRaises("set drive on input GPIO", periphery.GPIOError):
        gpio.drive = "open_drain"

    gpio.close()

    # Open with keyword arguments
    gpio = periphery.GPIO(path, line_input, "in", edge="rising", bias="default", drive="default", inverted=False, label="test123")
    passert("property line", gpio.line == line_input)
    passert("direction is in", gpio.direction == "in")
    passert("fd >= 0", gpio.fd >= 0)
    passert("chip_fd >= 0", gpio.chip_fd >= 0)
    passert("edge is rising", gpio.edge == "rising")
    passert("bias is default", gpio.bias == "default")
    passert("drive is default", gpio.drive == "default")
    passert("inverted is False", gpio.inverted == False)
    passert("label is test123", gpio.label == "test123")

    gpio.close()


def test_loopback():
    ptest()

    # Open in and out lines
    gpio_in = periphery.GPIO(path, line_input, "in")
    gpio_out = periphery.GPIO(path, line_output, "out")

    # Drive out low, check in low
    print("Drive out low, check in low")
    gpio_out.write(False)
    passert("value is False", gpio_in.read() == False)

    # Drive out high, check in high
    print("Drive out high, check in high")
    gpio_out.write(True)
    passert("value is True", gpio_in.read() == True)

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
    event = gpio_in.read_event()
    passert("event edge is falling", event.edge == "falling")
    passert("event timestamp is non-zero", event.timestamp != 0)

    # Check poll rising 0 -> 1 interrupt
    print("Check poll rising 0 -> 1 interrupt")
    gpio_in.edge = "rising"
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(0.5)
    gpio_out.write(True)
    passert("gpin_in polled True", poll_ret.get() == True)
    passert("value is high", gpio_in.read() == True)
    event = gpio_in.read_event()
    passert("event edge is rising", event.edge == "rising")
    passert("event timestamp is non-zero", event.timestamp != 0)

    # Set edge to both
    gpio_in.edge = "both"

    # Check poll falling 1 -> 0 interrupt
    print("Check poll falling 1 -> 0 interrupt")
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(0.5)
    gpio_out.write(False)
    passert("gpio_in polled True", poll_ret.get() == True)
    passert("value is low", gpio_in.read() == False)
    event = gpio_in.read_event()
    passert("event edge is falling", event.edge == "falling")
    passert("event timestamp is non-zero", event.timestamp != 0)

    # Check poll rising 0 -> 1 interrupt
    print("Check poll rising 0 -> 1 interrupt")
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(0.5)
    gpio_out.write(True)
    passert("gpio_in polled True", poll_ret.get() == True)
    passert("value is high", gpio_in.read() == True)
    event = gpio_in.read_event()
    passert("event edge is rising", event.edge == "rising")
    passert("event timestamp is non-zero", event.timestamp != 0)

    # Check poll timeout
    print("Check poll timeout")
    passert("gpio_in polled False", gpio_in.poll(1) == False)

    # Check poll falling 1 -> 0 interrupt with the poll_multiple() API
    print("Check poll falling 1 -> 0 interrupt with poll_multiple()")
    gpio_out.write(False)
    gpios_ready = periphery.GPIO.poll_multiple([gpio_in], 1)
    passert("gpios ready is gpio_in", gpios_ready == [gpio_in])
    passert("value is low", gpio_in.read() == False)
    event = gpio_in.read_event()
    passert("event edge is falling", event.edge == "falling")
    passert("event timestamp is non-zero", event.timestamp != 0)

    # Check poll rising 0 -> 1 interrupt with the poll_multiple() API
    print("Check poll rising 0 -> 1 interrupt with poll_multiple()")
    gpio_out.write(True)
    gpios_ready = periphery.GPIO.poll_multiple([gpio_in], 1)
    passert("gpios ready is gpio_in", gpios_ready == [gpio_in])
    passert("value is high", gpio_in.read() == True)
    event = gpio_in.read_event()
    passert("event edge is rising", event.edge == "rising")
    passert("event timestamp is non-zero", event.timestamp != 0)

    # Check poll timeout
    print("Check poll timeout with poll_multiple()")
    gpios_ready = periphery.GPIO.poll_multiple([gpio_in], 1)
    passert("gpios ready is empty", gpios_ready == [])

    gpio_in.close()
    gpio_out.close()

    # Open both GPIOs as inputs
    gpio_in = periphery.GPIO(path, line_input, "in")
    gpio_out = periphery.GPIO(path, line_output, "in")

    # Set bias pull-up, check value is high
    print("Check input GPIO reads high with pull-up bias")
    gpio_in.bias = "pull_up"
    time.sleep(0.1)
    passert("value is high", gpio_in.read() == True)

    # Set bias pull-down, check value is low
    print("Check input GPIO reads low with pull-down bias")
    gpio_in.bias = "pull_down"
    time.sleep(0.1)
    passert("value is low", gpio_in.read() == False)

    gpio_in.close()
    gpio_out.close()


def test_interactive():
    print("Starting interactive test...")

    gpio = periphery.GPIO(path, line_output, "out")

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
        print("Usage: python -m tests.test_gpio <GPIO chip device> <GPIO #1> <GPIO #2>")
        print("")
        print("[1/4] Argument test: No requirements.")
        print("[2/4] Open/close test: GPIO #2 should be real.")
        print("[3/4] Loopback test: GPIOs #1 and #2 should be connected with a wire.")
        print("[4/4] Interactive test: GPIO #2 should be observed with a multimeter.")
        print("")
        print("Hint: for Raspberry Pi 3,")
        print("Use GPIO 17 (header pin 11) and GPIO 27 (header pin 13),")
        print("connect a loopback between them, and run this test with:")
        print("    python -m tests.test_gpio /dev/gpiochip0 17 27")
        print("")
        sys.exit(1)

    path = sys.argv[1]
    line_input = int(sys.argv[2])
    line_output = int(sys.argv[3])

    test_arguments()
    pokay("Arguments test passed.")
    test_open_close()
    pokay("Open/close test passed.")
    test_loopback()
    pokay("Loopback test passed.")
    test_interactive()
    pokay("Interactive test passed.")

    pokay("All tests passed!")
