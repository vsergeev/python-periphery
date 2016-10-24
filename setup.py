try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='python-periphery',
    version='1.1.0',
    description='A pure Python 2/3 library for peripheral I/O (GPIO, LED, PWM, SPI, I2C, MMIO, Serial) in Linux.',
    author='vsergeev',
    author_email='v@sergeev.io',
    url='https://github.com/vsergeev/python-periphery',
    packages=['periphery'],
    long_description="""python-periphery is a pure Python library for GPIO, LED, PWM, SPI, I2C, MMIO, and Serial peripheral I/O interface access in userspace Linux. It is useful in embedded Linux environments (including Raspberry Pi, BeagleBone, etc. platforms) for interfacing with external peripherals. python-periphery is compatible with Python 2 and Python 3, is written in pure Python, and is MIT licensed. See https://github.com/vsergeev/python-periphery for more information.""",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: System :: Hardware',
        'Topic :: System :: Hardware :: Hardware Drivers',
    ],
    license='MIT',
    keywords='gpio spi led pwm i2c mmio serial uart embedded linux beaglebone raspberrypi rpi odroid',
)
