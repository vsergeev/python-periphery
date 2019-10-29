* v2.0.0 - 10/28/2019
    * GPIO
        * Add support for character device GPIOs.
        * Remove support for preserve direction from GPIO constructor.
        * Add retry loop to direction write after export to accommodate delayed
          udev permission rule application for sysfs GPIOs.
        * Unexport GPIO line on close for sysfs GPIOs.
        * Fix handling of `timeout=None` with sysfs GPIO `poll()`.
        * Add `devpath` property.
    * PWM
        * Fix chip and channel argument names in PWM constructor and
          documentation.
        * Add retry loop to PWM open after export to accommodate delayed
          creation of sysfs files by kernel driver.
        * Unexport PWM channel on close.
        * Add nanosecond `period_ns` and `duty_cycle_ns` properties.
        * Add `devpath` property.
    * LED
        * Raise `LookupError` instead of `ValueError` if LED name is not found
          during open.
        * Add `devpath` property.
    * Fix exception handling for Python 2 with `ioctl()` operations in Serial,
      SPI, and I2C modules.
    * Fix `with` statement context manager support for all modules.
    * Update tests with running hints for Raspberry Pi 3.
    * Contributors
        * Uwe Kleine-König, @ukleinek - 0005260
        * Heath Robinson, @ubiquitousthey - ac457d6

* v1.1.2 - 06/25/2019
    * Add LICENSE file to packaging.

* v1.1.1 - 04/03/2018
    * Fix handling of delayed pin directory export when opening a GPIO.

* v1.1.0 - 10/24/2016
    * Add support for preserving pin direction when opening GPIO.
    * Improve GPIO poll() implementation to work with more platforms.
    * Improve atomicity of MMIO fixed width writes.
    * Add PWM module.
    * Add LED module.
    * Add support for universal wheel packaging.
    * Contributors
        * Sanket Dasgupta - 8ac7b40
        * Joseph Kogut - 022ef29, d2e9132
        * Hector Martin - 1e3343a
        * Francesco Valla - 34b3877

* v1.0.0 - 06/25/2015
    * Initial release.
