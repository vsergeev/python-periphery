import sys
import os
import mmap
import ctypes
import struct

# Alias long to int on Python 3
if sys.version_info[0] >= 3:
    long = int

class MMIOError(IOError):
    """Base class for MMIO errors."""
    pass

class MMIO(object):
    def __init__(self, physaddr, size):
        """Instantiate an MMIO object and map the region of physical memory
        specified by the address base `physaddr` and size `size` in bytes.

        Args:
            physaddr (int, long): base physical address of memory region.
            size (int, long): size of memory region.

        Returns:
            MMIO: MMIO object.

        Raises:
            MMIOError: if an I/O or OS error occurs.
            TypeError: if `physaddr` or `size` types are invalid.

        """
        self.mapping = None
        self._open(physaddr, size)

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, t, value, traceback):
        self.close()

    def _open(self, physaddr, size):
        if not isinstance(physaddr, (int, long)):
            raise TypeError("Invalid physaddr type, should be integer.")
        if not isinstance(size, (int, long)):
            raise TypeError("Invalid size type, should be integer.")

        pagesize = os.sysconf(os.sysconf_names['SC_PAGESIZE'])

        self._physaddr = physaddr
        self._size = size
        self._aligned_physaddr = physaddr - (physaddr % pagesize)
        self._aligned_size = size + (physaddr - self._aligned_physaddr)

        try:
            fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        except OSError as e:
            raise MMIOError(e.errno, "Opening /dev/mem: " + e.strerror)

        try:
            self.mapping = mmap.mmap(fd, self._aligned_size, flags=mmap.MAP_SHARED, prot=(mmap.PROT_READ | mmap.PROT_WRITE), offset=self._aligned_physaddr)
        except OSError as e:
            raise MMIOError(e.errno, "Mapping /dev/mem: " + e.strerror)

        try:
            os.close(fd)
        except OSError as e:
            raise MMIOError(e.errno, "Closing /dev/mem: " + e.strerror)

    # Methods

    def _adjust_offset(self, offset):
        return offset + (self._physaddr - self._aligned_physaddr)

    def _validate_offset(self, offset, length):
        if (offset+length) > self._aligned_size:
            raise ValueError("Offset out of bounds.")

    def read32(self, offset):
        """Read 32-bits from the specified `offset` in bytes, relative to the
        base physical address of the MMIO region.

        Args:
            offset (int, long): offset from base physical address, in bytes.

        Returns:
            int: 32-bit value read.

        Raises:
            TypeError: if `offset` type is invalid.
            ValueError: if `offset` is out of bounds.

        """
        if not isinstance(offset, (int, long)):
            raise TypeError("Invalid offset type, should be integer.")

        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 4)
        return struct.unpack("=L", self.mapping[offset:offset+4])[0]

    def read16(self, offset):
        """Read 16-bits from the specified `offset` in bytes, relative to the
        base physical address of the MMIO region.

        Args:
            offset (int, long): offset from base physical address, in bytes.

        Returns:
            int: 16-bit value read.

        Raises:
            TypeError: if `offset` type is invalid.
            ValueError: if `offset` is out of bounds.

        """
        if not isinstance(offset, (int, long)):
            raise TypeError("Invalid offset type, should be integer.")

        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 2)
        return struct.unpack("=H", self.mapping[offset:offset+2])[0]

    def read8(self, offset):
        """Read 8-bits from the specified `offset` in bytes, relative to the
        base physical address of the MMIO region.

        Args:
            offset (int, long): offset from base physical address, in bytes.

        Returns:
            int: 8-bit value read.

        Raises:
            TypeError: if `offset` type is invalid.
            ValueError: if `offset` is out of bounds.

        """
        if not isinstance(offset, (int, long)):
            raise TypeError("Invalid offset type, should be integer.")

        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 1)
        return struct.unpack("B", self.mapping[offset:offset+1])[0]

    def read(self, offset, length):
        """Read a string of bytes from the specified `offset` in bytes,
        relative to the base physical address of the MMIO region.

        Args:
            offset (int, long): offset from base physical address, in bytes.
            length (int): number of bytes to read.

        Returns:
            bytes: bytes read.

        Raises:
            TypeError: if `offset` type is invalid.
            ValueError: if `offset` is out of bounds.

        """
        if not isinstance(offset, (int, long)):
            raise TypeError("Invalid offset type, should be integer.")

        offset = self._adjust_offset(offset)
        self._validate_offset(offset, length)
        return bytes(self.mapping[offset:offset+length])

    def write32(self, offset, value):
        """Write 32-bits to the specified `offset` in bytes, relative to the
        base physical address of the MMIO region.

        Args:
            offset (int, long): offset from base physical address, in bytes.
            value (int, long): 32-bit value to write.

        Raises:
            TypeError: if `offset` or `value` type are invalid.
            ValueError: if `offset` or `value` are out of bounds.

        """
        if not isinstance(offset, (int, long)):
            raise TypeError("Invalid offset type, should be integer.")
        if not isinstance(value, (int, long)):
            raise TypeError("Invalid value type, should be integer.")
        if value < 0 or value > 0xffffffff:
            raise ValueError("Value out of bounds.")

        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 4)
        self.mapping[offset:offset+4] = struct.pack("=L", value)

    def write16(self, offset, value):
        """Write 16-bits to the specified `offset` in bytes, relative to the
        base physical address of the MMIO region.

        Args:
            offset (int, long): offset from base physical address, in bytes.
            value (int, long): 16-bit value to write.

        Raises:
            TypeError: if `offset` or `value` type are invalid.
            ValueError: if `offset` or `value` are out of bounds.

        """
        if not isinstance(offset, (int, long)):
            raise TypeError("Invalid offset type, should be integer.")
        if not isinstance(value, (int, long)):
            raise TypeError("Invalid value type, should be integer.")
        if value < 0 or value > 0xffff:
            raise ValueError("Value out of bounds.")

        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 2)
        self.mapping[offset:offset+2] = struct.pack("=H", value)

    def write8(self, offset, value):
        """Write 8-bits to the specified `offset` in bytes, relative to the
        base physical address of the MMIO region.

        Args:
            offset (int, long): offset from base physical address, in bytes.
            value (int, long): 8-bit value to write.

        Raises:
            TypeError: if `offset` or `value` type are invalid.
            ValueError: if `offset` or `value` are out of bounds.

        """
        if not isinstance(offset, (int, long)):
            raise TypeError("Invalid offset type, should be integer.")
        if not isinstance(value, (int, long)):
            raise TypeError("Invalid value type, should be integer.")
        if value < 0 or value > 0xff:
            raise ValueError("Value out of bounds.")

        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 1)
        self.mapping[offset:offset+1] = struct.pack("B", value)

    def write(self, offset, data):
        """Write a string of bytes to the specified `offset` in bytes, relative
        to the base physical address of the MMIO region.

        Args:
            offset (int, long): offset from base physical address, in bytes.
            data (bytes, bytearray, list): a byte array or list of 8-bit
                                           integers to write.

        Raises:
            TypeError: if `offset` or `data` type are invalid.
            ValueError: if `offset` is out of bounds, or if data is not valid bytes.

        """
        if not isinstance(offset, (int, long)):
            raise TypeError("Invalid offset type, should be integer.")
        if not isinstance(data, (bytes, bytearray, list)):
            raise TypeError("Invalid data type, expected bytes, bytearray, or list.")

        offset = self._adjust_offset(offset)
        self._validate_offset(offset, len(data))

        data = bytes(bytearray(data))
        self.mapping[offset:offset+len(data)] = data

    def close(self):
        """Unmap the MMIO object's mapped physical memory."""
        if self.mapping is None:
            return

        self.mapping.close()
        self.mapping = None

        self._fd = None

    # Immutable properties

    @property
    def base(self):
        """Get the base physical address of the MMIO region.

        :type: int
        """
        return self._physaddr

    @property
    def size(self):
        """Get the mapping size of the MMIO region.

        :type: int
        """
        return self._size

    @property
    def pointer(self):
        """Get a ctypes void pointer to the memory mapped region.

        :type: ctypes.c_void_p
        """
        return ctypes.cast(ctypes.pointer(ctypes.c_uint8.from_buffer(self.mapping, 0)), ctypes.c_void_p)

    # String representation

    def __str__(self):
        return "MMIO 0x%08x (size=%d)" % (self.base, self.size)
