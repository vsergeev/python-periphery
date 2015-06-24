SPI
===

Code Example
------------

.. code-block:: python

    from periphery import SPI
    
    # Open spidev1.0 with mode 0 and max speed 1MHz
    spi = SPI("/dev/spidev1.0", 0, 1000000)
    
    data_out = [0xaa, 0xbb, 0xcc, 0xdd]
    data_in = spi.transfer(data_out)
    
    print("shifted out [0x%02x, 0x%02x, 0x%02x, 0x%02x]" % tuple(data_out))
    print("shifted in  [0x%02x, 0x%02x, 0x%02x, 0x%02x]" % tuple(data_in))
    
    spi.close()

API
---

.. autoclass:: periphery.SPI
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: periphery.SPIError
    :members:
    :undoc-members:
    :show-inheritance:

