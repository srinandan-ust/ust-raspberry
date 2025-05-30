from gpiozero import LED, GPIOPinMissing
from gpiozero.exc import BadPinFactory

# Global LED object
_led_device = None
_led_pin_number = None

def setup_led(pin_number):
    global _led_device, _led_pin_number
    if _led_device:
        print(f"LED already setup on pin {_led_pin_number}. Cleaning up first.")
        cleanup_led()

    _led_pin_number = pin_number
    try:
        _led_device = LED(pin_number)
        _led_device.off() # Ensure LED is off initially
        print(f"LED setup on GPIO pin {_led_pin_number}")
        return True
    except BadPinFactory as e:
        print(f"Error: Could not initialize LED on pin {pin_number}. Is pigpiod running or an alternative pin factory set? Error: {e}")
        _led_device = None
        return False
    except GPIOPinMissing:
        print(f"Error: GPIO pin {pin_number} not found.")
        _led_device = None
        return False
    except Exception as e:
        print(f"An unexpected error occurred during LED setup: {e}")
        _led_device = None
        return False

def led_on():
    if _led_device:
        if not _led_device.is_lit:
            _led_device.on()
            # print(f"LED on GPIO {_led_pin_number} turned ON")
    else:
        print("LED not setup. Call setup_led(pin) first.")

def led_off():
    if _led_device:
        if _led_device.is_lit:
            _led_device.off()
            # print(f"LED on GPIO {_led_pin_number} turned OFF")
    else:
        print("LED not setup. Call setup_led(pin) first.")

def cleanup_led():
    global _led_device, _led_pin_number
    if _led_device:
        _led_device.off()
        _led_device.close()
        _led_device = None
        print(f"LED on GPIO {_led_pin_number} cleaned up.")
        _led_pin_number = None