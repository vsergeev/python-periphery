LED
====

Code Example
------------

.. code-block:: python

    from periphery import LED
    
    # Open LED "led0" with initial state off
    led0 = LED("led0", False)
    # Open LED "led1" with initial state on
    led1 = LED("led1", True)
    
    value = led0.read()
    led1.write(value)
    
    # Set custom brightness level
    led1.write(led1.max_brightness / 2)
    
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

