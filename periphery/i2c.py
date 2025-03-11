import os
import ctypes
import array
import fcntl


class I2CError(IOError):
    """Base class for I2C errors."""
    pass


class _CI2CMessage(ctypes.Structure):
    _fields_ = [
        ("addr", ctypes.c_ushort),
        ("flags", ctypes.c_ushort),
        ("len", ctypes.c_ushort),
        ("buf", ctypes.POINTER(ctypes.c_ubyte)),
    ]


class _CI2CIocTransfer(ctypes.Structure):
    _fields_ = [
        ("msgs", ctypes.POINTER(_CI2CMessage)),
        ("nmsgs", ctypes.c_uint),
    ]


class I2C(object):
    # Constants scraped from <linux/i2c-dev.h> and <linux/i2c.h>
    _I2C_IOC_FUNCS = 0x705
    _I2C_IOC_RDWR = 0x707
    _I2C_FUNC_I2C = 0x1
    _I2C_M_TEN = 0x0010
    _I2C_M_RD = 0x0001
    _I2C_M_STOP = 0x8000
    _I2C_M_NOSTART = 0x4000
    _I2C_M_REV_DIR_ADDR = 0x2000
    _I2C_M_IGNORE_NAK = 0x1000
    _I2C_M_NO_RD_ACK = 0x0800
    _I2C_M_RECV_LEN = 0x0400

    def __init__(self, devpath):
        """Instantiate an I2C object and open the i2c-dev device at the
        specified path.

        Args:
            devpath (str): i2c-dev device path.

        Returns:
            I2C: I2C object.

        Raises:
            I2CError: if an I/O or OS error occurs.

        """
        self._fd = None
        self._devpath = None
        self._open(devpath)

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, t, value, traceback):
        self.close()

    def _open(self, devpath):
        # Open i2c device
        try:
            self._fd = os.open(devpath, os.O_RDWR)
        except OSError as e:
            raise I2CError(e.errno, "Opening I2C device: " + e.strerror)

        self._devpath = devpath

        # Query supported functions
        buf = array.array('I', [0])
        try:
            fcntl.ioctl(self._fd, I2C._I2C_IOC_FUNCS, buf, True)
        except (OSError, IOError) as e:
            self.close()
            raise I2CError(e.errno, "Querying supported functions: " + e.strerror)

        # Check that I2C_RDWR ioctl() is supported on this device
        if (buf[0] & I2C._I2C_FUNC_I2C) == 0:
            self.close()
            raise I2CError(None, "I2C not supported on device \"{:s}\"".format(devpath))

    # Methods

    def transfer(self, address, messages):
        """Transfer `messages` to the specified I2C `address`. Modifies the
        `messages` array with the results of any read transactions.

        Args:
            address (int): I2C address.
            messages (list): list of I2C.Message messages.

        Raises:
            I2CError: if an I/O or OS error occurs.
            TypeError: if `messages` type is not a sequence.
            ValueError: if `messages` length is zero, or if message data is not valid bytes.

        """
        try:
            if len(messages) == 0:
                raise ValueError("Invalid messages data, should be non-zero length.")
        except TypeError:
            raise TypeError("Invalid messages type, should be a sequence of I2C.Message.")

        # Convert I2C.Message messages to _CI2CMessage messages
        convert_reads = []
        cmessages = (_CI2CMessage * len(messages))()
        for message, cmessage in zip(messages, cmessages):
            data = message.data
            if not isinstance(data, bytearray):
                data = bytearray(data)
                if message.read:
                    convert_reads.append((message, data))

            cmessage.addr = address
            cmessage.flags = message.flags | (I2C._I2C_M_RD if message.read else 0)
            cmessage.len = n = len(data)
            cmessage.buf = (ctypes.c_ubyte * n).from_buffer(data)

        # Prepare transfer structure
        i2c_xfer = _CI2CIocTransfer()
        i2c_xfer.nmsgs = len(cmessages)
        i2c_xfer.msgs = cmessages

        # Transfer
        try:
            fcntl.ioctl(self._fd, I2C._I2C_IOC_RDWR, i2c_xfer, False)
        except (OSError, IOError) as e:
            raise I2CError(e.errno, "I2C transfer: " + e.strerror)

        # Update any read I2C.Message messages
        for message, data in convert_reads:
            # Convert read data to type used in I2C.Message messages
            if isinstance(message.data, list):
                message.data[:] = data
            else:
                message.data = bytes(data)

    def close(self):
        """Close the i2c-dev I2C device.

        Raises:
            I2CError: if an I/O or OS error occurs.

        """
        if self._fd is None:
            return

        try:
            os.close(self._fd)
        except OSError as e:
            raise I2CError(e.errno, "Closing I2C device: " + e.strerror)

        self._fd = None

    # Immutable properties

    @property
    def fd(self):
        """Get the file descriptor of the underlying i2c-dev device.

        :type: int
        """
        return self._fd

    @property
    def devpath(self):
        """Get the device path of the underlying i2c-dev device.

        :type: str
        """
        return self._devpath

    # String representation

    def __str__(self):
        return "I2C (device={:s}, fd={:d})".format(self.devpath, self.fd)

    class Message:
        def __init__(self, data, read=False, flags=0):
            """Instantiate an I2C Message object.

            Args:
                data (bytes, bytearray, list, positive integer):
                             a sequence of 8-bit integers to write;
                             a number of 0x00 to write;
                             or a number of bytes to read (result type is bytes)
                read (bool): specify this as a read message, where `data`
                             serves as placeholder bytes for the read;
                             if type is mutable, data is modified in-place
                flags (int): additional i2c-dev flags for this message.

            Returns:
                Message: Message object.

            Raises:
                TypeError: if `data`, `read`, or `flags` types are invalid.

            """
            if not isinstance(data, (bytes, bytearray, list, int)):
                raise TypeError("Invalid data type, should be bytes, bytearray, list or integer.")
            if not isinstance(read, bool):
                raise TypeError("Invalid read type, should be boolean.")
            if not isinstance(flags, int):
                raise TypeError("Invalid flags type, should be integer.")

            self.data = data
            self.read = read
            self.flags = flags
