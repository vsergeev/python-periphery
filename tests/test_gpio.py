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

    # Open with preserved direction
    gpio = periphery.GPIO(pin_output, "preserve")
    assert gpio.direction == "in"
    gpio.direction = "out"
    gpio.close()

    # Open with preserved direction, using default argument
    gpio = periphery.GPIO(pin_output)
    assert gpio.direction == "out"
    gpio.direction = "in"
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
    time.sleep(1)
    gpio_out.write(False)
    assert poll_ret.get() == True
    assert gpio_in.read() == False

    # Check poll timeout on 0 -> 0
    print("Check poll falling timeout on 0 -> 0")
    poll_ret = threaded_poll(gpio_in, 2)
    time.sleep(1)
    gpio_out.write(False)
    assert poll_ret.get() == False
    assert gpio_in.read() == False

    # Check poll rising 0 -> 1 interrupt
    print("Check poll rising 0 -> 1 interrupt")
    gpio_in.edge = "rising"
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(1)
    gpio_out.write(True)
    assert poll_ret.get() == True
    assert gpio_in.read() == True

    # Check poll timeout on 1 -> 1
    print("Check poll rising timeout on 1 -> 1")
    poll_ret = threaded_poll(gpio_in, 2)
    time.sleep(1)
    gpio_out.write(True)
    assert poll_ret.get() == False
    assert gpio_in.read() == True

    # Check poll rising+falling interrupts
    print("Check poll rising/falling interrupt")
    gpio_in.edge = "both"
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(1)
    gpio_out.write(False)
    assert poll_ret.get() == True
    assert gpio_in.read() == False
    poll_ret = threaded_poll(gpio_in, 5)
    time.sleep(1)
    gpio_out.write(True)
    assert poll_ret.get() == True
    assert gpio_in.read() == True

    # Check poll timeout
    print("Check poll timeout")
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
        print("    python -m tests.test_gpio 17 27")
        print("")
        sys.exit(1)

    pin_input = int(sys.argv[1])
    pin_output = int(sys.argv[2])

    print("Starting GPIO tests...")

    test_arguments()
    test_open_close()
    test_loopback()
    test_interactive()

    print("All GPIO tests passed.")
