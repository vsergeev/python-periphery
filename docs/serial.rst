Serial
======

Code Example
------------

.. code-block:: python

    from periphery import Serial
    
    # Open /dev/ttyUSB0 with baudrate 115200, and defaults of 8N1, no flow control
    serial = Serial("/dev/ttyUSB0", 115200)
    
    serial.write(b"Hello World!")
    
    # Read up to 128 bytes with 500ms timeout
    buf = serial.read(128, 0.5)
    print("read %d bytes: _%s_" % (len(buf), buf))
    
    serial.close()

API
---

.. autoclass:: periphery.Serial
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: periphery.SerialError
    :members:
    :undoc-members:
    :show-inheritance:

