GPIO
====

Code Example
------------

.. code-block:: python

    from periphery import GPIO
    
    # Open GPIO /dev/gpiochip0 line 10 with input direction
    gpio_in = GPIO("/dev/gpiochip0", 10, "in")
    # Open GPIO /dev/gpiochip0 line 12 with output direction
    gpio_out = GPIO("/dev/gpiochip0", 12, "out")
    
    value = gpio_in.read()
    gpio_out.write(not value)
    
    gpio_in.close()
    gpio_out.close()

API
---

.. class:: periphery.GPIO(path, line, direction)
    :noindex:

    .. autoclass:: periphery.gpio_cdev2.Cdev2GPIO
        :noindex:

.. class:: periphery.GPIO(line, direction)
    :noindex:

    .. autoclass:: periphery.SysfsGPIO
        :noindex:

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

