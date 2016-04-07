import os
import select

class LEDError(IOError):
    """Base class for LED errors."""
    pass

class LED(object):
    def __init__(self, led, brightness):
        """Instantiate a LED object and open the corresponding sysfs LED.

        Args:
        led (str): Linux led name.
	    brightness (int): Initial brightness.

        Returns:
            LED: LED object.

        Raises:
            LEDError: if an I/O or OS error occurs.
            TypeError: if `led` or `brightness`  types are invalid.
            ValueError: if `brightness` value is invalid.

        """
        self._fd = None
        self._led = None
        self._max_brightness = 0
        self._open(led, brightness)

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, t, value, traceback):
        self.close()

    def _open(self, led, brightness):
        if not isinstance(led, str):
            raise TypeError("Invalid led type, should be string.")
        if not isinstance(brightness, int):
            raise TypeError("Invalid brightness type, should be int.")

        led_path = "/sys/class/leds/%s" % led

        if not os.path.isdir(led_path):
            raise LEDError("LED not found!")

		# Read max brightness
        try:
            with open("/sys/class/leds/%s/max_brightness" % led, "r") as f_max_brightness:
                max_brightness = int(f_max_brightness.read())
        except OSError as e:
            raise LEDError(e.errno, "Reading LED max brightness: " + e.strerror)

        if brightness < 0 or brightness > max_brightness:
            raise ValueError("Invalid brightness, must be between 0 and %d" % max_brightness)

        # Write brightness
        try:
            with open("/sys/class/leds/%s/brightness" % led, "w") as f_brightness:
                f_brightness.write("%d\n" % brightness)
        except IOError as e:
            raise LEDError(e.errno, "Setting LED brighness: " + e.strerror)

        # Open brightness
        try:
            self._fd = os.open("/sys/class/leds/%s/brightness" % led, os.O_RDWR)
        except OSError as e:
            raise LEDError(e.errno, "Reading LED brightness: " + e.strerror)
            
        self._max_brightness = max_brightness
        self._led = led


    # Methods

    def read(self):
        """Read the brighness of the LED.

        Returns:
            int: Current brightness.

        Raises:
            LEDError: if an I/O or OS error occurs.

        """
        # Read value
        try:
            buf = os.read(self._fd, 4)
        except OSError as e:
            raise LEDError(e.errno, "Reading LED brightness: " + e.strerror)

        # Rewind
        try:
            os.lseek(self._fd, 0, os.SEEK_SET)
        except OSError as e:
            raise LEDError(e.errno, "Rewinding LED brightness: " + e.strerror)

        return int(buf)

    def write(self, brightness):
        """Set the brightness of the LED to `brightness`.

        Args:
            brightness (int): Brightness value to be set.

        Raises:
            LEDError: if an I/O or OS error occurs.
            TypeError: if `brightness` type is not int.

        """
        if not isinstance(brightness, int):
            raise TypeError("Invalid brightness type, should be int.")

        if not (0 <= brightness <= self._max_brightness):
            raise ValueError("Invalid brightness, must be between 0 and %d" % self._max_brightness)

        # Write value
        try:
            os.write(self._fd, b"%d\n" % brightness)
        except OSError as e:
            raise LEDError(e.errno, "Writing LED brightness: " + e.strerror)

        # Rewind
        try:
            os.lseek(self._fd, 0, os.SEEK_SET)
        except OSError as e:
            raise LEDError(e.errno, "Rewinding LED brightness: " + e.strerror)

    def close(self):
        """Close the sysfs LED.

        Raises:
            LEDError: if an I/O or OS error occurs.

        """
        if self._fd is None:
            return

        try:
            os.close(self._fd)
        except OSError as e:
            raise LEDError(e.errno, "Closing LED: " + e.strerror)

        self._fd = None
        
    # Mutable properties

    def _get_brightness(self):
        # Read brightness
        return self.read()

    def _set_brightness(self, brightness):
        return self.write(brightness)

    brightness = property(_get_brightness, _set_brightness)
    """Get or set the LED's brightness.

    Raises:
        LEDError: if an I/O or OS error occurs.
        TypeError: if `brightness` type is not int.
        ValueError: if `brightness` value is invalid.

    :type:
    """

    # Immutable properties

    @property
    def fd(self):
        """Get the file descriptor for the underlying sysfs LED "brightness" file
        of the LED object.

        :type: int
        """
        return self._fd

    @property
    def led(self):
        """Get the sysfs LED name.

        :type: int
        """
        return self._led

    # String representation

    def __str__(self):
        return "LED %s (fd=%d, max_brightness=%d)" % (self._led, self._fd, self._max_brightness)

