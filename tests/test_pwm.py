import os
import sys
import periphery
from .asserts import AssertRaises

if sys.version_info[0] == 3:
    raw_input = input

pwm_chip = None
pwm_channel = None


def test_arguments():
    print("Starting arguments test...")

    # Invalid open types
    with AssertRaises(TypeError):
        periphery.PWM("foo", 0)
    with AssertRaises(TypeError):
        periphery.PWM(0, "foo")

    print("Arguments test passed.")


def test_open_close():
    print("Starting open/close test...")

    # Open non-existent PWM chip
    with AssertRaises(LookupError):
        periphery.PWM(9999, pwm_channel)

    # Open non-existent PWM channel
    with AssertRaises(periphery.PWMError):
        periphery.PWM(pwm_chip, 9999)

    # Open legitimate PWM chip/channel
    pwm = periphery.PWM(pwm_chip, pwm_channel)
    assert pwm.chip == pwm_chip
    assert pwm.channel == pwm_channel

    # Initialize duty cycle to 0
    pwm.duty_cycle = 0

    # Set period, check period, check period_ns, check frequency
    pwm.period = 1e-3
    assert abs(pwm.period - 1e-3) < 1e-4
    assert abs(pwm.period_ns - 1000000) < 1e5
    assert abs(pwm.frequency - 1000) < 100
    pwm.period = 5e-4
    assert abs(pwm.period - 5e-4) < 1e-5
    assert abs(pwm.period_ns - 500000) < 1e4
    assert abs(pwm.frequency - 2000) < 100

    # Set frequency, check frequency, check period, check period_ns
    pwm.frequency = 1000
    assert abs(pwm.frequency - 1000) < 100
    assert abs(pwm.period - 1e-3) < 1e-4
    assert abs(pwm.period_ns - 1000000) < 1e5
    pwm.frequency = 2000
    assert abs(pwm.frequency - 2000) < 100
    assert abs(pwm.period - 5e-4) < 1e-5
    assert abs(pwm.period_ns - 500000) < 1e4

    # Set period_ns, check period_ns, check period, check frequency
    pwm.period_ns = 1000000
    assert abs(pwm.period_ns - 1000000) < 1e5
    assert abs(pwm.period - 1e-3) < 1e-4
    assert abs(pwm.frequency - 1000) < 100
    pwm.period_ns = 500000
    assert abs(pwm.period_ns - 500000) < 1e4
    assert abs(pwm.period - 5e-4) < 1e-5
    assert abs(pwm.frequency - 2000) < 100

    pwm.period_ns = 1000000

    # Set duty cycle, check duty cycle, check duty_cycle_ns
    pwm.duty_cycle = 0.25
    assert abs(pwm.duty_cycle - 0.25) < 1e-3
    assert abs(pwm.duty_cycle_ns - 250000) < 1e4
    pwm.duty_cycle = 0.50
    assert abs(pwm.duty_cycle - 0.50) < 1e-3
    assert abs(pwm.duty_cycle_ns - 500000) < 1e4
    pwm.duty_cycle = 0.75
    assert abs(pwm.duty_cycle - 0.75) < 1e-3
    assert abs(pwm.duty_cycle_ns - 750000) < 1e4

    # Set duty_cycle_ns, check duty_cycle_ns, check duty_cycle
    pwm.duty_cycle_ns = 250000
    assert abs(pwm.duty_cycle_ns - 250000) < 1e4
    assert abs(pwm.duty_cycle - 0.25) < 1e-3
    pwm.duty_cycle_ns = 500000
    assert abs(pwm.duty_cycle_ns - 500000) < 1e4
    assert abs(pwm.duty_cycle - 0.50) < 1e-3
    pwm.duty_cycle_ns = 750000
    assert abs(pwm.duty_cycle_ns - 750000) < 1e4
    assert abs(pwm.duty_cycle - 0.75) < 1e-3

    # Set polarity, check polarity
    pwm.polarity = "normal"
    assert pwm.polarity == "normal"
    pwm.polarity = "inversed"
    assert pwm.polarity == "inversed"
    # Set enabled, check enabled
    pwm.enabled = True
    assert pwm.enabled == True
    pwm.enabled = False
    assert pwm.enabled == False
    # Use enable()/disable(), check enabled
    pwm.enable()
    assert pwm.enabled == True
    pwm.disable()
    assert pwm.enabled == False

    # Set invalid polarity
    with AssertRaises(ValueError):
        pwm.polarity = "foo"

    pwm.close()

    print("Open/close test passed.")


def test_interactive():
    print("Starting interactive test...")

    pwm = periphery.PWM(pwm_chip, pwm_channel)

    print("Starting interactive test. Get out your oscilloscope, buddy!")
    raw_input("Press enter to continue...")

    # Set initial parameters and enable PWM
    pwm.duty_cycle = 0.0
    pwm.frequency = 1e3
    pwm.polarity = "normal"
    pwm.enabled = True

    # Check tostring
    print("PWM description: {}".format(str(pwm)))
    assert raw_input("PWM description looks ok? y/n ") == "y"

    # Set 1 kHz frequency, 0.25 duty cycle
    pwm.frequency = 1e3
    pwm.duty_cycle = 0.25
    assert raw_input("Frequency is 1 kHz, duty cycle is 25%? y/n ") == "y"

    # Set 1 kHz frequency, 0.50 duty cycle
    pwm.frequency = 1e3
    pwm.duty_cycle = 0.50
    assert raw_input("Frequency is 1 kHz, duty cycle is 50%? y/n ") == "y"

    # Set 2 kHz frequency, 0.25 duty cycle
    pwm.frequency = 2e3
    pwm.duty_cycle = 0.25
    assert raw_input("Frequency is 2 kHz, duty cycle is 25%? y/n ") == "y"

    # Set 2 kHz frequency, 0.50 duty cycle
    pwm.frequency = 2e3
    pwm.duty_cycle = 0.50
    assert raw_input("Frequency is 2 kHz, duty cycle is 50%? y/n ") == "y"

    pwm.duty_cycle = 0.0
    pwm.enabled = False

    pwm.close()

    print("Interactive test passed.")


if __name__ == "__main__":
    if os.environ.get("CI") == "true":
        test_arguments()
        sys.exit(0)

    if len(sys.argv) < 3:
        print("Usage: python -m tests.test_pwm <PWM chip> <PWM channel>")
        print("")
        print("[1/4] Arguments test: No requirements.")
        print("[2/4] Open/close test: PWM channel should be real.")
        print("[3/4] Loopback test: No test.")
        print("[4/4] Interactive test: PWM channel should be observed with an oscilloscope or logic analyzer.")
        print("")
        print("Hint: for Raspberry Pi 3, enable PWM0 and PWM1 with:")
        print("   $ echo \"dtoverlay=pwm-2chan,pin=18,func=2,pin2=13,func2=4\" | sudo tee -a /boot/config.txt")
        print("   $ sudo reboot")
        print("Monitor GPIO 18 (header pin 12), and run this test with:")
        print("    python -m tests.test_pwm 0 0")
        print("or, monitor GPIO 13 (header pin 33), and run this test with:")
        print("    python -m tests.test_pwm 0 1")
        print("")

        sys.exit(1)

    pwm_chip = int(sys.argv[1])
    pwm_channel = int(sys.argv[2])

    print("Starting PMW tests...")

    test_arguments()
    test_open_close()
    test_interactive()

    print("All PWM tests passed.")
