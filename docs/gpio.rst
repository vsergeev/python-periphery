GPIO
====

Code Example
------------

.. code-block:: python

    from periphery import GPIO
    
    # Open GPIO 10 with input direction
    gpio_in = GPIO(10, "in")
    # Open GPIO 12 with output direction
    gpio_out = GPIO(12, "out")
    
    value = gpio_in.read()
    gpio_out.write(value)
    
    gpio_in.close()
    gpio_out.close()

API
---

.. autoclass:: periphery.GPIO
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: periphery.GPIOError
    :members:
    :undoc-members:
    :show-inheritance:

