import os
import select

class GPIOException(IOError):
    pass

class GPIO(object):
    def __init__(self, pin, direction):
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
        if direction.lower() not in ["in", "out", "high", "low"]:
            raise ValueError("Invalid direction, can be: \"in\", \"out\", \"high\", \"low\".")

        gpio_path = "/sys/class/gpio/gpio%d" % pin

        if not os.path.isdir(gpio_path):
            # Export the pin
            try:
                f_export = open("/sys/class/gpio/export", "w")
                f_export.write("%d\n" % pin)
                f_export.close()
            except IOError as e:
                raise GPIOException(e.errno, "Exporting GPIO: " + e.strerror)

        # Write direction
        try:
            direction = direction.lower()
            f_direction = open("/sys/class/gpio/gpio%d/direction" % pin, "w")
            f_direction.write(direction + "\n")
            f_direction.close()
        except IOError as e:
            raise GPIOException(e.errno, "Setting GPIO direction: " + e.strerror)

        # Open value
        try:
            self._fd = os.open("/sys/class/gpio/gpio%d/value" % pin, os.O_RDWR)
        except OSError as e:
            raise GPIOException(e.errno, "Opening GPIO: " + e.strerror)

        self._pin = pin


    # Methods

    def read(self):
        # Read value
        try:
            buf = os.read(self._fd, 2)
        except OSError as e:
            raise GPIOException(e.errno, "Reading GPIO: " + e.strerror)

        # Rewind
        try:
            os.lseek(self._fd, 0, os.SEEK_SET)
        except OSError as e:
            raise GPIOException(e.errno, "Rewinding GPIO: " + e.strerror)

        if buf[0] == b"0"[0]:
            return False
        elif buf[0] == b"1"[0]:
            return True

        raise GPIOException(None, "Unknown GPIO value: \"%s\"" % buf[0])

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
            raise GPIOException(e.errno, "Writing GPIO: " + e.strerror)

        # Rewind
        try:
            os.lseek(self._fd, 0, os.SEEK_SET)
        except OSError as e:
            raise GPIOException(e.errno, "Rewinding GPIO: " + e.strerror)

    def poll(self, timeout_ms):
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("Invalid timeout_ms type, should be integer or None.")

        # Seek to the end
        try:
            os.lseek(self._fd, 0, os.SEEK_END)
        except OSError as e:
            raise GPIOException(e.errno, "Seeking to end of GPIO: " + e.strerror)

        # Poll
        p = select.poll()
        p.register(self._fd, select.POLLPRI | select.POLLERR)
        events = p.poll(timeout_ms)

        # If GPIO edge interrupt occurred
        if len(events) > 0:
            # Rewind
            try:
                os.lseek(self._fd, 0, os.SEEK_SET)
            except OSError as e:
                raise GPIOException(e.errno, "Rewinding GPIO: " + e.strerror)

            return True

        return False

    def close(self):
        if self._fd is None:
            return

        try:
            os.close(self._fd)
        except OSError as e:
            raise GPIOException(e.errno, "Closing GPIO: " + e.strerror)

        self._fd = None

    # Immutable properties

    @property
    def fd(self):
        return self._fd

    @property
    def pin(self):
        return self._pin

    @property
    def supports_interrupts(self):
        return os.path.isfile("/sys/class/gpio/gpio%d/edge" % self._pin)

    # Mutable properties

    def _get_direction(self):
        # Read direction
        try:
            f_direction = open("/sys/class/gpio/gpio%d/direction" % self._pin, "r")
            direction = f_direction.read()
            f_direction.close()
        except IOError as e:
            raise GPIOException(e.errno, "Getting GPIO direction: " + e.strerror)

        return direction.strip()

    def _set_direction(self, direction):
        if not isinstance(direction, str):
            raise TypeError("Invalid direction type, should be string.")
        if direction.lower() not in ["in", "out", "high", "low"]:
            raise ValueError("Invalid direction, can be: \"in\", \"out\", \"high\", \"low\".")

        # Write direction
        try:
            direction = direction.lower()
            f_direction = open("/sys/class/gpio/gpio%d/direction" % self._pin, "w")
            f_direction.write(direction + "\n")
            f_direction.close()
        except IOError as e:
            raise GPIOException(e.errno, "Setting GPIO direction: " + e.strerror)

    direction = property(_get_direction, _set_direction)

    def _get_edge(self):
        # Read edge
        try:
            f_edge = open("/sys/class/gpio/gpio%d/edge" % self._pin, "r")
            edge = f_edge.read()
            f_edge.close()
        except IOError as e:
            raise GPIOException(e.errno, "Getting GPIO edge: " + e.strerror)

        return edge.strip()

    def _set_edge(self, edge):
        if not isinstance(edge, str):
            raise TypeError("Invalid edge type, should be string.")
        if edge.lower() not in ["none", "rising", "falling", "both"]:
            raise ValueError("Invalid edge, can be: \"none\", \"rising\", \"falling\", \"both\".")

        # Write edge
        try:
            edge = edge.lower()
            f_edge = open("/sys/class/gpio/gpio%d/edge" % self._pin, "w")
            f_edge.write(edge + "\n")
            f_edge.close()
        except IOError as e:
            raise GPIOException(e.errno, "Setting GPIO edge: " + e.strerror)

    edge = property(_get_edge, _set_edge)

    # String representation

    def __str__(self):
        if self.supports_interrupts:
            return "GPIO %d (fd=%d, direction=%s, supports interrupts, edge=%s)" % (self._pin, self._fd, self.direction, self.edge)

        return "GPIO %d (fd=%d, direction=%s, no interrupts)" % (self._pin, self._fd, self.direction)

