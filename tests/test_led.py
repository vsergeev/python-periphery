import sys
import periphery
from .asserts import AssertRaises

if sys.version_info[0] == 3:
    raw_input = input

led0 = None

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
    with AssertRaises(periphery.LEDError):
        periphery.GPIO("invalid_led_XXX", 0)

    # Open legitimate LED
    led0 = periphery.LED(led0, 0)
    assert led0.led == led0
    assert led0.fd > 0

    # Set brigthness to 1, check brightness
    led0.brightness = 1
    assert led0.brightness == 1
    
    # Set brigthness to 0, check brightness
    led0.brightness = 0
    assert led0.brightness == 0

    led0.close()

    print("Open/close test passed.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m tests.test_led <led>")
        sys.exit(1)

    led0 = int(sys.argv[1])

    print("Starting LED tests...")

    test_arguments()
    test_open_close()

    print("All LED tests passed.")


