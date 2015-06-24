MMIO
====

Code Example
------------

.. code-block:: python

    from periphery import MMIO
    
    # Open am335x real-time clock subsystem page
    rtc_mmio = MMIO(0x44E3E000, 0x1000)
    
    # Read current time
    rtc_secs = rtc_mmio.read32(0x00)
    rtc_mins = rtc_mmio.read32(0x04)
    rtc_hrs = rtc_mmio.read32(0x08)
    
    print("hours: %02x minutes: %02x seconds: %02x" % (rtc_hrs, rtc_mins, rtc_secs))
    
    rtc_mmio.close()
    
    # Open am335x control module page
    ctrl_mmio = MMIO(0x44E10000, 0x1000)
    
    # Read MAC address
    mac_id0_lo = ctrl_mmio.read32(0x630)
    mac_id0_hi = ctrl_mmio.read32(0x634)
    
    print("MAC address: %04x%08x" % (mac_id0_lo, mac_id0_hi))
    
    ctrl_mmio.close()

API
---

.. autoclass:: periphery.MMIO
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: periphery.MMIOError
    :members:
    :undoc-members:
    :show-inheritance:

