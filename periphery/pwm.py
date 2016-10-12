import os

class PWMError(IOError):
    """Base class for PWM errors."""
    pass

class PWM(object):
    # Sysfs paths
    _sysfs_path = "/sys/class/pwm/"
    _channel_path = "pwmchip{}"

    # Channel paths
    _export_path = "export"
    _pin_path = "pwm{}"

    # Pin attribute paths
    _pin_period_path = "period"
    _pin_duty_cycle_path = "duty_cycle"
    _pin_polarity_path = "polarity"
    _pin_enable_path = "enable"

    def __init__(self, channel, pin):
        """Instantiate a PWM object and open the sysfs PWM corresponding to the
        specified channel and pin.

        Args:
            channel (int): Linux channel number.
            pin (int): Linux pin number.

        Returns:
            PWM: PWM object.

        Raises:
            PWMError: if an I/O or OS error occurs.
            TypeError: if `channel` or `pin` types are invalid.
            ValueError: if PWM channel does not exist.

        """

        self._channel = None
        self._pin = None
        self._open(channel, pin)

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, t, value, traceback):
        self.close()

    def _open(self, channel, pin):
        if not isinstance(channel, int):
            raise TypeError("Invalid channel type, should be integer.")
        if not isinstance(pin, int):
            raise TypeError("Invalid pin type, should be integer.")

        channel_path = os.path.join(self._sysfs_path, self._channel_path.format(channel))
        if not os.path.isdir(channel_path):
            raise ValueError("PWM channel does not exist, check that the required modules are loaded.")

        pin_path = os.path.join(channel_path, self._pin_path.format(pin))
        if not os.path.isdir(pin_path):
            try:
                with open(os.path.join(channel_path, self._export_path), "w") as f_export:
                    f_export.write("%d\n" % pin)
            except IOError as e:
                raise PWMError(e.errno, "Exporting PWM pin: " + e.strerror)

        self._channel = channel
        self._pin = pin

        # Look up the period, for fast duty cycle updates
        self._period = self._get_period()

    def close(self):
        """Close the sysfs PWM."""
        self._channel = None
        self._pin = None

    def _write_pin_attr(self, attr, value):
        path = os.path.join(
            self._sysfs_path,
            self._channel_path.format(self._channel),
            self._pin_path.format(self._pin),
            attr)

        with open(path, 'w') as f_attr:
            f_attr.write(value + "\n")

    def _read_pin_attr(self, attr):
        path = os.path.join(
            self._sysfs_path,
            self._channel_path.format(self._channel),
            self._pin_path.format(self._pin),
            attr)

        with open(path, 'r') as f_attr:
            return f_attr.read().strip()

    # Methods

    def enable(self):
        """Enable the PWM output."""
        self.enabled = True

    def disable(self):
        """Disable the PWM output."""
        self.enabled = False

    # Immutable properties

    @property
    def channel(self):
        """Get the sysfs PWM channel number.

        :type: int
        """
        return self._channel

    @property
    def pin(self):
        """Get the sysfs PWM pin number.

        :type: int
        """
        return self._pin

    # Mutable properties

    def _get_period(self):
        try:
            period_ns = int(self._read_pin_attr(self._pin_period_path))
        except ValueError:
            raise PWMError(None, "Unknown period value: \"%s\"" % period_ns)

        # Convert period from nanoseconds to seconds
        period = period_ns / 1e9

        # Update our cached period
        self._period = period

        return period

    def _set_period(self, period):
        if not isinstance(period, (int, float)):
            raise TypeError("Invalid period type, should be int or float.")

        # Convert period from seconds to integer nanoseconds
        period_ns = int(period * 1e9)

        self._write_pin_attr(self._pin_period_path, "{}".format(period_ns))

        # Update our cached period
        self._period = float(period)

    period = property(_get_period, _set_period)
    """Get or set the PWM's output period in seconds.

    Raises:
        PWMError: if an I/O or OS error occurs.
        TypeError: if value type is not int or float.

    :type: int, float
    """

    def _get_duty_cycle(self):
        try:
            duty_cycle_ns = int(self._read_pin_attr(self._pin_duty_cycle_path))
        except ValueError:
            raise PWMError(None, "Unknown duty cycle value: \"%s\"" % duty_cycle_ns)

        # Convert duty cycle from nanoseconds to seconds
        duty_cycle = duty_cycle_ns / 1e9

        # Convert duty cycle to ratio from 0.0 to 1.0
        duty_cycle = duty_cycle / self._period

        return duty_cycle

    def _set_duty_cycle(self, duty_cycle):
        if not isinstance(duty_cycle, (int, float)):
            raise TypeError("Invalid duty cycle type, should be int or float.")
        elif not 0.0 <= duty_cycle <= 1.0:
            raise ValueError("Invalid duty cycle value, should be between 0.0 and 1.0.")

        # Convert duty cycle from ratio to seconds
        duty_cycle = duty_cycle * self._period

        # Convert duty cycle from seconds to integer nanoseconds
        duty_cycle_ns = int(duty_cycle * 1e9)

        self._write_pin_attr(self._pin_duty_cycle_path, "{}".format(duty_cycle_ns))

    duty_cycle = property(_get_duty_cycle, _set_duty_cycle)
    """Get or set the PWM's output duty cycle as a ratio from 0.0 to 1.0.

    Raises:
        PWMError: if an I/O or OS error occurs.
        TypeError: if value type is not int or float.
        ValueError: if value is out of bounds of 0.0 to 1.0.

    :type: int, float
    """

    def _get_frequency(self):
        return 1.0 / self.period

    def _set_frequency(self, frequency):
        if not isinstance(frequency, (int, float)):
            raise TypeError("Invalid frequency type, should be int or float.")

        self.period = 1.0 / frequency

    frequency = property(_get_frequency, _set_frequency)
    """Get or set the PWM's output frequency in Hertz.

    Raises:
        PWMError: if an I/O or OS error occurs.
        TypeError: if value type is not int or float.

    :type: int, float
    """

    def _get_polarity(self):
        return self._read_pin_attr(self._pin_polarity_path)

    def _set_polarity(self, polarity):
        if not isinstance(polarity, str):
            raise TypeError("Invalid polarity type, should be str.")
        elif polarity.lower() not in ["normal", "inversed"]:
            raise ValueError("Invalid polarity, can be: \"normal\" or \"inversed\".")

        self._write_pin_attr(self._pin_polarity_path, polarity.lower())

    polarity = property(_get_polarity, _set_polarity)
    """Get or set the PWM's output polarity. Can be "normal" or "inversed".

    Raises:
        PWMError: if an I/O or OS error occurs.
        TypeError: if value type is not str.
        ValueError: if value is invalid.

    :type: str
    """

    def _get_enabled(self):
        enabled = self._read_pin_attr(self._pin_enable_path)

        if enabled == "1":
            return True
        elif enabled == "0":
            return False

        raise PWMError(None, "Unknown enabled value: \"%s\"" % enabled)

    def _set_enabled(self, value):
        if not isinstance(value, bool):
            raise TypeError("Invalid enabled type, should be string.")

        self._write_pin_attr(self._pin_enable_path, "1" if value else "0")

    enabled = property(_get_enabled, _set_enabled)
    """Get or set the PWM's output enabled state.

    Raises:
        PWMError: if an I/O or OS error occurs.
        TypeError: if value type is not bool.

    :type: bool
    """

    # String representation

    def __str__(self):
        return "PWM%d, pin %d (period=%f sec, duty_cycle=%f%%, polarity=%s, enabled=%s)" % \
            (self._channel, self._pin, self.period, self.duty_cycle * 100,
             self.polarity, str(self.enabled))
