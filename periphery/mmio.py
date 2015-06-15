import os
import mmap
import ctypes

class MMIOException(IOError):
    pass

class MMIO(object):
    def __init__(self, physaddr, size):
        self.mapping = None
        self._open(physaddr, size)

    def __del__(self):
        self.close()
        self.mapping = None

    def _open(self, physaddr, size):
        pagesize = os.sysconf(os.sysconf_names['SC_PAGESIZE'])

        self._physaddr = physaddr
        self._size = size
        self._aligned_physaddr = physaddr - (physaddr % pagesize)
        self._aligned_size = size + (physaddr - self._aligned_physaddr)

        try:
            fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        except OSError as e:
            raise MMIOException(e.errno, "Opening /dev/mem: " + e.strerror)

        try:
            self.mapping = mmap.mmap(fd, self._aligned_size, flags=mmap.MAP_SHARED, prot=(mmap.PROT_READ | mmap.PROT_WRITE), offset=self._aligned_physaddr)
        except OSError as e:
            raise MMIOException(e.errno, "Mapping /dev/mem: " + e.strerror)

        try:
            os.close(fd)
        except OSError as e:
            raise MMIOException(e.errno, "Closing /dev/mem: " + e.strerror)

    def close(self):
        if self.mapping is None:
            return

        self.mapping.close()
        self.mapping = None

        self._fd = None

    # Methods

    def _adjust_offset(self, offset):
        return offset + (self._physaddr - self._aligned_physaddr)

    def _validate_offset(self, offset, length):
        if (offset+length) > self._aligned_size:
            raise ValueError("Offset out of bounds.")

    def read32(self, offset):
        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 4)
        return ctypes.c_uint32.from_buffer(self.mapping, offset).value

    def read16(self, offset):
        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 2)
        return ctypes.c_uint16.from_buffer(self.mapping, offset).value

    def read8(self, offset):
        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 1)
        return ctypes.c_uint8.from_buffer(self.mapping, offset).value

    def read(self, offset, length):
        offset = self._adjust_offset(offset)
        self._validate_offset(offset, length)

        c_byte_array = (ctypes.c_uint8 * length).from_buffer(self.mapping, offset)
        return bytes(bytearray(c_byte_array))

    def write32(self, offset, value):
        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 4)
        ctypes.c_uint32.from_buffer(self.mapping, offset).value = value

    def write16(self, offset, value):
        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 2)
        ctypes.c_uint16.from_buffer(self.mapping, offset).value = value

    def write8(self, offset, value):
        offset = self._adjust_offset(offset)
        self._validate_offset(offset, 1)
        ctypes.c_uint8.from_buffer(self.mapping, offset).value = value

    def write(self, offset, data):
        offset = self._adjust_offset(offset)
        self._validate_offset(offset, len(data))

        if not isinstance(data, bytes) and not isinstance(data, bytearray) and not isinstance(data, list):
            raise TypeError("Invalid data type, expected bytes, bytearray, or list.")

        data = bytearray(data)

        c_byte_array = (ctypes.c_uint8 * len(data)).from_buffer(self.mapping, offset)
        for i in range(len(data)):
            c_byte_array[i] = data[i]

    # Immutable properties

    @property
    def base(self):
        return self._physaddr

    @property
    def size(self):
        return self._size

    @property
    def pointer(self):
        return ctypes.cast(ctypes.pointer(ctypes.c_uint8.from_buffer(self.mapping, 0)), ctypes.c_void_p)

    # String representation

    def __str__(self):
        return "MMIO 0x%08x (size=%d)" % (self.base, self.size)

