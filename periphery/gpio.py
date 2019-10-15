import collections
import os
import os.path
import select
import time


class GPIOError(IOError):
    """Base class for GPIO errors."""
    pass


class EdgeEvent(collections.namedtuple('EdgeEvent', ['edge', 'timestamp'])):
    def __new__(cls, edge, timestamp):
        """EdgeEvent containing the event edge and event time reported by Linux.

        Args:
            edge (str): event edge, either "rising" or "falling".
            timestamp (int): event time in nanoseconds.
        """
        return super(EdgeEvent, cls).__new__(cls, edge, timestamp)


class GPIO(object):
    def __new__(cls, *args):
        return SysfsGPIO.__new__(cls, *args)

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, t, value, traceback):
        self.close()

    # Methods

    def read(self):
        """Read the state of the GPIO.

        Returns:
            bool: ``True`` for high state, ``False`` for low state.

        Raises:
            GPIOError: if an I/O or OS error occurs.

        """
        raise NotImplementedError()

    def write(self, value):
        """Set the state of the GPIO to `value`.

        Args:
            value (bool): ``True`` for high state, ``False`` for low state.

        Raises:
            GPIOError: if an I/O or OS error occurs.
            TypeError: if `value` type is not bool.

        """
        raise NotImplementedError()

    def poll(self, timeout=None):
        """Poll a GPIO for the edge event configured with the .edge property.

        For character device GPIOs, the edge event should be consumed with
        `read_event()`. For sysfs GPIOs, the edge event should be consumed with
        `read()`.

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
        raise NotImplementedError()

    def read_event(self):
        """Read the edge event that occurred with the GPIO.

        This method is intended for use with character device GPIOs and is
        unsupported by sysfs GPIOs.

        Returns:
            EdgeEvent: a namedtuple containing the string edge event that
            occurred (either ``"rising"`` or ``"falling"``), and the event time
            reported by Linux in nanoseconds.

        Raises:
            GPIOError: if an I/O or OS error occurs.
            NotImplementedError: if called on a sysfs GPIO.

        """
        raise NotImplementedError()

    def close(self):
        """Close the sysfs GPIO.

        Raises:
            GPIOError: if an I/O or OS error occurs.

        """
        raise NotImplementedError()

    # Immutable properties

    @property
    def devpath(self):
        """Get the device path of the underlying GPIO device.

        :type: str
        """
        raise NotImplementedError()

    @property
    def fd(self):
        """Get the line file descriptor of the GPIO object.

        :type: int
        """
        raise NotImplementedError()

    @property
    def line(self):
        """Get the GPIO object's line number.

        :type: int
        """
        raise NotImplementedError()

    @property
    def name(self):
        """Get the line name of the GPIO.

        his method is intended for use with character device GPIOs and always
        returns the empty string for sysfs GPIOs.

        :type: str
        """
        raise NotImplementedError()

    @property
    def chip_fd(self):
        """Get the GPIO chip file descriptor of the GPIO object.

        This method is intended for use with character device GPIOs and is unsupported by sysfs GPIOs.

        Raises:
            NotImplementedError: if accessed on a sysfs GPIO.

        :type: int
        """
        raise NotImplementedError()

    @property
    def chip_name(self):
        """Get the name of the GPIO chip associated with the GPIO.

        :type: str
        """
        raise NotImplementedError()

    @property
    def chip_label(self):
        """ Get the label of the GPIO chip associated with the GPIO.

        :type: str
        """
        raise NotImplementedError()

    # Mutable properties

    def _get_direction(self):
        raise NotImplementedError()

    def _set_direction(self, direction):
        raise NotImplementedError()

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
        raise NotImplementedError()

    def _set_edge(self, edge):
        raise NotImplementedError()

    edge = property(_get_edge, _set_edge)
    """Get or set the GPIO's interrupt edge. Can be "none", "rising",
    "falling", "both".

    Raises:
        GPIOError: if an I/O or OS error occurs.
        TypeError: if `edge` type is not str.
        ValueError: if `edge` value is invalid.

    :type: str
    """

    # String representation

    def __str__(self):
        """Get the string representation of the GPIO.

        :type: str
        """
        raise NotImplementedError()


class SysfsGPIO(GPIO):
    # Number of retries to check for successful GPIO export
    GPIO_EXPORT_STAT_RETRIES = 10
    # Delay between check for GPIO export (100ms)
    GPIO_EXPORT_STAT_DELAY = 0.1

    def __init__(self, line, direction):
        """**Sysfs GPIO**

        Instantiate a GPIO object and open the sysfs GPIO with the specified
        line and direction.

        `direction` can be "in" for input; "out" for output, initialized to
        low; "high" for output, initialized to high; or "low" for output,
        initialized to low.

        Args:
            line (int): GPIO line number.
            direction (str): GPIO direction, can be "in", "out", "high", or
                             "low",

        Returns:
            SysfsGPIO: GPIO object.

        Raises:
            GPIOError: if an I/O or OS error occurs.
            TypeError: if `line` or `direction`  types are invalid.
            ValueError: if `direction` value is invalid.
            TimeoutError: if waiting for GPIO export times out.

        """
        self._fd = None
        self._line = None

        self._open(line, direction)

    def __new__(self, line, direction):
        return object.__new__(SysfsGPIO)

    def _open(self, line, direction):
        if not isinstance(line, int):
            raise TypeError("Invalid line type, should be integer.")
        if not isinstance(direction, str):
            raise TypeError("Invalid direction type, should be string.")
        if direction.lower() not in ["in", "out", "high", "low"]:
            raise ValueError("Invalid direction, can be: \"in\", \"out\", \"high\", \"low\".")

        gpio_path = "/sys/class/gpio/gpio%d" % line

        if not os.path.isdir(gpio_path):
            # Export the line
            try:
                with open("/sys/class/gpio/export", "w") as f_export:
                    f_export.write("%d\n" % line)
            except IOError as e:
                raise GPIOError(e.errno, "Exporting GPIO: " + e.strerror)

            # Loop until GPIO is exported
            exported = False
            for i in range(SysfsGPIO.GPIO_EXPORT_STAT_RETRIES):
                if os.path.isdir(gpio_path):
                    exported = True
                    break

                time.sleep(SysfsGPIO.GPIO_EXPORT_STAT_DELAY)

            if not exported:
                raise TimeoutError("Exporting GPIO: waiting for '%s' timed out" % gpio_path)

        # Write direction
        try:
            with open(os.path.join(gpio_path, "direction"), "w") as f_direction:
                f_direction.write(direction.lower() + "\n")
        except IOError as e:
            raise GPIOError(e.errno, "Setting GPIO direction: " + e.strerror)

        # Open value
        try:
            self._fd = os.open(os.path.join(gpio_path, "value"), os.O_RDWR)
        except OSError as e:
            raise GPIOError(e.errno, "Opening GPIO: " + e.strerror)

        self._line = line
        self._path = gpio_path

    # Methods

    def read(self):
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
        if not isinstance(timeout, (int, float, type(None))):
            raise TypeError("Invalid timeout type, should be integer, float, or None.")

        # Setup poll
        p = select.poll()
        p.register(self._fd, select.POLLPRI | select.POLLERR)

        # Scale timeout to milliseconds
        if isinstance(timeout, (int, float)) and timeout > 0:
            timeout *= 1000

        # Poll
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

    def read_event(self):
        raise NotImplementedError()

    def close(self):
        if self._fd is None:
            return

        try:
            os.close(self._fd)
        except OSError as e:
            raise GPIOError(e.errno, "Closing GPIO: " + e.strerror)

        self._fd = None

        # Unexport the line
        try:
            unexport_fd = os.open("/sys/class/gpio/unexport", os.O_WRONLY)
            os.write(unexport_fd, b"%d\n" % self._line)
            os.close(unexport_fd)
        except OSError as e:
            raise GPIOError(e.errno, "Unexporting GPIO: " + e.strerror)

    # Immutable properties

    @property
    def devpath(self):
        return self._path

    @property
    def fd(self):
        return self._fd

    @property
    def line(self):
        return self._line

    @property
    def name(self):
        return ""

    @property
    def chip_fd(self):
        raise NotImplementedError("Sysfs GPIO does not have a gpiochip file descriptor.")

    @property
    def chip_name(self):
        gpio_path = os.path.join(self._path, "device")

        gpiochip_path = os.readlink(gpio_path)

        if '/' not in gpiochip_path:
            raise GPIOError(None, "Reading gpiochip name: invalid device symlink \"%s\"" % gpiochip_path)

        return gpiochip_path.split('/')[-1]

    @property
    def chip_label(self):
        gpio_path = "/sys/class/gpio/%s/label" % self.chip_name

        try:
            with open(gpio_path, "r") as f_label:
                label = f_label.read()
        except (GPIOError, IOError) as e:
            if isinstance(e, IOError):
                raise GPIOError(e.errno, "Reading gpiochip label: " + e.strerror)

            raise GPIOError(None, "Reading gpiochip label: " + e.strerror)

        return label.strip()

    # Mutable properties

    def _get_direction(self):
        # Read direction
        try:
            with open(os.path.join(self._path, "direction"), "r") as f_direction:
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
            with open(os.path.join(self._path, "direction"), "w") as f_direction:
                f_direction.write(direction.lower() + "\n")
        except IOError as e:
            raise GPIOError(e.errno, "Setting GPIO direction: " + e.strerror)

    direction = property(_get_direction, _set_direction)

    def _get_edge(self):
        # Read edge
        try:
            with open(os.path.join(self._path, "edge"), "r") as f_edge:
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
            with open(os.path.join(self._path, "edge"), "w") as f_edge:
                f_edge.write(edge.lower() + "\n")
        except IOError as e:
            raise GPIOError(e.errno, "Setting GPIO edge: " + e.strerror)

    edge = property(_get_edge, _set_edge)

    # String representation

    def __str__(self):
        try:
            str_direction = self.direction
        except GPIOError:
            str_direction = "<error>"

        try:
            str_edge = self.edge
        except GPIOError:
            str_edge = "<error>"

        try:
            str_chip_name = self.chip_name
        except GPIOError:
            str_chip_name = "<error>"

        try:
            str_chip_label = self.chip_label
        except GPIOError:
            str_chip_label = "<error>"

        return "GPIO %d (device=%s, fd=%d, direction=%s, edge=%s, chip_name=\"%s\", chip_label=\"%s\", type=sysfs)" % \
            (self._line, self._path, self._fd, str_direction, str_edge, str_chip_name, str_chip_label)
