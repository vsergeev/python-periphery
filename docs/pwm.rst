PWM
===

Code Example
------------

.. code-block:: python

    from periphery import PWM
    
    # Open PWM channel 0, pin 10
    pwm = PWM(0, 10)
    
    # Set frequency to 1 kHz
    pwm.frequency = 1e3
    # Set duty cycle to 75%
    pwm.duty_cycle = 0.75
    
    pwm.enable()

    # Change duty cycle to 50%
    pwm.duty_cycle = 0.50
    
    pwm.close()

API
---

.. autoclass:: periphery.PWM
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: periphery.PWMError
    :members:
    :undoc-members:
    :show-inheritance:

