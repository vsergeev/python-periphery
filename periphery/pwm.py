import os

class PWMError(IOError):
    """ Base class for PWM errors. """
    pass

class PWM(object):
    sysfs_path = "/sys/class/pwm/"
    channel_path = "pwmchip{}"

    # Channel specific paths
    export_path = "export"
    pin_path = "pwm{}"

    # Pin specific paths
    pin_period_path = "period"
    pin_duty_path = "duty_cycle"
    pin_polarity_path = "polarity"
    pin_enable_path = "enable"

    def __init__(self, channel, pin, polarity="normal"):

        self._fd = None
        self._channel = None
        self._pin = None
        self._period = None
        self._duty = None
        self._polarity="normal"
        self._open(channel, pin, polarity)

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, t, value, traceback):
        self.close()

    def _open(self, channel, pin, polarity):
        if not isinstance(channel, int):
            raise TypeError("Invalid channel type, should be integer.")
        if not isinstance(pin, int):
            raise TypeError("Invalid pin type, should be integer.")
        if not isinstance(polarity, str):
            raise TypeError("Invalid polarity type, should be string.")
        if polarity.lower() not in ['normal', 'inversed']:
            raise ValueError("Invalid polarity, can be: 'normal', or 'inversed'.")

        channel_path = os.path.join(self.sysfs_path, self.channel_path.format(channel))
        if not os.path.isdir(channel_path):
            raise ValueError("PWM channel does not exist, check that the required modules are loaded.")
            
        pin_path = os.path.join(channel_path, self.pin_path.format(pin))
        if not os.path.isdir(pin_path):
            try:
                with open(os.path.join(channel_path, self.export_path), "w") as f_export:
                    f_export.write("%d\n" % pin)
            except IOError as e:
                raise PWMError(e.errno, "Exporting PWM: " + e.strerror)

        try:
            self._fd = os.open(os.path.join(pin_path, self.pin_period_path), os.O_RDWR)
        except OSError as e:
            raise PWMError(e.errno, "Opening PWM: " + e.strerror)

        self._channel = channel
        self._pin = pin

        self._period = self._read_pin_attr('period')
        self._duty_cycle = self._read_pin_attr('duty_cycle')
        self._enabled = self._read_pin_attr('enable')

    def close(self):
        """ Closes the sysfs PWM
        
        Rasies:
            PWMError: if an I/O or OS error occurs """

        if self._fd is None:
            return

        try:
            os.close(self._fd)
        except OSError as e:
            raise PWMError(e.errno, "Closing PWM: " + e.strerror)

        self._fd = None

    def _write_pin_attr(self, attr, value):
        path = os.path.join(
            self.sysfs_path,
            self.channel_path.format(self._channel),
            self.pin_path.format(self._pin),
            attr)

        with open(path, 'w') as f_attr:
                f_attr.write(str(value))

    def _read_pin_attr(self, attr):
        path = os.path.join(
            self.sysfs_path,
            self.channel_path.format(self._channel),
            self.pin_path.format(self._pin),
            attr)

        with open(path, 'r') as f_attr:
            return f_attr.read()

    @property
    def fd(self):
        return self._fd

    @property
    def channel(self):
        return self._channel

    @property
    def pin(self):
        return self._pin

    @property
    def frequency(self):
        return (1000000000 / self._period)

    @frequency.setter
    def frequency(self, value):
        if not isinstance(value, int):
            raise ValueError("Invalid frequency, must be integer.")

        period = (1000000000 / value)
        self._write_pin_attr(self.pin_period_path, period)
        self._period = period

    @property
    def period(self):
        return self._period

    @period.setter
    def period(self, value):
        if not isinstance(value, int):
            raise ValueError("Invalid period, must be integer.")

        self._write_pin_attr(self.pin_period_path, value)
        self._period = value

    @property
    def duty_cycle(self):
        return self._duty_cycle

    @duty_cycle.setter
    def duty_cycle(self, value):
        if not isinstance(value, int):
            raise ValueError("Invalid duty cycle, must be integer.")

        self._write_pin_attr(self.pin_duty_path, value)
        self._duty_cycle = value

    @property
    def duty_cycle_pct(self):
        return 100.0 / self._period * self.duty_cycle

    @duty_cycle_pct.setter
    def duty_cycle_pct(self, value):
        if not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError("Invalid duty cycle pct, must be integer between 0-100")

        duty = self._period * (value / 100.0)
        self._write_pin_attr(self.pin_duty_path, int(duty))
        self._duty_cycle = duty

    @property
    def polarity(self):
        return self._polarity

    @polarity.setter
    def polarity(self, value):
        if not isinstance(value, str):
            raise ValueError("Invalid polarity, can be: 'normal', or 'inversed'.")

        self._write_pin_attr(self.pin_polarity_path, value)
        self._polarity = value
    
    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if not isinstance(value, int):
            raise ValueError("Invalid value for 'enable', must be integer.")

        self._write_pin_attr(self.pin_enable_path, value)
        self._enabled = value

    def __str__(self):
        return "PWM%d, Pin %d (fd=%d, period=%d, duty_cycle=%d, polarity=%d, enable=%d)" % \
            (self._channel, self._pin, self._fd, self._period, self._duty_cycle, self._polarity, self._enabled)
