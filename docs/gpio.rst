GPIO
====

Code Example
------------

.. code-block:: python

    from periphery import GPIO
    
    # Open GPIO /dev/gpiochip0 10 with input direction
    gpio_in = GPIO("/dev/gpiochip0", 10, "in")
    # Open GPIO /dev/gpiochip0 12 with output direction
    gpio_out = GPIO("/dev/gpiochip0", 12, "out")
    
    value = gpio_in.read()
    gpio_out.write(not value)
    
    gpio_in.close()
    gpio_out.close()

API
---

.. class:: periphery.GPIO(path, line, direction)

    .. autoclass:: periphery.CdevGPIO

.. class:: periphery.GPIO(line, direction)

    .. autoclass:: periphery.SysfsGPIO

.. autoclass:: periphery.GPIO
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: periphery.EdgeEvent
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: periphery.GPIOError
    :members:
    :undoc-members:
    :show-inheritance:

