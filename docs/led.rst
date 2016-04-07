LED
====

Code Example
------------

.. code-block:: python

    from periphery import LED
    
    # Open 'led0' LED with initial brightness 0
    led0 = LED("led0", 0)
    # Open 'led1' LED with initial brightness 255
    led1 = LED("led1", 255)
    
    value = led0.read()
    led1.write(value)
    
    led0.close()
    led1.close()

API
---

.. autoclass:: periphery.LED
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: periphery.LEDError
    :members:
    :undoc-members:
    :show-inheritance:

