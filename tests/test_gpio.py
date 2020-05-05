import os
import sys
import threading
import time

import periphery
from .asserts import AssertRaises

if sys.version_info[0] == 3:
    raw_input = input
    import queue
else:
    import Queue as queue


path = None
line_input = None
line_output = None


def test_arguments():
    print("Starting arguments test...")

    # Invalid open types
    with AssertRaises(TypeError):
        periphery.GPIO(1, 1, "in")
    with AssertRaises(TypeError):
        periphery.GPIO("abc", 2.3, "in")
    with AssertRaises(TypeError):
        periphery.GPIO("abc", 1, 1)
    # Invalid direction
    with AssertRaises(ValueError):
        periphery.GPIO("abc", 1, "blah")

    print("Arguments test passed.")


def test_open_close():
    print("Starting open/close test...")

    # Open non-existent GPIO (export should fail with EINVAL)
    with AssertRaises(periphery.GPIOError):
        periphery.GPIO(path, 9999, "in")

    # Open legitimate GPIO
    gpio = periphery.GPIO(path, line_output, "in")
    assert gpio.line == line_output
    assert gpio.direction == "in"
    assert gpio.fd >= 0
    assert gpio.chip_fd >= 0

    # Set invalid direction
    with AssertRaises(ValueError):
        gpio.direction = "blah"
    # Set invalid edge
    with AssertRaises(ValueError):
        gpio.edge = "blah"

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
    # Attempt to set interrupt edge on output GPIO
    with AssertRaises(periphery.GPIOError):
        gpio.edge = "rising"
    # Attempt to read event on output GPIO
    with AssertRaises(periphery.GPIOError):
        gpio.read_event()

    # Set direction in, check direction in
    gpio.direction = "in"
    assert gpio.direction == "in"

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

    # Open in and out lines
    gpio_in = periphery.GPIO(path, line_input, "in")
    gpio_out = periphery.GPIO(path, line_output, "out")

    # Drive out low, check in low
    print("Drive out low, check in low")
    gpio_out.write(False)
    assert gpio_in.read() == False

    # Drive out high, check in high
    print("Drive out high, check in high")
    gpio_out.write(True)
    assert gpio_in.read() == True

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
    assert poll_ret.get() == True
    assert gpio_in.read() == False
    event = gpio_in.read_event()
    assert event.edge == "falling"
    assert event.timestamp != 0

    # Check poll rising 0 -> 1 interrupt
    print("Check poll rising 0 -> 1 interrupt")
    gpio_in.edge = "rising"
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(0.5)
    gpio_out.write(True)
    assert poll_ret.get() == True
    assert gpio_in.read() == True
    event = gpio_in.read_event()
    assert event.edge == "rising"
    assert event.timestamp != 0

    # Set edge to both
    gpio_in.edge = "both"

    # Check poll falling 1 -> 0 interrupt
    print("Check poll falling 1 -> 0 interrupt")
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(0.5)
    gpio_out.write(False)
    assert poll_ret.get() == True
    assert gpio_in.read() == False
    event = gpio_in.read_event()
    assert event.edge == "falling"
    assert event.timestamp != 0

    # Check poll rising 0 -> 1 interrupt
    print("Check poll rising 0 -> 1 interrupt")
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(0.5)
    gpio_out.write(True)
    assert poll_ret.get() == True
    assert gpio_in.read() == True
    event = gpio_in.read_event()
    assert event.edge == "rising"
    assert event.timestamp != 0

    # Check poll timeout
    print("Check poll timeout")
    assert gpio_in.poll(1) == False

    # Check poll falling 1 -> 0 interrupt with the poll_multiple() API
    print("Check poll falling 1 -> 0 interrupt with poll_multiple()")
    gpio_out.write(False)
    gpios_ready = periphery.GPIO.poll_multiple([gpio_in], 1)
    assert gpios_ready == [gpio_in]
    assert gpio_in.read() == False
    event = gpio_in.read_event()
    assert event.edge == "falling"
    assert event.timestamp != 0

    # Check poll rising 0 -> 1 interrupt with the poll_multiple() API
    print("Check poll rising 0 -> 1 interrupt with poll_multiple()")
    gpio_out.write(True)
    gpios_ready = periphery.GPIO.poll_multiple([gpio_in], 1)
    assert gpios_ready == [gpio_in]
    assert gpio_in.read() == True
    event = gpio_in.read_event()
    assert event.edge == "rising"
    assert event.timestamp != 0

    # Check poll timeout
    print("Check poll timeout with poll_multiple()")
    gpios_ready = periphery.GPIO.poll_multiple([gpio_in], 1)
    assert gpios_ready == []

    gpio_in.close()
    gpio_out.close()

    print("Loopback test passed.")


def test_interactive():
    print("Starting interactive test...")

    gpio = periphery.GPIO(path, line_output, "out")

    print("Starting interactive test. Get out your multimeter, buddy!")
    raw_input("Press enter to continue...")

    # Check tostring
    print("GPIO description: {}".format(str(gpio)))
    assert raw_input("GPIO description looks ok? y/n ") == "y"

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

    print("Starting GPIO tests...")

    test_arguments()
    test_open_close()
    test_loopback()
    test_interactive()

    print("All GPIO tests passed.")
