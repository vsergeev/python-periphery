import os
import select

class GPIOError(IOError):
    """Base class for GPIO errors."""
    pass

class GPIO(object):
    def __init__(self, pin, direction="preserve"):
        """Instantiate a GPIO object and open the sysfs GPIO corresponding to
        the specified pin, with the specified direction.

        `direction` can be "in" for input; "out" for output, initialized to
        low; "high" for output, initialized to high; "low" for output,
        initialized to low, or "preserve" for preserving existing direction.
        Default is "preserve".

        Args:
            pin (int): Linux pin number.
            direction (str): pin direction, can be "in", "out", "high", "low",
                             or "preserve".

        Returns:
            GPIO: GPIO object.

        Raises:
            GPIOError: if an I/O or OS error occurs.
            TypeError: if `pin` or `direction`  types are invalid.
            ValueError: if `direction` value is invalid.

        """
        self._fd = None
        self._pin = None
        self._open(pin, direction)

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, t, value, traceback):
        self.close()

    def _open(self, pin, direction):
        if not isinstance(pin, int):
            raise TypeError("Invalid pin type, should be integer.")
        if not isinstance(direction, str):
            raise TypeError("Invalid direction type, should be string.")
        if direction.lower() not in ["in", "out", "high", "low", "preserve"]:
            raise ValueError("Invalid direction, can be: \"in\", \"out\", \"high\", \"low\", \"preserve\".")

        gpio_path = "/sys/class/gpio/gpio%d" % pin

        if not os.path.isdir(gpio_path):
            # Export the pin
            try:
                with open("/sys/class/gpio/export", "w") as f_export:
                    f_export.write("%d\n" % pin)
            except IOError as e:
                raise GPIOError(e.errno, "Exporting GPIO: " + e.strerror)

        # Write direction, if it's not to be preserved
        direction = direction.lower()
        if direction != "preserve":
            try:
                with open("/sys/class/gpio/gpio%d/direction" % pin, "w") as f_direction:
                    f_direction.write(direction + "\n")
            except IOError as e:
                raise GPIOError(e.errno, "Setting GPIO direction: " + e.strerror)

        # Open value
        try:
            self._fd = os.open("/sys/class/gpio/gpio%d/value" % pin, os.O_RDWR)
        except OSError as e:
            raise GPIOError(e.errno, "Opening GPIO: " + e.strerror)

        self._pin = pin


    # Methods

    def read(self):
        """Read the state of the GPIO.

        Returns:
            bool: ``True`` for high state, ``False`` for low state.

        Raises:
            GPIOError: if an I/O or OS error occurs.

        """
        # Read value
        try:
            buf = os.read(self._fd, 2)
        except OSError as e:
            raise GPIOError(e.errno, "Reading GPIO: " + e.strerror)

        # Rewind
        try:
            os.lseek(self._fd, 0, os.SEEK_SET)
        except OSError as e:
            raise GPIOError(e.errno, "Rewinding GPIO: " + e.strerror)

        if buf[0] == b"0"[0]:
            return False
        elif buf[0] == b"1"[0]:
            return True

        raise GPIOError(None, "Unknown GPIO value: \"%s\"" % buf[0])

    def write(self, value):
        """Set the state of the GPIO to `value`.

        Args:
            value (bool): ``True`` for high state, ``False`` for low state.

        Raises:
            GPIOError: if an I/O or OS error occurs.
            TypeError: if `value` type is not bool.

        """
        if not isinstance(value, bool):
            raise TypeError("Invalid value type, should be bool.")

        # Write value
        try:
            if value:
                os.write(self._fd, b"1\n")
            else:
                os.write(self._fd, b"0\n")
        except OSError as e:
            raise GPIOError(e.errno, "Writing GPIO: " + e.strerror)

        # Rewind
        try:
            os.lseek(self._fd, 0, os.SEEK_SET)
        except OSError as e:
            raise GPIOError(e.errno, "Rewinding GPIO: " + e.strerror)

    def poll(self, timeout=None):
        """Poll a GPIO for the edge event configured with the .edge property.

        `timeout` can be a positive number for a timeout in seconds, 0 for a
        non-blocking poll, or negative or None for a blocking poll. Defaults to
        blocking poll.

        Args:
            timeout (int, float, None): timeout duration in seconds.

        Returns:
            bool: ``True`` if an edge event occurred, ``False`` on timeout.

        Raises:
            GPIOError: if an I/O or OS error occurs.
            TypeError: if `timeout` type is not None or int.

        """
        if not isinstance(timeout, (int, float, type(None))):
            raise TypeError("Invalid timeout type, should be integer, float, or None.")

        # Setup epoll
        p = select.epoll()
        p.register(self._fd, select.EPOLLIN | select.EPOLLET | select.EPOLLPRI)

        # Poll twice, as first call returns with current state
        for _ in range(2):
            events = p.poll(timeout)

        # If GPIO edge interrupt occurred
        if events:
            # Rewind
            try:
                os.lseek(self._fd, 0, os.SEEK_SET)
            except OSError as e:
                raise GPIOError(e.errno, "Rewinding GPIO: " + e.strerror)

            return True

        return False

    def close(self):
        """Close the sysfs GPIO.

        Raises:
            GPIOError: if an I/O or OS error occurs.

        """
        if self._fd is None:
            return

        try:
            os.close(self._fd)
        except OSError as e:
            raise GPIOError(e.errno, "Closing GPIO: " + e.strerror)

        self._fd = None

    # Immutable properties

    @property
    def fd(self):
        """Get the file descriptor for the underlying sysfs GPIO "value" file
        of the GPIO object.

        :type: int
        """
        return self._fd

    @property
    def pin(self):
        """Get the sysfs GPIO pin number.

        :type: int
        """
        return self._pin

    @property
    def supports_interrupts(self):
        """Get whether or not this GPIO supports edge interrupts, configurable
        with the .edge property.

        :type: bool
        """
        return os.path.isfile("/sys/class/gpio/gpio%d/edge" % self._pin)

    # Mutable properties

    def _get_direction(self):
        # Read direction
        try:
            with open("/sys/class/gpio/gpio%d/direction" % self._pin, "r") as f_direction:
                direction = f_direction.read()
        except IOError as e:
            raise GPIOError(e.errno, "Getting GPIO direction: " + e.strerror)

        return direction.strip()

    def _set_direction(self, direction):
        if not isinstance(direction, str):
            raise TypeError("Invalid direction type, should be string.")
        if direction.lower() not in ["in", "out", "high", "low"]:
            raise ValueError("Invalid direction, can be: \"in\", \"out\", \"high\", \"low\".")

        # Write direction
        try:
            direction = direction.lower()
            with open("/sys/class/gpio/gpio%d/direction" % self._pin, "w") as f_direction:
                f_direction.write(direction + "\n")
        except IOError as e:
            raise GPIOError(e.errno, "Setting GPIO direction: " + e.strerror)

    direction = property(_get_direction, _set_direction)
    """Get or set the GPIO's direction. Can be "in", "out", "high", "low".

    Direction "in" is input; "out" is output, initialized to low; "high" is
    output, initialized to high; and "low" is output, initialized to low.

    Raises:
        GPIOError: if an I/O or OS error occurs.
        TypeError: if `direction` type is not str.
        ValueError: if `direction` value is invalid.

    :type: str
    """

    def _get_edge(self):
        # Read edge
        try:
            with open("/sys/class/gpio/gpio%d/edge" % self._pin, "r") as f_edge:
                edge = f_edge.read()
        except IOError as e:
            raise GPIOError(e.errno, "Getting GPIO edge: " + e.strerror)

        return edge.strip()

    def _set_edge(self, edge):
        if not isinstance(edge, str):
            raise TypeError("Invalid edge type, should be string.")
        if edge.lower() not in ["none", "rising", "falling", "both"]:
            raise ValueError("Invalid edge, can be: \"none\", \"rising\", \"falling\", \"both\".")

        # Write edge
        try:
            edge = edge.lower()
            with open("/sys/class/gpio/gpio%d/edge" % self._pin, "w") as f_edge:
                f_edge.write(edge + "\n")
        except IOError as e:
            raise GPIOError(e.errno, "Setting GPIO edge: " + e.strerror)

    edge = property(_get_edge, _set_edge)
    """Get or set the GPIO's interrupt edge. Can be "none", "rising", "falling", "both".

    Raises:
        GPIOError: if an I/O or OS error occurs.
        TypeError: if `edge` type is not str.
        ValueError: if `edge` value is invalid.

    :type: str
    """

    # String representation

    def __str__(self):
        if self.supports_interrupts:
            return "GPIO %d (fd=%d, direction=%s, supports interrupts, edge=%s)" % (self._pin, self._fd, self.direction, self.edge)

        return "GPIO %d (fd=%d, direction=%s, no interrupts)" % (self._pin, self._fd, self.direction)

